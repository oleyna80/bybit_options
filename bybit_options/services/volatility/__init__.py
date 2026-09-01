"""
Volatility Intelligence Module.

Provides comprehensive volatility analysis for Trading Expert:
- IV Rank integration
- Historical Volatility calculation
- Volatility Smile analysis (market + SVI model)
- Unified context API

Usage:
    from bybit_options.services.volatility import VolatilityContextAPI
    
    api = VolatilityContextAPI()
    context = await api.get_context("BTC")
"""

from .iv_rank_connector import IVRankConnector, IVRankData
from .hv_calculator import HVCalculator, HVData
from .smile_analyzer import SmileAnalyzer, VolatilitySmile, SmilePoint
from .context_api import VolatilityContextAPI, VolatilityContext

__all__ = [
    "IVRankConnector",
    "IVRankData",
    "HVCalculator", 
    "HVData",
    "SmileAnalyzer",
    "VolatilitySmile",
    "SmilePoint",
    "VolatilityContextAPI",
    "VolatilityContext",
]
