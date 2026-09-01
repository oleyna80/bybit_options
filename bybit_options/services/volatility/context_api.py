"""
Volatility Context API.
Unified access point for all volatility intelligence.
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime

from loguru import logger

from .iv_rank_connector import IVRankConnector, IVRankData
from .hv_calculator import HVCalculator, HVData
from .smile_analyzer import SmileAnalyzer, VolatilitySmile


@dataclass
class VolatilityContext:
    """
    Complete volatility context for decision making.
    This is what Trading Expert receives.
    """
    symbol: str
    timestamp: datetime
    
    # IV Rank
    iv_rank: float
    iv_regime: str  # "HIGH", "NORMAL", "LOW"
    current_iv: float
    
    # Historical Volatility
    hv_7d: float
    hv_30d: float
    hv_90d: float
    iv_hv_ratio: Optional[float]
    hv_signal: str  # "SELL_PREMIUM", "BUY_PREMIUM", "NEUTRAL"
    
    # Smile (optional - may not be available for all expiries)
    atm_iv: Optional[float] = None
    put_skew: Optional[float] = None
    call_skew: Optional[float] = None
    skew_slope: Optional[float] = None
    
    @property
    def overall_signal(self) -> str:
        """
        Combined signal based on all factors.
        """
        signals = []
        
        # IV Rank signal
        if self.iv_regime == "HIGH":
            signals.append("SELL")
        elif self.iv_regime == "LOW":
            signals.append("BUY")
        
        # IV/HV signal
        if self.hv_signal == "SELL_PREMIUM":
            signals.append("SELL")
        elif self.hv_signal == "BUY_PREMIUM":
            signals.append("BUY")
        
        # Count votes
        sell_count = signals.count("SELL")
        buy_count = signals.count("BUY")
        
        if sell_count > buy_count:
            return "SELL_PREMIUM"
        elif buy_count > sell_count:
            return "BUY_PREMIUM"
        else:
            return "NEUTRAL"


class VolatilityContextAPI:
    """
    Main API for volatility intelligence.
    
    Usage:
        api = VolatilityContextAPI()
        context = await api.get_context("BTC")
        print(context.overall_signal)  # "SELL_PREMIUM"
    """
    
    def __init__(self, market_data=None, timeframe: str = "1d"):
        """
        Args:
            market_data: Optional MarketDataActor for smile analysis
            timeframe: "1d" or "4h" for HV calculation
        """
        self.iv_rank = IVRankConnector()
        self.hv_calc = HVCalculator(timeframe=timeframe)
        self.smile = SmileAnalyzer(market_data) if market_data else SmileAnalyzer()
    
    async def get_context(
        self,
        symbol: str = "BTC",
        include_smile: bool = False,
        expiry: Optional[str] = None,
        spot_price: Optional[float] = None
    ) -> VolatilityContext:
        """
        Get full volatility context.
        
        Args:
            symbol: Base coin
            include_smile: Whether to analyze volatility smile
            expiry: Expiry for smile analysis (required if include_smile)
            spot_price: Current spot (for smile analysis)
        
        Returns:
            VolatilityContext with all metrics
        """
        try:
            # Ensure database is connected
            from bybit_options.services.delta.database_config import db
            await db.connect()
            
            # Get IV Rank
            iv_data = await self.iv_rank.get_current(symbol)
            
            current_iv = iv_data.current_iv if iv_data else 0.65  # Default
            iv_rank_value = iv_data.iv_rank if iv_data else 50.0
            iv_regime = iv_data.regime if iv_data else "NORMAL"
            
            # Get HV
            hv_data = await self.hv_calc.calculate(symbol, current_iv=current_iv)
            
            # Get Smile (optional)
            smile_data: Optional[VolatilitySmile] = None
            if include_smile and expiry:
                spot = spot_price or 100000.0  # Default BTC spot
                smile_data = await self.smile.build_smile(symbol, expiry, spot)
            
            return VolatilityContext(
                symbol=symbol,
                timestamp=datetime.utcnow(),
                iv_rank=iv_rank_value,
                iv_regime=iv_regime,
                current_iv=current_iv,
                hv_7d=hv_data.hv_7d,
                hv_30d=hv_data.hv_30d,
                hv_90d=hv_data.hv_90d,
                iv_hv_ratio=hv_data.iv_hv_ratio,
                hv_signal=hv_data.signal,
                atm_iv=smile_data.atm_iv if smile_data else None,
                put_skew=smile_data.put_skew_25d if smile_data else None,
                call_skew=smile_data.call_skew_25d if smile_data else None,
                skew_slope=smile_data.skew_slope if smile_data else None
            )
            
        except Exception as e:
            logger.error(f"Failed to get volatility context: {e}")
            # Return minimal context
            return VolatilityContext(
                symbol=symbol,
                timestamp=datetime.utcnow(),
                iv_rank=50.0,
                iv_regime="NORMAL",
                current_iv=0.65,
                hv_7d=0.0,
                hv_30d=0.0,
                hv_90d=0.0,
                iv_hv_ratio=None,
                hv_signal="NEUTRAL"
            )
    
    async def get_iv_rank_history(
        self,
        symbol: str = "BTC",
        days: int = 365
    ) -> list:
        """
        Get IV Rank history for charting.
        
        Returns:
            List of IVRankData
        """
        # Ensure database is connected
        from bybit_options.services.delta.database_config import db
        await db.connect()
        
        return await self.iv_rank.get_history(symbol, days)
