"""
Historical Volatility Calculator.
Calculates realized volatility from OHLCV data.
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime

import numpy as np
from loguru import logger


@dataclass
class HVData:
    """Historical Volatility metrics."""
    symbol: str
    hv_7d: float          # 7-day HV (annualized)
    hv_30d: float         # 30-day HV
    hv_90d: float         # 90-day HV
    current_iv: Optional[float] = None  # For comparison
    iv_hv_ratio: Optional[float] = None  # IV / HV_30d
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    @property
    def signal(self) -> str:
        """
        Trading signal based on IV/HV ratio.
        """
        if self.iv_hv_ratio is None:
            return "NEUTRAL"
        
        if self.iv_hv_ratio > 1.2:
            return "SELL_PREMIUM"  # IV overpriced
        elif self.iv_hv_ratio < 0.8:
            return "BUY_PREMIUM"   # IV underpriced
        else:
            return "NEUTRAL"


class HVCalculator:
    """
    Historical Volatility Calculator.
    
    Supports:
    - Daily candles (default)
    - 4H candles (for more precision)
    """
    
    def __init__(self, timeframe: str = "1d"):
        """
        Args:
            timeframe: "1d" for daily, "4h" for 4-hour candles
        """
        self.timeframe = timeframe
        # Annualization factor
        if timeframe == "1d":
            self.ann_factor = np.sqrt(365)  # Crypto trades 24/7
        else:  # 4h
            self.ann_factor = np.sqrt(365 * 6)  # 6 candles per day
    
    async def calculate(
        self, 
        symbol: str = "BTC",
        current_iv: Optional[float] = None
    ) -> HVData:
        """
        Calculate HV for multiple windows.
        
        Args:
            symbol: Base coin
            current_iv: Current ATM IV for ratio calculation
        
        Returns:
            HVData with 7/30/90 day HV
        """
        try:
            from bybit_options.services.delta.database_config import db
            
            # Fetch OHLCV data (need 100+ candles for 90-day HV)
            query = """
                SELECT close
                FROM perpetual_ohlcv
                WHERE symbol = $1
                ORDER BY timestamp DESC
                LIMIT 100
            """
            
            rows = await db.fetch(query, f"{symbol}USDT")
            
            if not rows:
                logger.warning(f"No OHLCV data found for {symbol}USDT")
                return HVData(
                    symbol=symbol,
                    hv_7d=0.0,
                    hv_30d=0.0,
                    hv_90d=0.0
                )
            
            # Convert to numpy array (reverse to get chronological order)
            closes = np.array([float(row["close"]) for row in rows])[::-1]
            
            # Calculate HV for each window
            hv_7d = self._calculate_hv(closes, 7)
            hv_30d = self._calculate_hv(closes, 30)
            hv_90d = self._calculate_hv(closes, 90)
            
            # Calculate IV/HV ratio if current_iv provided
            iv_hv_ratio = None
            if current_iv is not None and hv_30d > 0.001:
                iv_hv_ratio = current_iv / hv_30d
            
            return HVData(
                symbol=symbol,
                hv_7d=hv_7d,
                hv_30d=hv_30d,
                hv_90d=hv_90d,
                current_iv=current_iv,
                iv_hv_ratio=iv_hv_ratio
            )
            
        except Exception as e:
            logger.error(f"Failed to calculate HV for {symbol}: {e}")
            return HVData(
                symbol=symbol,
                hv_7d=0.0,
                hv_30d=0.0,
                hv_90d=0.0
            )
    
    def _calculate_hv(self, closes: np.ndarray, window: int) -> float:
        """
        Calculate HV for specific window.
        
        Args:
            closes: Array of close prices (chronological order)
            window: Number of periods
        
        Returns:
            Annualized volatility (e.g., 0.65 = 65%)
        """
        if len(closes) < window + 1:
            logger.warning(f"Not enough data for HV-{window}: {len(closes)} candles")
            return 0.0
        
        # Use last `window` periods
        recent_closes = closes[-(window + 1):]
        
        # Log returns
        log_returns = np.log(recent_closes[1:] / recent_closes[:-1])
        
        # Handle edge case: zero or negative prices
        log_returns = log_returns[np.isfinite(log_returns)]
        
        if len(log_returns) == 0:
            return 0.0
        
        # Standard deviation
        std = np.std(log_returns)
        
        # Annualize
        hv = std * self.ann_factor
        
        return float(hv)
