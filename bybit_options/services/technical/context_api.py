"""
Technical Context API.

Provides unified multi-timeframe technical analysis combining:
- Alligator states (W1, D1, H4)
- Key fractals (support/resistance levels)
- Global trend determination
- Trading signals for Trading Expert
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

from loguru import logger

from bybit_options.services.technical.alligator_state import (
    AlligatorStateDetector,
    AlligatorContext,
    AlligatorState,
)


@dataclass
class FractalLevel:
    """Represents a key fractal level (support or resistance)."""
    price: float
    direction: str  # "UP" | "DOWN"
    timeframe: str
    candle_time: datetime
    is_key: bool
    distance_pct: float  # Distance from current price in %


@dataclass
class TechnicalContext:
    """Complete technical analysis context across all timeframes."""
    symbol: str
    timestamp: datetime
    current_price: float
    
    # Alligator states by timeframe
    alligator_w1: Optional[AlligatorContext] = None
    alligator_d1: Optional[AlligatorContext] = None
    alligator_h4: Optional[AlligatorContext] = None
    
    # Nearest key fractals
    nearest_resistance: Optional[FractalLevel] = None
    nearest_support: Optional[FractalLevel] = None
    
    # Global trend (based on W1)
    global_trend: str = "NEUTRAL"  # "BULLISH" | "BEARISH" | "NEUTRAL"
    
    # Signal for Trading Expert
    trend_signal: str = "NEUTRAL"  # "BUY_DELTA" | "SELL_DELTA" | "NEUTRAL"
    signal_confidence: float = 0.0  # 0.0 - 1.0


class TechnicalContextAPI:
    """
    Unified API for technical analysis across multiple timeframes.
    
    Hierarchy:
    W1 (Weekly) → Global trend, primary
    D1 (Daily) → Confirmation, fallback
    H4 (4-hour) → Tactical trend, entry timing
    """
    
    def __init__(self, db_pool, kline_loader=None):
        """
        Initialize Technical Context API.
        
        Args:
            db_pool: asyncpg pool for database access
            kline_loader: KlineLoader instance (optional, will try to import if None)
        """
        self.db_pool = db_pool
        self.kline_loader = kline_loader
        self.alligator_detector = AlligatorStateDetector()
    
    async def get_context(self, symbol: str) -> TechnicalContext:
        """
        Get complete technical context for a symbol.
        
        Args:
            symbol: Base symbol (e.g., "BTC")
            
        Returns:
            TechnicalContext with multi-timeframe analysis
        """
        symbol_usdt = f"{symbol}USDT"
        
        # 1. Load candles for all timeframes
        candles_w1 = await self._load_candles(symbol_usdt, "W1", 50)
        candles_d1 = await self._load_candles(symbol_usdt, "D1", 100)
        candles_h4 = await self._load_candles(symbol_usdt, "H4", 200)
        
        # Get current price
        current_price = float(candles_h4[-1]["close"]) if candles_h4 else 0.0
        
        # 2. Detect Alligator states
        alligator_w1 = self.alligator_detector.detect(candles_w1) if len(candles_w1) >= 2 else None
        alligator_d1 = self.alligator_detector.detect(candles_d1) if len(candles_d1) >= 2 else None
        alligator_h4 = self.alligator_detector.detect(candles_h4) if len(candles_h4) >= 2 else None
        
        # 3. Get nearest fractals
        fractals = await self._get_nearest_fractals(symbol_usdt, current_price)
        
        # 4. Determine global trend
        global_trend = self._determine_global_trend(alligator_w1, alligator_d1)
        
        # 5. Generate trading signal
        signal, confidence = self._generate_signal(
            global_trend, alligator_h4, fractals, current_price
        )
        
        return TechnicalContext(
            symbol=symbol,
            timestamp=datetime.utcnow(),
            current_price=current_price,
            alligator_w1=alligator_w1,
            alligator_d1=alligator_d1,
            alligator_h4=alligator_h4,
            nearest_resistance=fractals.get("resistance"),
            nearest_support=fractals.get("support"),
            global_trend=global_trend,
            trend_signal=signal,
            signal_confidence=confidence
        )
    
    async def _load_candles(self, symbol: str, timeframe: str, limit: int) -> List[Dict]:
        """
        Load candles for a given symbol and timeframe.
        
        Args:
            symbol: Symbol with quote (e.g., "BTCUSDT")
            timeframe: W1, D1, H4, H1
            limit: Number of candles to load
            
        Returns:
            List of candle dicts with OHLCV
        """
        # For now, use perpetual_ohlcv table
        # TODO: Implement proper multi-timeframe candle loading
        try:
            from bybit_options.services.delta.database_config import db
            
            # Map timeframe to interval in minutes
            interval_map = {
                "W1": 10080,  # 7 * 24 * 60
                "D1": 1440,   # 24 * 60
                "H4": 240,
                "H1": 60
            }
            
            interval = interval_map.get(timeframe, 240)
            
            await db.connect()
            
            # Query candles from perpetual_ohlcv
            # Note: This is a simplified implementation
            # In production, you'd want a proper candle aggregation service
            query = """
                SELECT 
                    timestamp as time,
                    open,
                    high,
                    low,
                    close,
                    volume
                FROM perpetual_ohlcv
                WHERE symbol = $1
                ORDER BY timestamp DESC
                LIMIT $2
            """
            
            rows = await db.fetch(query, symbol, limit)
            
            if not rows:
                logger.warning(f"No candles found for {symbol} {timeframe}")
                return []
            
            # Convert to candle dicts and reverse (oldest first)
            candles = [
                {
                    "time": row["time"],
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": float(row["volume"]) if row["volume"] else 0.0
                }
                for row in reversed(rows)
            ]
            
            return candles
            
        except Exception as e:
            logger.error(f"Failed to load candles for {symbol} {timeframe}: {e}")
            return []
    
    async def _get_nearest_fractals(
        self, 
        symbol: str, 
        current_price: float
    ) -> Dict[str, Optional[FractalLevel]]:
        """
        Get nearest support and resistance fractals.
        
        Args:
            symbol: Symbol with quote
            current_price: Current price for distance calculation
            
        Returns:
            Dict with 'support' and 'resistance' FractalLevel or None
        """
        try:
            from bybit_options.services.delta.database_config import db
            await db.connect()
            
            # Get nearest resistance (UP fractal above current price)
            resistance_query = """
                SELECT price, fractal_type, candle_time, timeframe, is_key_fractal
                FROM fractals_cache
                WHERE symbol = $1 
                  AND fractal_type = 'UP'
                  AND price > $2
                  AND is_key_fractal = TRUE
                ORDER BY price ASC
                LIMIT 1
            """
            
            # Get nearest support (DOWN fractal below current price)
            support_query = """
                SELECT price, fractal_type, candle_time, timeframe, is_key_fractal
                FROM fractals_cache
                WHERE symbol = $1 
                  AND fractal_type = 'DOWN'
                  AND price < $2
                  AND is_key_fractal = TRUE
                ORDER BY price DESC
                LIMIT 1
            """
            
            resistance_row = await db.fetchrow(resistance_query, symbol, current_price)
            support_row = await db.fetchrow(support_query, symbol, current_price)
            
            resistance = None
            if resistance_row:
                price = float(resistance_row["price"])
                resistance = FractalLevel(
                    price=price,
                    direction="UP",
                    timeframe=resistance_row["timeframe"],
                    candle_time=resistance_row["candle_time"],
                    is_key=resistance_row["is_key_fractal"],
                    distance_pct=((price - current_price) / current_price) * 100
                )
            
            support = None
            if support_row:
                price = float(support_row["price"])
                support = FractalLevel(
                    price=price,
                    direction="DOWN",
                    timeframe=support_row["timeframe"],
                    candle_time=support_row["candle_time"],
                    is_key=support_row["is_key_fractal"],
                    distance_pct=((current_price - price) / current_price) * 100
                )
            
            return {"resistance": resistance, "support": support}
            
        except Exception as e:
            logger.error(f"Failed to get fractals for {symbol}: {e}")
            return {"resistance": None, "support": None}
    
    def _determine_global_trend(
        self, 
        w1: Optional[AlligatorContext], 
        d1: Optional[AlligatorContext]
    ) -> str:
        """
        Determine global trend based on W1 and D1 Alligator states.
        
        W1 (Weekly) is primary, D1 (Daily) is fallback.
        
        Args:
            w1: W1 Alligator context
            d1: D1 Alligator context
            
        Returns:
            "BULLISH" | "BEARISH" | "NEUTRAL"
        """
        if not w1:
            # Fallback to D1 if W1 not available
            if not d1:
                return "NEUTRAL"
            w1 = d1
        
        # W1 EATING = strong trend
        if w1.state == AlligatorState.EATING_UP and w1.trend_direction == "UP":
            return "BULLISH"
        elif w1.state == AlligatorState.EATING_DOWN and w1.trend_direction == "DOWN":
            return "BEARISH"
        
        # W1 AWAKENING = emerging trend
        elif w1.state == AlligatorState.AWAKENING:
            if w1.trend_direction == "UP":
                return "BULLISH"
            elif w1.trend_direction == "DOWN":
                return "BEARISH"
        
        # W1 SLEEPING = check D1 as fallback
        elif w1.state == AlligatorState.SLEEPING:
            if d1:
                if d1.state in (AlligatorState.EATING_UP, AlligatorState.AWAKENING) and d1.trend_direction == "UP":
                    return "BULLISH"
                elif d1.state in (AlligatorState.EATING_DOWN, AlligatorState.AWAKENING) and d1.trend_direction == "DOWN":
                    return "BEARISH"
        
        return "NEUTRAL"
    
    def _generate_signal(
        self,
        global_trend: str,
        h4_alligator: Optional[AlligatorContext],
        fractals: Dict[str, Optional[FractalLevel]],
        current_price: float
    ) -> tuple:
        """
        Generate trading signal based on multi-timeframe analysis.
        
        Args:
            global_trend: Global trend (BULLISH/BEARISH/NEUTRAL)
            h4_alligator: H4 Alligator context for timing
            fractals: Nearest fractals
            current_price: Current price
            
        Returns:
            (signal, confidence) tuple
        """
        # If no H4 data, return neutral
        if not h4_alligator:
            return "NEUTRAL", 0.5
        
        # Strong bullish signal: W1 bullish + H4 confirms
        if global_trend == "BULLISH" and h4_alligator.trend_direction == "UP":
            # Higher confidence if H4 is also EATING
            confidence = 0.9 if h4_alligator.state == AlligatorState.EATING_UP else 0.7
            return "BUY_DELTA", confidence
        
        # Strong bearish signal: W1 bearish + H4 confirms
        elif global_trend == "BEARISH" and h4_alligator.trend_direction == "DOWN":
            confidence = 0.9 if h4_alligator.state == AlligatorState.EATING_DOWN else 0.7
            return "SELL_DELTA", confidence
        
        # Neutral trend or conflicting signals
        else:
            return "NEUTRAL", 0.5
