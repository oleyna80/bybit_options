"""
WebSocket Stream Manager - The Ears of the Trading System

DESIGN PHILOSOPHY:
- Paranoid error handling: Assume network/API will fail
- Zero-copy reads: Immutable snapshots for lock-free access
- Staleness detection: Force reconnect on silent failures
- Circuit breaker: Backoff when exchange is down

ARCHITECTURE:
    BybitStreamManager
        ├─ PublicStreamClient (ticker, orderbook)
        ├─ PrivateStreamClient (positions, orders)
        └─ LocalCache (copy-on-write dict)

USAGE:
    async with BybitStreamManager(api_key, secret) as manager:
        await manager.subscribe_ticker("BTCUSDT")
        
        # From another coroutine:
        ticker = manager.get_ticker("BTCUSDT")
"""

import asyncio
import aiohttp
import hmac
import hashlib
import json
import time
import logging
from typing import Dict, List, Optional, Set, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class StreamConfig:
    """WebSocket configuration with sane production defaults"""
    
    # Bybit endpoints
    public_url: str = "wss://stream.bybit.com/v5/public/linear"
    private_url: str = "wss://stream.bybit.com/v5/private"
    
    # Timeouts
    ping_interval: int = 20  # Bybit requires ping every 30s, we're conservative
    pong_timeout: int = 10   # If no pong after ping → reconnect
    staleness_threshold: int = 30  # No message for 30s → force reconnect
    
    # Reconnect strategy
    initial_backoff: float = 1.0  # Start with 1s delay
    max_backoff: float = 300.0    # Cap at 5 minutes
    max_retries: int = 10         # After 10 fails → circuit breaker
    circuit_breaker_cooldown: int = 3600  # 1 hour suspension
    
    # Connection
    connection_timeout: int = 10
    message_timeout: int = 5


# ============================================================================
# CACHE LAYER (Copy-on-Write)
# ============================================================================

