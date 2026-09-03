"""
Option Board Service
Retrieves real-time option board data, caches it, and broadcasts updates via WebSocket.
"""

import asyncio
import time
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime

from bybit_options.services.bybit_connector import BybitConnector
from websocket_manager import get_websocket_manager
from option_board_utils import (
    generate_option_symbols,
    parse_option_symbol,
    format_option_display,
    calculate_board_statistics,
    get_all_option_series,
    fetch_option_tickers
)

logger = logging.getLogger(__name__)


@dataclass
class OptionBoard:
    """
    Represents a snapshot of the Option Board for a specific expiry.
    Optimized for fast lookup/serialization.
    """
    timestamp: float
    base_coin: str
    expiry: str
    underlying_price: float
    # List of option objects (dicts) for easy JSON serialization
    options: List[Dict[str, Any]]
    statistics: Dict[str, Any]
    
    # Lookup map for fast access: symbol -> option_data
    _symbol_map: Dict[str, Dict[str, Any]] = field(default_factory=dict, repr=False)

    def __post_init__(self):
        """Build internal lookup map for O(1) access."""
        if not self._symbol_map and self.options:
            for opt in self.options:
                self._symbol_map[opt['symbol']] = opt

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization (excluding private fields)."""
        return {
            "timestamp": datetime.fromtimestamp(self.timestamp).isoformat(),
            "base_coin": self.base_coin,
            "expiry": self.expiry,
            "underlying_price": self.underlying_price,
            "options": self.options,
            "statistics": self.statistics,
            "count": len(self.options)
        }

    def get_option(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fast lookup by symbol."""
        return self._symbol_map.get(symbol)


