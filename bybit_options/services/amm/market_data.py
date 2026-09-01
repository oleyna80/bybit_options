import asyncio
from typing import Dict, Set, Optional, Callable
from decimal import Decimal
from loguru import logger
from pybit.unified_trading import WebSocket

class MarketDataActor:
    """
    Real-time Market Data Consumer (Websocket).
    Maintains a local cache of Tickers and Orderbooks.
    """
    
    def __init__(self, testnet: bool = False):
        self.testnet = testnet
        self.ws: Optional[WebSocket] = None
        self.ws_linear: Optional[WebSocket] = None  # NEW: For underlying prices
        self.active_symbols: Set[str] = set()
        
        # Cache
        # symbol -> { "mark_price": float, "bid": float, "ask": float, "iv": float }
        self.ticker_cache: Dict[str, Dict] = {}
        
        # NEW: Underlying prices cache (BTC -> 104523.45)
        self.underlying_cache: Dict[str, float] = {}
        
        # symbol -> { "update_id": int, "bids": [], "asks": [] }
        # Only needed for Sniper or deep liquidity check. 
        # For Gardener (Pricing), Ticker stream is usually sufficient (Best Bid/Ask).
        self.snapshot_cache: Dict[str, Dict] = {} 

    async def start(self):
        """Initialize Websocket Connection."""
        channel_type = "linear"  # For Options? Check Option support.
        # Bybit V5 Public WS has different categories? 
        # Actually standard V5 WS covers all.
        
        self.ws = WebSocket(
            testnet=self.testnet,
            channel_type="option", # Important: "option" for Option tickers
            trace_logging=False,
        )
        
        # Note: pybit WebSocket runs in a separate thread.
        # We need to bridge it to asyncio if we want async callbacks,
        # but for cache updates, threaded callbacks updating a dict is fine (atomic in GIL for simple dicts).
        
        logger.info("[AMM] Market Data Actor Started (Option + Linear channels)")

    def subscribe_underlying(self, base_coins: Set[str]):
        """
        Subscribe to perpetual tickers for underlying spot prices.
        
        Args:
            base_coins: Set of base coins (e.g., {"BTC", "ETH"})
        """
        if not base_coins:
            return
            
        logger.info(f"[AMM] Subscribing to {len(base_coins)} underlying tickers...")
        
        # Initialize linear WebSocket if needed
        if not self.ws_linear:
            self.ws_linear = WebSocket(
                testnet=self.testnet,
                channel_type="linear",
                trace_logging=False
            )
        
        # Subscribe to each underlying
        for coin in base_coins:
            symbol = f"{coin}USDT"
            try:
                self.ws_linear.ticker_stream(
                    symbol=symbol,
                    callback=self._handle_underlying
                )
                logger.info(f"[AMM] Subscribed to underlying: {symbol}")
            except Exception as e:
                logger.error(f"[AMM] Failed to subscribe to {symbol}: {e}")
    
    def _handle_underlying(self, message):
        """
        Callback for linear ticker updates (threaded by pybit).
        Updates underlying_cache with latest spot prices.
        """
        try:
            data = message.get("data")
            if not data:
                return
            
            symbol = data.get("symbol", "")
            last_price = data.get("lastPrice")
            
            if last_price:
                # Extract base coin (BTCUSDT -> BTC)
                base = symbol.replace("USDT", "")
                self.underlying_cache[base] = float(last_price)
                logger.debug(f"[AMM] Updated underlying {base}: {last_price}")
                
        except Exception as e:
            logger.error(f"[AMM] Underlying ticker parse error: {e}")

    def subscribe(self, symbols: Set[str]):
        """
        Subscribe to public tickers for list of symbols.
        """
        new_symbols = symbols - self.active_symbols
        if not new_symbols:
            return

        logger.info(f"[AMM] Subscribing to {len(new_symbols)} new symbols...")
        
        # Convert set to list
        sym_list = list(new_symbols)
        
        # Bybit V5 Option Tickers: tickers.{symbol}
        # Limit per request? Pybit handles splitting usually? 
        # Or we loop.
        
        for sym in sym_list:
            self.ws.ticker_stream(symbol=sym, callback=self._handle_ticker)
            self.active_symbols.add(sym)

    def _handle_ticker(self, message):
        """
        Callback from pybit (Threaded).
        Updates local cache.
        """
        try:
            data = message.get("data")
            if not data:
                return

            symbol = data.get("symbol")
            
            # Option Ticker Format (V5):
            # markPrice, bid1Price, ask1Price, markIv, etc.
            
            mp = data.get("markPrice")
            bid = data.get("bid1Price")
            ask = data.get("ask1Price")
            mark_iv = data.get("markIv")
            
            # Update Cache
            current = self.ticker_cache.get(symbol, {})
            if mp: current["mark_price"] = float(mp)
            if bid: current["bid"] = float(bid)
            if ask: current["ask"] = float(ask)
            if mark_iv: current["mark_iv"] = float(mark_iv)
            
            self.ticker_cache[symbol] = current
            
        except Exception as e:
            logger.error(f"[AMM] Ticker Parse Error: {e}")

    def get_market_iv(self, symbol: str) -> Optional[float]:
        """Returns latest Exchange Mark IV."""
        return self.ticker_cache.get(symbol, {}).get("mark_iv")

    def get_mark_price(self, symbol: str) -> Optional[float]:
        return self.ticker_cache.get(symbol, {}).get("mark_price")
        
    def get_best_bid(self, symbol: str) -> Optional[float]:
        return self.ticker_cache.get(symbol, {}).get("bid")
    
    def get_underlying_price(self, base_coin: str) -> Optional[float]:
        """
        Get cached spot price for underlying asset.
        
        Args:
            base_coin: Base coin symbol (e.g., "BTC", "ETH")
            
        Returns:
            Latest spot price or None if not available
        """
        return self.underlying_cache.get(base_coin)

    async def stop(self):
        if self.ws:
            # self.ws.exit() # pybit doesn't strictly have async close?
            pass
        logger.info("[AMM] Market Data Actor Stopped.")