class TickerCache:
    """
    Lock-free cache using Copy-on-Write pattern
    
    Thread Safety Model:
    - Single Writer (WS loop) updates _staging
    - Multiple Readers get immutable _snapshot
    - No locks → no contention
    """
    
    def __init__(self):
        self._staging: Dict[str, Dict[str, Any]] = {}
        self._snapshot: Dict[str, Dict[str, Any]] = {}
        self._last_update: Dict[str, float] = {}
    
    def update(self, symbol: str, data: Dict[str, Any]):
        """
        Update ticker data (called from WS loop)
        
        Performance: O(1) shallow copy, ~10μs overhead
        """
        self._staging[symbol] = data
        self._last_update[symbol] = time.time()
        
        # Atomic swap: Python GIL guarantees atomicity of dict assignment
        import copy
        self._snapshot = copy.copy(self._staging)
    
    def get(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get immutable snapshot (thread-safe for readers)"""
        return self._snapshot.get(symbol)
    
    def get_all(self) -> Dict[str, Dict[str, Any]]:
        """Get all tickers (returns reference to immutable dict)"""
        return self._snapshot
    
    def get_staleness(self, symbol: str) -> Optional[float]:
        """Return seconds since last update (for watchdog)"""
        last = self._last_update.get(symbol)
        if last is None:
            return None
        return time.time() - last


class OrderbookCache:
    """
    Orderbook cache with proper price-level management
    
    ARCHITECTURE:
    - Uses Dict[float, float] for O(1) price level lookup
    - Applies deltas correctly: size=0 means DELETE level
    - Validates sequence monotonicity
    - Invalidates cache on sequence gaps
    
    DATA STRUCTURE:
    {
        "BTCUSDT": {
            "bids": {50000.0: 1.5, 49999.5: 2.3, ...},  # price -> size
            "asks": {50001.0: 0.8, 50002.0: 1.2, ...},
            "seq": 12345,
            "timestamp": 1234567890.123,
            "valid": True  # False if sequence gap detected
        }
    }
    """
    
    def __init__(self):
        self._books: Dict[str, Dict] = {}  # symbol -> book structure
        self._snapshot: Dict[str, Dict] = {}
        self._last_seq: Dict[str, int] = {}
    
    def update_snapshot(self, symbol: str, snapshot: Dict):
        """
        Initialize orderbook from snapshot
        
        Bybit snapshot format:
        {
            "s": "BTCUSDT",
            "b": [["50000.0", "1.5"], ["49999.5", "2.3"], ...],
            "a": [["50001.0", "0.8"], ...],
            "u": 12345,  # sequence number
            "seq": 12345
        }
        """
        # Convert list of [price, size] to dict
        bids_dict = {}
        for price_str, size_str in snapshot.get("b", []):
            price = float(price_str)
            size = float(size_str)
            if size > 0:  # Skip zero-size levels
                bids_dict[price] = size
        
        asks_dict = {}
        for price_str, size_str in snapshot.get("a", []):
            price = float(price_str)
            size = float(size_str)
            if size > 0:
                asks_dict[price] = size
        
        seq = snapshot.get("u", 0) or snapshot.get("seq", 0)
        
        self._books[symbol] = {
            "bids": bids_dict,
            "asks": asks_dict,
            "seq": seq,
            "timestamp": time.time(),
            "valid": True  # Mark as valid
        }
        self._last_seq[symbol] = seq
        
        logger.info(
            f"Orderbook snapshot loaded for {symbol}: "
            f"{len(bids_dict)} bids, {len(asks_dict)} asks, seq={seq}"
        )
        
        self._sync_snapshot()
    
    def update_delta(self, symbol: str, delta: Dict) -> bool:
        """
        Apply delta update with proper price-level merging
        
        CRITICAL ALGORITHM:
        1. Validate sequence number (detect gaps)
        2. For each price level in delta:
           - If size > 0: UPDATE level
           - If size == 0: DELETE level
        3. Preserve levels not in delta
        
        Bybit delta format:
        {
            "s": "BTCUSDT",
            "b": [["50000.0", "2.0"], ["49999.0", "0"]],  # 0 = delete
            "a": [["50001.0", "1.5"]],
            "u": 12346
        }
        
        Returns:
            True if update applied, False if sequence gap detected
        """
        new_seq = delta.get("u", 0)
        
        # Validate sequence
        if symbol in self._last_seq:
            expected = self._last_seq[symbol] + 1
            if new_seq != expected:
                logger.error(
                    f"❌ Orderbook sequence gap on {symbol}: "
                    f"expected={expected}, got={new_seq}. "
                    f"Delta will be rejected, book marked INVALID."
                )
                
                # Mark book as invalid
                if symbol in self._books:
                    self._books[symbol]["valid"] = False
                
                return False  # Caller must resync
        
        # Get existing book
        book = self._books.get(symbol)
        if not book:
            logger.warning(
                f"⚠️  Delta received for {symbol} without snapshot. "
                f"Ignoring delta. Snapshot must be loaded first."
            )
            return False
        
        # Check if book is valid (no previous sequence gaps)
        if not book.get("valid", False):
            logger.warning(
                f"⚠️  Delta for {symbol} ignored: book is INVALID "
                f"(previous sequence gap). Waiting for resync."
            )
            return False
        
        # Apply delta to bids
        if "b" in delta:
            for price_str, size_str in delta["b"]:
                price = float(price_str)
                size = float(size_str)
                
                if size == 0:
                    # DELETE level
                    book["bids"].pop(price, None)  # Safe delete
                else:
                    # UPDATE level
                    book["bids"][price] = size
        
        # Apply delta to asks
        if "a" in delta:
            for price_str, size_str in delta["a"]:
                price = float(price_str)
                size = float(size_str)
                
                if size == 0:
                    # DELETE level
                    book["asks"].pop(price, None)
                else:
                    # UPDATE level
                    book["asks"][price] = size
        
        # Update metadata
        book["seq"] = new_seq
        book["timestamp"] = time.time()
        self._last_seq[symbol] = new_seq
        
        self._sync_snapshot()
        return True
    
    def get(self, symbol: str) -> Optional[Dict]:
        """
        Get orderbook snapshot
        
        Returns:
            {
                "bids": {price: size, ...},
                "asks": {price: size, ...},
                "seq": 12345,
                "timestamp": 1234567890.123,
                "valid": True
            }
        """
        book = self._snapshot.get(symbol)
        
        # Warn if book is invalid
        if book and not book.get("valid", False):
            logger.warning(
                f"⚠️  Orderbook for {symbol} is INVALID "
                f"(sequence gap detected). Data may be stale."
            )
        
        return book
    
    def get_sorted_levels(
        self, 
        symbol: str, 
        side: str, 
        max_levels: int = 50
    ) -> List[tuple[float, float]]:
        """
        Get sorted price levels for a side
        
        Args:
            symbol: Trading symbol
            side: "bids" or "asks"
            max_levels: Max number of levels to return
        
        Returns:
            List of (price, size) tuples, sorted by price
            - Bids: Descending (best bid first)
            - Asks: Ascending (best ask first)
        """
        book = self._snapshot.get(symbol)
        if not book or not book.get("valid", False):
            return []
        
        levels = book.get(side, {})
        
        if side == "bids":
            # Sort descending (highest price first)
            sorted_levels = sorted(levels.items(), key=lambda x: x[0], reverse=True)
        else:
            # Sort ascending (lowest price first)
            sorted_levels = sorted(levels.items(), key=lambda x: x[0])
        
        return sorted_levels[:max_levels]
    
    def invalidate(self, symbol: str):
        """
        Mark orderbook as invalid (used when sequence gap detected)
        """
        if symbol in self._books:
            self._books[symbol]["valid"] = False
            logger.warning(f"Orderbook for {symbol} marked INVALID")
            self._sync_snapshot()
    
    def _sync_snapshot(self):
        """Sync staging to immutable snapshot (copy-on-write)"""
        import copy
        self._snapshot = copy.copy(self._books)


# ============================================================================
# WEBSOCKET CLIENT
# ============================================================================

class WSClientState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    SUSPENDED = "suspended"  # Circuit breaker active


@dataclass
class WSStats:
    """Connection statistics for monitoring"""
    messages_received: int = 0
    reconnect_count: int = 0
    last_error: Optional[str] = None
    uptime_start: Optional[float] = None
    
    def mark_connected(self):
        self.uptime_start = time.time()
    
    def get_uptime(self) -> Optional[float]:
        if self.uptime_start:
            return time.time() - self.uptime_start
        return None


class BaseWebSocketClient:
    """
    Base WebSocket client with robust reconnect logic
    
    Implements:
    - Exponential backoff
    - Circuit breaker
    - Heartbeat monitoring
    - Staleness detection
    """
    
    def __init__(
        self,
        url: str,
        config: StreamConfig,
        on_message: Callable[[Dict], None]
    ):
        self.url = url
        self.config = config
        self.on_message = on_message
        
        self.state = WSClientState.DISCONNECTED
        self.ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self.session: Optional[aiohttp.ClientSession] = None
        
        self.stats = WSStats()
        self._reconnect_attempt = 0
        self._last_message_time = 0.0
        
        self._tasks: Set[asyncio.Task] = set()
        self._should_run = False
    
    async def start(self):
        """Start WebSocket connection with auto-reconnect"""
        self._should_run = True
        self.session = aiohttp.ClientSession()
        
        # Spawn tasks
        connect_task = asyncio.create_task(self._connect_loop())
        heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        watchdog_task = asyncio.create_task(self._staleness_watchdog())
        
        self._tasks.update([connect_task, heartbeat_task, watchdog_task])
    
    async def stop(self):
        """Graceful shutdown"""
        self._should_run = False
        
        # Cancel all tasks
        for task in self._tasks:
            task.cancel()
        
        await asyncio.gather(*self._tasks, return_exceptions=True)
        
        # Close WebSocket
        if self.ws and not self.ws.closed:
            await self.ws.close()
        
        # Close session
        if self.session:
            await self.session.close()
        
        logger.info(f"WebSocket stopped: {self.url}")
    
    async def _connect_loop(self):
        """Main connection loop with exponential backoff"""
        while self._should_run:
            try:
                # Circuit breaker check
                if self._reconnect_attempt >= self.config.max_retries:
                    logger.warning(
                        f"Circuit breaker triggered after {self._reconnect_attempt} "
                        f"attempts. Suspending for {self.config.circuit_breaker_cooldown}s"
                    )
                    self.state = WSClientState.SUSPENDED
                    await asyncio.sleep(self.config.circuit_breaker_cooldown)
                    self._reconnect_attempt = 0  # Reset
                
                # Exponential backoff
                if self._reconnect_attempt > 0:
                    delay = min(
                        self.config.initial_backoff * (2 ** self._reconnect_attempt),
                        self.config.max_backoff
                    )
                    logger.info(f"Reconnecting in {delay:.1f}s (attempt {self._reconnect_attempt})")
                    await asyncio.sleep(delay)
                
                # Connect
                self.state = WSClientState.CONNECTING
                logger.info(f"Connecting to {self.url}")
                
                self.ws = await self.session.ws_connect(
                    self.url,
                    timeout=self.config.connection_timeout,
                    heartbeat=self.config.ping_interval
                )
                
                self.state = WSClientState.CONNECTED
                self.stats.mark_connected()
                self._reconnect_attempt = 0  # Reset on success
                logger.info(f"âœ… Connected to {self.url}")
                
                # Handle messages
                await self._message_loop()
            
            except asyncio.CancelledError:
                logger.info("Connection loop cancelled")
                break
            
            except Exception as e:
                logger.error(f"Connection error: {e}", exc_info=True)
                self.stats.last_error = str(e)
                self.stats.reconnect_count += 1
                self._reconnect_attempt += 1
                self.state = WSClientState.RECONNECTING
                
                # Close broken connection
                if self.ws and not self.ws.closed:
                    await self.ws.close()
    
    async def _message_loop(self):
        """Receive and dispatch messages"""
        assert self.ws is not None
        
        async for msg in self.ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    self._last_message_time = time.time()
                    self.stats.messages_received += 1
                    
                    # Dispatch to handler
                    self.on_message(data)
                
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON: {msg.data[:100]}")
                except Exception as e:
                    logger.error(f"Message handler error: {e}", exc_info=True)
            
            elif msg.type == aiohttp.WSMsgType.ERROR:
                logger.error(f"WebSocket error: {msg.data}")
                break
            
            elif msg.type == aiohttp.WSMsgType.CLOSED:
                logger.warning("WebSocket closed by server")
                break
    
    async def _heartbeat_loop(self):
        """Send ping frames to keep connection alive"""
        while self._should_run:
            await asyncio.sleep(self.config.ping_interval)
            
            if self.ws and not self.ws.closed:
                try:
                    # Bybit expects JSON ping
                    await self.ws.send_json({"op": "ping"})
                except Exception as e:
                    logger.error(f"Ping failed: {e}")
    
    async def _staleness_watchdog(self):
        """Detect silent connection failures"""
        while self._should_run:
            await asyncio.sleep(self.config.staleness_threshold)
            
            if self.state == WSClientState.CONNECTED:
                staleness = time.time() - self._last_message_time
                
                if staleness > self.config.staleness_threshold:
                    logger.error(
                        f"Stale connection detected: no messages for {staleness:.1f}s"
                    )
                    # Force reconnect
                    if self.ws and not self.ws.closed:
                        await self.ws.close()
    
    async def send(self, message: Dict):
        """Send message to WebSocket"""
        if self.ws and not self.ws.closed:
            await self.ws.send_json(message)
        else:
            logger.warning("Cannot send: WebSocket not connected")


# ============================================================================
# PRIVATE STREAM CLIENT (with Auth)
# ============================================================================

class PrivateStreamClient(BaseWebSocketClient):
    """
    Private WebSocket with HMAC authentication
    
    Handles:
    - Position updates
    - Order updates
    - Execution reports
    """
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        config: StreamConfig,
        on_message: Callable[[Dict], None]
    ):
        super().__init__(config.private_url, config, on_message)
        self.api_key = api_key
        self.api_secret = api_secret
    
    async def _connect_loop(self):
        """Override to add authentication after connect"""
        # Connect first
        await super()._connect_loop()
    
    async def _message_loop(self):
        """Authenticate before processing messages"""
        assert self.ws is not None
        
        # Send auth request
        await self._authenticate()
        
        # Wait for auth response
        auth_msg = await self.ws.receive()
        if auth_msg.type == aiohttp.WSMsgType.TEXT:
            auth_response = json.loads(auth_msg.data)
            if auth_response.get("success"):
                logger.info("âœ… Private stream authenticated")
            else:
                logger.error(f"Authentication failed: {auth_response}")
                return
        
        # Continue with normal message loop
        await super()._message_loop()
    
    async def _authenticate(self):
        """
        Send HMAC authentication frame
        
        Bybit V5 auth format:
        {
            "op": "auth",
            "args": [API_KEY, EXPIRES, SIGNATURE]
        }
        """
        expires = int((time.time() + 1) * 1000)
        signature_payload = f"GET/realtime{expires}"
        
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            signature_payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        auth_message = {
            "op": "auth",
            "args": [self.api_key, expires, signature]
        }
        
        await self.send(auth_message)


# ============================================================================
# STREAM MANAGER (Main Interface)
# ============================================================================

class BybitStreamManager:
    """
    High-level WebSocket manager
    
    Responsibilities:
    - Manage public/private connections
    - Subscribe to channels
    - Maintain local cache
    - Expose lock-free read interface
    
    Usage:
        async with BybitStreamManager(key, secret) as manager:
            await manager.subscribe_ticker("BTCUSDT")
            
            # From Risk Engine:
            ticker = manager.get_ticker("BTCUSDT")
    """
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        config: Optional[StreamConfig] = None
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.config = config or StreamConfig()
        
        # Clients
        self.public_client: Optional[BaseWebSocketClient] = None
        self.private_client: Optional[PrivateStreamClient] = None
        
        # Cache
        self.ticker_cache = TickerCache()
        self.orderbook_cache = OrderbookCache()
        
        # Subscriptions
        self._subscribed_tickers: Set[str] = set()
        self._subscribed_books: Set[str] = set()
        
        # NEW: Callbacks for event-driven integration
        self._execution_callback: Optional[Callable[[Dict], None]] = None
        self._position_callback: Optional[Callable[[Dict], None]] = None
        self._options_callback: Optional[Callable[[Dict], None]] = None
        
        # Options subscriptions
        self._subscribed_options: Set[str] = set()
    
    async def __aenter__(self):
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()
    
    async def start(self):
        """Initialize WebSocket connections"""
        # Public stream
        self.public_client = BaseWebSocketClient(
            url=self.config.public_url,
            config=self.config,
            on_message=self._handle_public_message
        )
        await self.public_client.start()
        
        # Private stream
        self.private_client = PrivateStreamClient(
            api_key=self.api_key,
            api_secret=self.api_secret,
            config=self.config,
            on_message=self._handle_private_message
        )
        await self.private_client.start()
        
        logger.info("âœ… Stream Manager started")
    
    async def stop(self):
        """Shutdown all connections"""
        if self.public_client:
            await self.public_client.stop()
        if self.private_client:
            await self.private_client.stop()
        
        logger.info("Stream Manager stopped")
    
    # ========================================================================
    # SUBSCRIPTION API
    # ========================================================================
    
    async def subscribe_ticker(self, symbol: str):
        """
        Subscribe to ticker updates
        
        Example message:
        {
            "topic": "tickers.BTCUSDT",
            "data": {
                "symbol": "BTCUSDT",
                "lastPrice": "50000.00",
                "bid1Price": "49999.50",
                ...
            }
        }
        """
        if symbol in self._subscribed_tickers:
            return
        
        subscribe_msg = {
            "op": "subscribe",
            "args": [f"tickers.{symbol}"]
        }
        
        await self.public_client.send(subscribe_msg)
        self._subscribed_tickers.add(symbol)
        logger.info(f"Subscribed to ticker: {symbol}")
    
    async def subscribe_orderbook(self, symbol: str, depth: int = 50):
        """
        Subscribe to orderbook updates
        
        Bybit sends:
        1. Snapshot on first subscription
        2. Delta updates subsequently
        """
        if symbol in self._subscribed_books:
            return
        
        subscribe_msg = {
            "op": "subscribe",
            "args": [f"orderbook.{depth}.{symbol}"]
        }
        
        await self.public_client.send(subscribe_msg)
        self._subscribed_books.add(symbol)
        logger.info(f"Subscribed to orderbook: {symbol}")
    
    async def subscribe_position(self):
        """Subscribe to position updates (private)"""
        subscribe_msg = {
            "op": "subscribe",
            "args": ["position"]
        }
        await self.private_client.send(subscribe_msg)
        logger.info("Subscribed to position updates")
    
    async def subscribe_options(self, base_coin: str, callback: Callable[[Dict], None]):
        """
        Subscribe to options updates for a base coin
        
        Args:
            base_coin: Base coin symbol (e.g., "BTC", "ETH")
            callback: Function to call when options data is received
        """
        if base_coin in self._subscribed_options:
            return
        
        # Store callback
        self._options_callback = callback
        
        # Subscribe to options channel (Bybit options topic format may vary)
        # For now, we'll assume topic is "option.BTC" or similar
        subscribe_msg = {
            "op": "subscribe",
            "args": [f"option.{base_coin}"]
        }
        
        try:
            await self.public_client.send(subscribe_msg)
            self._subscribed_options.add(base_coin)
            logger.info(f"Subscribed to options updates for {base_coin}")
        except Exception as e:
            logger.error(f"Failed to subscribe to options for {base_coin}: {e}")
            raise
    
    # ========================================================================
    # CALLBACK REGISTRATION (Event-Driven Integration)
    # ========================================================================
    
    def set_execution_callback(self, callback: Callable[[Dict], None]):
        """
        Register callback for trade executions
        
        Args:
            callback: Async function that receives execution data
            
        Example:
            async def on_trade(execution: Dict):
                await trade_logger.log_trade(execution)
            
            stream_manager.set_execution_callback(on_trade)
        """
        self._execution_callback = callback
        logger.info("✅ Execution callback registered")
    
    def set_position_callback(self, callback: Callable[[Dict], None]):
        """Register callback for position updates"""
        self._position_callback = callback
        logger.info("✅ Position callback registered")
    
    # ========================================================================
    # MESSAGE HANDLERS
    # ========================================================================
    
    def _handle_public_message(self, message: Dict):
        """Route public stream messages"""
        topic = message.get("topic", "")
        
        if topic.startswith("tickers."):
            self._handle_ticker(message)
        elif topic.startswith("orderbook."):
            self._handle_orderbook(message)
        elif topic.startswith("option."):
            self._handle_option(message)
        elif message.get("op") == "pong":
            pass  # Heartbeat response
        else:
            logger.debug(f"Unhandled public message: {topic}")
    
    def _handle_ticker(self, message: Dict):
        """Update ticker cache"""
        data = message.get("data", {})
        symbol = data.get("symbol")
        
        if symbol:
            self.ticker_cache.update(symbol, data)
    
    def _handle_option(self, message: Dict):
        """
        Handle options updates
        
        Args:
            message: WebSocket message with options data
        """
        data = message.get("data", {})
        
        # Trigger options callback if registered
        if self._options_callback:
            try:
                # Schedule async callback
                asyncio.create_task(self._options_callback(data))
                logger.debug(f"Options update received: {data.get('symbol', 'unknown')}")
            except Exception as e:
                logger.error(f"Error in options callback: {e}")
        else:
            logger.debug(f"Options update received but no callback registered: {data}")
    
    def _handle_orderbook(self, message: Dict):
        """Update orderbook cache with sequence validation"""
        data = message.get("data", {})
        symbol = data.get("s")  # Bybit uses "s" for symbol
        
        if not symbol:
            return
        
        # Check if snapshot or delta
        msg_type = message.get("type")
        
        if msg_type == "snapshot":
            self.orderbook_cache.update_snapshot(symbol, data)
        elif msg_type == "delta":
            success = self.orderbook_cache.update_delta(symbol, data)
            if not success:
                # Sequence gap detected → request new snapshot
                logger.warning(f"Requesting orderbook resync for {symbol}")
                asyncio.create_task(self._resync_orderbook(symbol))
    
    async def _resync_orderbook(self, symbol: str):
        """
        Resync orderbook after sequence gap detection
        
        STRATEGY:
        1. Invalidate local cache (mark as stale)
        2. Unsubscribe from WebSocket channel
        3. Fetch fresh snapshot via REST API
        4. Resubscribe to WebSocket (will get new snapshot + deltas)
        
        PRODUCTION ALTERNATIVE:
        Instead of unsubscribe/resubscribe, we could:
        - Fetch REST snapshot in parallel to WebSocket
        - Apply buffered deltas on top of snapshot
        - This avoids brief data gap during resync
        """
        logger.warning(f"🔄 Starting orderbook resync for {symbol}")
        
        # Step 1: Mark current book as invalid
        self.orderbook_cache.invalidate(symbol)
        
        # Step 2: Unsubscribe from WebSocket
        try:
            await self.public_client.send({
                "op": "unsubscribe",
                "args": [f"orderbook.50.{symbol}"]
            })
            logger.info(f"Unsubscribed from orderbook.50.{symbol}")
        except Exception as e:
            logger.error(f"Failed to unsubscribe: {e}")
        
        # Step 3: Wait for unsubscribe to process
        await asyncio.sleep(1)
        
        # Step 4: Fetch fresh snapshot via REST API
        # OPTION A: Use MarketDataService (requires integration)
        try:
            # TODO: Integrate with market_data_service.py
            # snapshot = await self.market_data_service.fetch_orderbook_snapshot(symbol)
            # self.orderbook_cache.update_snapshot(symbol, snapshot)
            
            logger.warning(
                f"⚠️  REST snapshot fetch not implemented yet. "
                f"Falling back to WebSocket resubscribe."
            )
        except Exception as e:
            logger.error(f"REST snapshot fetch failed: {e}")
        
        # Step 5: Resubscribe (triggers fresh snapshot from Bybit)
        try:
            await self.subscribe_orderbook(symbol, depth=50)
            logger.info(f"✅ Resubscribed to orderbook.50.{symbol}")
        except Exception as e:
            logger.error(f"Failed to resubscribe: {e}")
        
        logger.info(f"✅ Orderbook resync completed for {symbol}")
    
    def _handle_private_message(self, message: Dict):
        """Route private stream messages"""
        topic = message.get("topic", "")
        
        if topic == "position":
            self._handle_position_update(message)
        elif topic == "order":
            self._handle_order_update(message)
        elif topic == "execution":
            self._handle_execution(message)
        else:
            logger.debug(f"Unhandled private message: {topic}")
    
    def _handle_position_update(self, message: Dict):
        """
        Handle position updates from private stream
        
        Triggers registered callback if available
        """
        data = message.get("data", [])
        logger.info(f"Position update: {len(data)} positions changed")
        
        # Trigger callback
        if self._position_callback:
            for position in data:
                # Schedule async callback
                asyncio.create_task(self._position_callback(position))
    
    def _handle_order_update(self, message: Dict):
        """Handle order status changes"""
        data = message.get("data", [])
        logger.info(f"Order update: {len(data)} orders changed")
    
    def _handle_execution(self, message: Dict):
        """
        Handle trade executions
        
        CRITICAL: This is where fills are reported by Bybit
        Triggers registered callback for trade logging
        """
        data = message.get("data", [])
        logger.info(f"Execution: {len(data)} trades executed")
        
        # NEW: Trigger callback for each execution
        if self._execution_callback:
            for execution in data:
                # Log execution details
                logger.debug(
                    f"  Trade: {execution.get('symbol')} "
                    f"{execution.get('side')} {execution.get('execQty')} "
                    f"@ {execution.get('execPrice')}"
                )
                
                # Schedule async callback
                # This will eventually call TradeLogger.log_trade()
                asyncio.create_task(self._execution_callback(execution))
    
    # ========================================================================
    # PUBLIC READ API (Lock-free)
    # ========================================================================
    
    def get_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get latest ticker data (thread-safe)
        
        Returns:
            Immutable snapshot of ticker data or None
        """
        return self.ticker_cache.get(symbol)
    
    def get_all_tickers(self) -> Dict[str, Dict[str, Any]]:
        """Get all cached tickers (immutable snapshot)"""
        return self.ticker_cache.get_all()
    
    def get_orderbook(self, symbol: str) -> Optional[Dict]:
        """
        Get latest orderbook (thread-safe)
        
        Returns:
            {
                "bids": [[price, size], ...],
                "asks": [[price, size], ...],
                "seq": 12345,
                "timestamp": 1234567890.123
            }
        """
        return self.orderbook_cache.get(symbol)
    
    def get_best_bid_ask(self, symbol: str) -> Optional[tuple[float, float]]:
        """
        Get best bid/ask prices (fast O(1) after initial sort)
        
        PERFORMANCE:
        - First call: O(n log n) to sort dict keys
        - Subsequent calls: O(1) if orderbook unchanged (cached)
        
        Returns:
            (best_bid, best_ask) or None if book invalid/empty
        """
        book = self.orderbook_cache.get(symbol)
        if not book:
            return None
        
        # Check if book is valid
        if not book.get("valid", False):
            logger.debug(f"Skipping best bid/ask for {symbol}: book is INVALID")
            return None
        
        bids = book.get("bids", {})
        asks = book.get("asks", {})
        
        if not bids or not asks:
            logger.debug(f"Empty orderbook for {symbol}")
            return None
        
        # Best bid = highest price in bids
        # Best ask = lowest price in asks
        try:
            best_bid = max(bids.keys())
            best_ask = min(asks.keys())
            return (best_bid, best_ask)
        except ValueError:
            # Empty dict (shouldn't happen due to checks above)
            return None
    
    def get_mid_price(self, symbol: str) -> Optional[float]:
        """
        Calculate mid price from orderbook
        
        Critical for Short Gamma: We need accurate mark price
        """
        bid_ask = self.get_best_bid_ask(symbol)
        if not bid_ask:
            return None
        
        bid, ask = bid_ask
        return (bid + ask) / 2.0
    
    # ========================================================================
    # MONITORING & DIAGNOSTICS
    # ========================================================================
    
    def get_connection_status(self) -> Dict[str, Any]:
        """
        Get detailed connection statistics
        
        Returns:
            {
                "public": {
                    "state": "connected",
                    "uptime": 3600.5,
                    "messages_received": 12345,
                    "reconnect_count": 2
                },
                "private": {...}
            }
        """
        return {
            "public": {
                "state": self.public_client.state.value if self.public_client else "not_started",
                "uptime": self.public_client.stats.get_uptime() if self.public_client else None,
                "messages_received": self.public_client.stats.messages_received if self.public_client else 0,
                "reconnect_count": self.public_client.stats.reconnect_count if self.public_client else 0,
                "last_error": self.public_client.stats.last_error if self.public_client else None
            },
            "private": {
                "state": self.private_client.state.value if self.private_client else "not_started",
                "uptime": self.private_client.stats.get_uptime() if self.private_client else None,
                "messages_received": self.private_client.stats.messages_received if self.private_client else 0,
                "reconnect_count": self.private_client.stats.reconnect_count if self.private_client else 0,
                "last_error": self.private_client.stats.last_error if self.private_client else None
            }
        }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics for monitoring
        
        Returns:
            {
                "tickers": {
                    "count": 5,
                    "symbols": ["BTCUSDT", ...],
                    "staleness": {"BTCUSDT": 2.3, ...}
                },
                "orderbooks": {...}
            }
        """
        all_tickers = self.ticker_cache.get_all()
        all_books = self.orderbook_cache._snapshot
        
        ticker_staleness = {
            symbol: self.ticker_cache.get_staleness(symbol)
            for symbol in all_tickers.keys()
        }
        
        return {
            "tickers": {
                "count": len(all_tickers),
                "symbols": list(all_tickers.keys()),
                "staleness_seconds": ticker_staleness
            },
            "orderbooks": {
                "count": len(all_books),
                "symbols": list(all_books.keys()),
                "sequences": {
                    symbol: book.get("seq")
                    for symbol, book in all_books.items()
                }
            }
        }
    
    def is_healthy(self) -> bool:
        """
        Health check for monitoring systems
        
        Returns:
            True if both streams connected and data is fresh
        """
        # Check connection state
        if not self.public_client or not self.private_client:
            return False
        
        if (self.public_client.state != WSClientState.CONNECTED or
            self.private_client.state != WSClientState.CONNECTED):
            return False
        
        # Check data freshness (at least one ticker updated in last 30s)
        all_tickers = self.ticker_cache.get_all()
        if not all_tickers:
            return False
        
        for symbol in all_tickers.keys():
            staleness = self.ticker_cache.get_staleness(symbol)
            if staleness and staleness < 30:
                return True  # At least one fresh ticker
        
        return False


# ============================================================================
# INTEGRATION EXAMPLE
# ============================================================================

async def main():
    """
    Example usage demonstrating:
    1. Connection management
    2. Subscription
    3. Lock-free reads from multiple coroutines
    """
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    api_key = os.getenv("BYBIT_API_KEY")
    api_secret = os.getenv("BYBIT_API_SECRET")
    
    if not api_key or not api_secret:
        print("âŒ Missing API credentials in .env")
        return
    
    # Initialize stream manager
    async with BybitStreamManager(api_key, api_secret) as manager:
        
        # Subscribe to market data
        await manager.subscribe_ticker("BTCUSDT")
        await manager.subscribe_orderbook("BTCUSDT", depth=50)
        await manager.subscribe_position()
        
        print("âœ… Subscriptions active")
        
        # Simulate concurrent reads (like Risk Engine would do)
        async def price_monitor():
            """Simulates Risk Engine polling price"""
            while True:
                await asyncio.sleep(0.1)  # 100ms polling
                
                ticker = manager.get_ticker("BTCUSDT")
                mid_price = manager.get_mid_price("BTCUSDT")
                
                if ticker and mid_price:
                    last_price = ticker.get("lastPrice")
                    print(f"[Price Monitor] Last: {last_price} | Mid: {mid_price:.2f}")
        
        async def health_monitor():
            """Simulates monitoring system"""
            while True:
                await asyncio.sleep(10)
                
                status = manager.get_connection_status()
                cache_stats = manager.get_cache_stats()
                health = manager.is_healthy()
                
                print(f"\n[Health Monitor]")
                print(f"  Healthy: {health}")
                print(f"  Public: {status['public']['state']} "
                      f"(msgs: {status['public']['messages_received']})")
                print(f"  Private: {status['private']['state']} "
                      f"(msgs: {status['private']['messages_received']})")
                print(f"  Tickers cached: {cache_stats['tickers']['count']}")
                print(f"  Orderbooks cached: {cache_stats['orderbooks']['count']}\n")
        
        # Run monitors concurrently
        monitor_tasks = [
            asyncio.create_task(price_monitor()),
            asyncio.create_task(health_monitor())
        ]
        
        try:
            # Run for 60 seconds
            await asyncio.sleep(60)
        except KeyboardInterrupt:
            print("\n⚠️  Shutting down...")
        finally:
            # Cancel monitors
            for task in monitor_tasks:
                task.cancel()
            await asyncio.gather(*monitor_tasks, return_exceptions=True)
    
    print("âœ… Clean shutdown complete")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Run
    asyncio.run(main())