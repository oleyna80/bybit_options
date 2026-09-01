"""Position-related models and enums."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from bybit_options.models.greeks import GreeksModel, SlippageMetrics, IVMetrics, GammaRentMetrics


class PositionSide(str, Enum):
    BUY = "Buy"
    SELL = "Sell"


class PositionType(str, Enum):
    LINEAR = "LINEAR"
    OPTION = "OPTION"
    INVERSE = "INVERSE"


class OptionType(str, Enum):
    CALL = "C"
    PUT = "P"


class PositionModel(BaseModel):
    """Complete position model with all metrics."""

    symbol: str = Field(description="Trading symbol")
    side: PositionSide = Field(description="Buy or Sell")
    size: float = Field(description="Position size")
    pos_type: PositionType = Field(description="Position type")
    base_coin: str = Field(description="Base currency (BTC, ETH, etc)")

    series: Optional[str] = Field(None, description="Expiry date (e.g., 19DEC25)")
    option_type: Optional[OptionType] = Field(None, description="Call or Put")
    strike: Optional[float] = Field(None, description="Strike price")

    greeks: GreeksModel = Field(default_factory=GreeksModel)

    slippage: Optional[SlippageMetrics] = None
    iv_metrics: Optional[IVMetrics] = None
    gamma_rent: Optional[GammaRentMetrics] = None

    entry_price: Optional[float] = None
    mark_value: Optional[float] = None
    unrealized_pnl: Optional[float] = None

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "BTC-19DEC25-100000-C-USDT",
                "side": "Buy",
                "size": 1.5,
                "pos_type": "OPTION",
                "base_coin": "BTC",
                "series": "19DEC25",
                "option_type": "C",
                "strike": 100000.0,
                "greeks": {
                    "delta_coin": 0.7523,
                    "gamma_coin": 0.000045,
                    "vega_usd": 234.56,
                    "theta_usd": -45.67,
                },
            }
        }