class OptionBoardService:
    """
    Service for fetching and managing Option Board data.
    Implements Caching and Pub/Sub broadcasting.
    """

    def __init__(self, connector: BybitConnector, cache_ttl: float = 1.0):
        """
        Args:
            connector: Initialized BybitConnector
            cache_ttl: Cache Time-To-Live in seconds (default: 1.0s)
        """
        self.connector = connector
        self.cache_ttl = cache_ttl
        
        # Cache storage: key=(base_coin, expiry) -> value=(hit_time, OptionBoard)
        self._cache: Dict[tuple, tuple] = {}

    async def get_board(
        self, 
        base_coin: str = "BTC", 
        expiry: str = None,
        force_refresh: bool = False
    ) -> Optional[OptionBoard]:
        """
        Get option board for a specific expiry.
        
        Args:
            base_coin: Base currency (e.g., "BTC")
            expiry: Expiry date (e.g., "2JAN26"). If None, finds nearest.
            force_refresh: Ignore cache if True.
            
        Returns:
            OptionBoard object or None if failed.
        """
        # 0. Resolve Expiry if missing
        if not expiry:
            series = await get_all_option_series(self.connector, base_coin)
            if not series:
                logger.warning(f"No option series found for {base_coin}")
                return None
            expiry = series[0]  # Nearest expiry
            
        # 1. Check Cache
        cache_key = (base_coin, expiry)
        if not force_refresh and cache_key in self._cache:
            hit_time, cached_board = self._cache[cache_key]
            age = time.time() - hit_time
            if age < self.cache_ttl:
                logger.debug(f"OptionBoard cache hit for {cache_key} (age={age:.3f}s)")
                return cached_board

        # 2. Fetch Fresh Data
        try:
            start_time = time.time()
            board = await self._fetch_fresh_board(base_coin, expiry)
            
            if board:
                # 3. Update Cache
                self._cache[cache_key] = (time.time(), board)
                
                # 4. Broadcast to WebSocket (Fire-and-forget logic)
                # We reuse the global manager instance
                ws_manager = get_websocket_manager()
                # We await it here because it's just pushing to local queues, not IO blocking
                await ws_manager.broadcast_options_board_update(board.to_dict())
                
                duration = (time.time() - start_time) * 1000
                logger.info(f"Fetched & Broadcasted OptionBoard {base_coin}-{expiry} in {duration:.1f}ms")
                
            return board

        except Exception as e:
            logger.error(f"Failed to fetch option board for {base_coin}-{expiry}: {e}", exc_info=True)
            return None

    async def _fetch_fresh_board(self, base_coin: str, expiry: str) -> Optional[OptionBoard]:
        """Internal method to perform API calls."""
        
        # A. Fetch Underlying Price (Parallel)
        # B. Fetch Option Tickers (Parallel Batching)
        
        # 1. Prepare tasks
        underlying_symbol = f"{base_coin}USDT"
        
        # We need option symbols first to fetch tickers
        # Standard range: 75k-110k is hardcoded in old script, but we should probably be dynamic?
        # For V1, let's stick to the generated range or finding all available chain ticks.
        # Actually, best practice is to ask exchange for all symbols of that expiry.
        # But `generate_option_symbols` was used before.
        # Let's improve: Get ALL symbols for this expiry from instruments info first?
        # Or stick to the utility's logic.
        # Logic in `get_option_board.py` utilized `get_all_option_series` then `get_real_option_symbols`
        # `get_real_option_symbols` fetches ALL instruments and filters.
        # Let's reuse `get_real_option_symbols` logic but optimized.
        
        # Fetch underlying ticker
        ticker_task = self.connector.get_tickers(category="spot", symbol=underlying_symbol)
        
        # Fetch instruments to get symbols (if we don't assume range)
        # Using the helper from utils which fetches instruments
        # We'll need to import or implement logic similar to `get_real_option_symbols` from the script
        # Since that function was in the script, not utils, let's check utils again.
        # Utils has `generate_option_symbols` (static). The script had `get_real_option_symbols`.
        # I should probably reimplement `get_real_option_symbols` logic here or move it to utils.
        # For now, I'll inline a robust version here using `get_instruments_info`.
        
        instruments_task = self.connector.get_instruments_info(
            category="option",
            base_coin=base_coin
        )
        
        results = await asyncio.gather(ticker_task, instruments_task, return_exceptions=True)
        
        # Process Underlying Price
        underlying_res = results[0]
        underlying_price = 0.0
        if not isinstance(underlying_res, Exception) and underlying_res:
             underlying_price = float(underlying_res[0].get("lastPrice", 0))

        # Process Symbols
        instruments_res = results[1]
        if isinstance(instruments_res, Exception) or not instruments_res:
            logger.error("Failed to fetch option instruments")
            return None
            
        # Filter for our expiry
        symbols = []
        for inst in instruments_res:
            sym = inst.get("symbol", "")
            if f"-{expiry}-" in sym and sym.endswith("-USDT"):
                # Clean symbol for util compatibility
                symbols.append(sym.replace("-USDT", ""))
        
        if not symbols:
            logger.warning(f"No symbols found for {base_coin}-{expiry}")
            return None
            
        # 2. Fetch Tickers for these symbols
        # Uses utility for batch fetching
        tickers_map = await fetch_option_tickers(self.connector, symbols, batch_size=20)
        
        # 3. Format Data
        formatted_options = []
        
        for sym in symbols:
            # We need the full -USDT for the map lookup in tickers_map?
            # fetch_option_tickers uses normalized symbol.
            # let's try to match.
            full_sym = f"{sym}-USDT"
            ticker = tickers_map.get(full_sym) or tickers_map.get(sym)
            
            if not ticker:
                continue
                
            try:
                # Parse symbol
                parsed = parse_option_symbol(full_sym)
                
                # Format
                opt_data = format_option_display(parsed, ticker, underlying_price)
                formatted_options.append(opt_data)
            except Exception as e:
                # logger.warning(f"Error parsing {sym}: {e}")
                continue

        # 4. Calculate Stats
        stats = calculate_board_statistics(formatted_options)
        
        return OptionBoard(
            timestamp=time.time(),
            base_coin=base_coin,
            expiry=expiry,
            underlying_price=underlying_price,
            options=formatted_options,
            statistics=stats
        )
