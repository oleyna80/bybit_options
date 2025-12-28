"""
Pydantic data models for type safety and API serialization
"""

from pydantic import BaseModel, Field, computed_field
from typing import Optional, Dict, List
from enum import Enum
from datetime import datetime


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


class CoinHolding(BaseModel):
    """Coin holdings in wallet"""

    coin: str = Field(description="Coin symbol (BTC, ETH, etc)")
    wallet_balance: float = Field(description="Amount held")
    usd_value: float = Field(description="Value in USD")
    equity: float = Field(description="Equity (includes unrealized PnL)")
    unrealized_pnl: float = Field(default=0.0, description="Unrealized PnL")

    class Config:
        json_schema_extra = {
            "example": {
                "coin": "ETH",
                "wallet_balance": 0.5,
                "usd_value": 1500.0,
                "equity": 1500.0,
                "unrealized_pnl": 100.0,
            }
        }


class GreeksModel(BaseModel):
    """Option Greeks - aggregatable metrics"""

    delta_coin: float = Field(0.0, description="Delta in base coin units")
    gamma_coin: float = Field(0.0, description="Gamma in base coin units")
    vega_usd: float = Field(0.0, description="Vega in USD")
    theta_usd: float = Field(0.0, description="Theta in USD per day")

    def __add__(self, other: "GreeksModel") -> "GreeksModel":
        """Allow aggregation of Greeks"""
        return GreeksModel(
            delta_coin=self.delta_coin + other.delta_coin,
            gamma_coin=self.gamma_coin + other.gamma_coin,
            vega_usd=self.vega_usd + other.vega_usd,
            theta_usd=self.theta_usd + other.theta_usd,
        )

    class Config:
        json_schema_extra = {
            "example": {
                "delta_coin": 0.5234,
                "gamma_coin": 0.000123,
                "vega_usd": 145.67,
                "theta_usd": -23.45,
            }
        }


class SlippageMetrics(BaseModel):
    """Slippage and liquidity metrics"""

    bid: float = Field(description="Best bid price")
    ask: float = Field(description="Best ask price")
    mark_price: float = Field(description="Mark price")
    spread_abs: float = Field(description="Absolute spread (Ask - Bid)")
    spread_pct: float = Field(description="Spread as % of mark price")
    mid_price: float = Field(description="(Bid + Ask) / 2")

    @computed_field
    @property
    def slippage_risk(self) -> str:
        """Classify slippage risk level"""
        if self.spread_pct < 0.5:
            return "LOW"
        elif self.spread_pct < 2.0:
            return "MEDIUM"
        else:
            return "HIGH"

    class Config:
        json_schema_extra = {
            "example": {
                "bid": 1234.5,
                "ask": 1256.8,
                "mark_price": 1245.0,
                "spread_abs": 22.3,
                "spread_pct": 1.79,
                "mid_price": 1245.65,
            }
        }


class IVMetrics(BaseModel):
    """Implied Volatility metrics"""

    position_iv: Optional[float] = Field(None, description="IV of the position")
    atm_iv: Optional[float] = Field(None, description="ATM IV for comparison")
    iv_diff_pct: Optional[float] = Field(None, description="% difference from ATM")

    @computed_field
    @property
    def is_expensive(self) -> Optional[bool]:
        """Is this position expensive relative to ATM?"""
        if self.iv_diff_pct is None:
            return None
        return self.iv_diff_pct > 10.0  # More than 10% premium

    class Config:
        json_schema_extra = {
            "example": {"position_iv": 0.72, "atm_iv": 0.65, "iv_diff_pct": 10.77}
        }


class GammaRentMetrics(BaseModel):
    """
    Gamma Rent calculation (Theta/Gamma ratio)

    Interpretation:
    - Negative (typical): Paying theta to hold gamma (long options)
    - More negative = More expensive gamma
    - Positive (rare): Earning theta while exposed to gamma (certain spreads)
    """

    theta_usd: float = Field(description="Theta in USD/day")
    gamma_coin: float = Field(description="Gamma in coin units")
    gamma_rent: Optional[float] = Field(
        None, description="Raw Theta/Gamma - maintains directional information"
    )

    @computed_field
    @property
    def gamma_rent_normalized(self) -> Optional[float]:
        """
        Normalized gamma rent: USD/day per 1.0 coin of gamma

        Example: -5000 means "I'm paying $5000/day per 1 BTC of gamma"
        More intuitive for cross-position comparison
        """
        if self.gamma_rent is None or abs(self.gamma_coin) < 1e-10:
            return None

        # This equals gamma_rent, but computed explicitly for clarity
        return self.theta_usd / self.gamma_coin if self.gamma_coin != 0 else None

    @computed_field
    @property
    def interpretation(self) -> str:
        """Human-readable interpretation"""
        if self.gamma_rent is None or self.gamma_rent == 0:
            return "N/A - No gamma exposure"

        if self.gamma_rent > 0:
            # Rare case: Short gamma with negative theta, or long gamma with positive theta
            return "Earning theta while holding gamma (unusual structure)"
        else:
            # Typical case: Paying theta to hold gamma (long options)
            abs_rent = abs(self.gamma_rent)
            if abs_rent > 10000:
                return f"Expensive gamma (paying ${abs_rent:,.0f}/day per coin)"
            elif abs_rent > 1000:
                return f"Moderate gamma cost (${abs_rent:,.0f}/day per coin)"
            else:
                return f"Cheap gamma (${abs_rent:,.0f}/day per coin)"

    class Config:
        json_schema_extra = {
            "example": {
                "theta_usd": -45.67,
                "gamma_coin": 0.00234,
                "gamma_rent": -19504.27,
                "interpretation": "Expensive gamma (paying $19,504/day per coin)",
            }
        }


class PositionModel(BaseModel):
    """Complete position model with all metrics"""

    symbol: str = Field(description="Trading symbol")
    side: PositionSide = Field(description="Buy or Sell")
    size: float = Field(description="Position size")
    pos_type: PositionType = Field(description="Position type")
    base_coin: str = Field(description="Base currency (BTC, ETH, etc)")

    # Option-specific fields
    series: Optional[str] = Field(None, description="Expiry date (e.g., 19DEC25)")
    option_type: Optional[OptionType] = Field(None, description="Call or Put")
    strike: Optional[float] = Field(None, description="Strike price")

    # Greeks
    greeks: GreeksModel = Field(default_factory=GreeksModel)

    # Risk metrics
    slippage: Optional[SlippageMetrics] = None
    iv_metrics: Optional[IVMetrics] = None
    gamma_rent: Optional[GammaRentMetrics] = None

    # Position value
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


class CoinRiskModel(BaseModel):
    """Risk aggregation for a single base coin"""

    base_coin: str

    # Aggregated Greeks
    total_greeks: GreeksModel = Field(default_factory=GreeksModel)
    futures_greeks: GreeksModel = Field(default_factory=GreeksModel)
    options_greeks: GreeksModel = Field(default_factory=GreeksModel)

    # Greeks by expiry series
    series_greeks: Dict[str, GreeksModel] = Field(default_factory=dict)

    # Underlying price
    underlying_price: Optional[float] = None

    # Positions
    positions: List[PositionModel] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "base_coin": "BTC",
                "total_greeks": {
                    "delta_coin": 2.3456,
                    "gamma_coin": 0.00123,
                    "vega_usd": 1234.56,
                    "theta_usd": -234.56,
                },
                "underlying_price": 98765.43,
            }
        }


class MarginModel(BaseModel):
    """Account margin and risk metrics"""

    account_type: str = Field(description="UNIFIED or CONTRACT")

    # Balance metrics
    total_equity: float = Field(description="Total account equity")
    available_balance: float = Field(description="Available for trading")
    used_margin: float = Field(description="Margin in use")

    # Risk metrics
    initial_margin: float = Field(0.0, description="Initial margin requirement")
    maintenance_margin: float = Field(0.0, description="Maintenance margin")
    margin_ratio: Optional[float] = Field(
        None, description="Used margin / Total equity %"
    )

    # Health indicators
    unrealized_pnl: float = Field(0.0, description="Unrealized P&L")
    realized_pnl: float = Field(0.0, description="Realized P&L")

    # Holdings
    holdings: List[CoinHolding] = Field(
        default_factory=list, description="Coin holdings in wallet"
    )

    @computed_field
    @property
    def health_status(self) -> str:
        """Account health classification"""
        if self.margin_ratio is None:
            return "UNKNOWN"
        if self.margin_ratio < 50:
            return "HEALTHY"
        elif self.margin_ratio < 75:
            return "MODERATE"
        else:
            return "HIGH_RISK"

    class Config:
        json_schema_extra = {
            "example": {
                "account_type": "UNIFIED",
                "total_equity": 50000.0,
                "available_balance": 25000.0,
                "used_margin": 25000.0,
                "maintenance_margin": 5000.0,
                "margin_ratio": 50.0,
                "unrealized_pnl": 1234.56,
                "holdings": [
                    {
                        "coin": "BTC",
                        "wallet_balance": 0.5,
                        "usd_value": 50000.0,
                        "equity": 50000.0,
                    }
                ],
            }
        }


class PortfolioRiskModel(BaseModel):
    """Complete portfolio risk snapshot"""

    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Margin & Account
    margin: MarginModel

    # Risk by coin
    coin_risks: Dict[str, CoinRiskModel] = Field(default_factory=dict)

    # Portfolio-wide Greeks (only Vega/Theta are aggregatable)
    total_vega_usd: float = 0.0
    total_theta_usd: float = 0.0

    # Warnings
    warnings: List[str] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2025-12-10T14:30:00Z",
                "margin": {"total_equity": 50000.0, "margin_ratio": 45.5},
                "total_vega_usd": 5678.90,
                "total_theta_usd": -987.65,
                "warnings": [
                    "HIGH GAMMA on BTC: 0.00234",
                    "NEGATIVE THETA: -${987.65}/day",
                ],
            }
        }


class PerpetualOHLCV(BaseModel):
    """Daily OHLCV data for Perpetual Futures (e.g., BTC-PERPETUAL)"""

    timestamp: datetime = Field(description="Date (UTC start of day)")
    open: float = Field(description="Open price")
    high: float = Field(description="High price")
    low: float = Field(description="Low price")
    close: float = Field(description="Close price")
    volume: float = Field(description="Trading volume (in coin)")

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2025-12-21T00:00:00Z",
                "open": 50000.0,
                "high": 51000.0,
                "low": 49500.0,
                "close": 50500.0,
                "volume": 1234.56,
            }
        }


class OptionIVDaily(BaseModel):
    """Daily Implied Volatility snapshot for ATM monthly option"""

    timestamp: datetime = Field(description="Date (UTC start of day)")
    atm_strike: float = Field(description="ATM Strike price used")
    iv_value: float = Field(description="Implied Volatility (e.g., 0.65 for 65%)")
    days_to_expiry: int = Field(description="Days to expiry of the option series")

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2025-12-21T00:00:00Z",
                "atm_strike": 50000.0,
                "iv_value": 0.685,
                "days_to_expiry": 31,
            }
        }


class IVRankDaily(BaseModel):
    """Daily calculated IV Rank (0-100) based on 30-day rolling window"""

    timestamp: datetime = Field(description="Date (UTC start of day)")
    iv_rank: float = Field(description="IV Rank (0-100)")
    current_iv: float = Field(description="Current IV used for calculation")
    min_iv_30d: float = Field(description="Min IV in the 30-day window")
    max_iv_30d: float = Field(description="Max IV in the 30-day window")

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2025-12-21T00:00:00Z",
                "iv_rank": 75.5,
                "current_iv": 0.685,
                "min_iv_30d": 0.55,
                "max_iv_30d": 0.70,
            }
        }


# --- Response Models for API ---


class PriceHistoryResponse(BaseModel):
    """Response model for price history API"""

    symbol: str = Field(description="Symbol, e.g., BTC-PERPETUAL")
    candles: List[PerpetualOHLCV] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "BTC-PERPETUAL",
                "candles": [
                    # ... list of PerpetualOHLCV examples
                ],
            }
        }


class IVHistoryResponse(BaseModel):
    """Response model for IV history API"""

    base_coin: str = Field(description="Base coin, e.g., BTC")
    iv_data: List[OptionIVDaily] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "base_coin": "BTC",
                "iv_data": [
                    # ... list of OptionIVDaily examples
                ],
            }
        }


class IVRankHistoryResponse(BaseModel):
    """Response model for IV Rank history API"""

    base_coin: str = Field(description="Base coin, e.g., BTC")
    iv_rank_data: List[IVRankDaily] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "base_coin": "BTC",
                "iv_rank_data": [
                    # ... list of IVRankDaily examples
                ],
            }
        }


# Re-export strategy models for backward compatibility
# These imports allow existing code to import from data_models
# while keeping strategy-specific models in separate module
try:
    from strategy_models import (
        StrategyType,
        IronCondorLeg,
        IronCondorConfig,
        HedgeInstrument,
        HedgeRecommendation,
        ScenarioParameters,
        ScenarioResult,
        AnalysisResult,
        ExportFormat,
        ExportRequest,
    )
except ImportError:
    # Define placeholder classes if strategy_models is not available
    class StrategyType:
        pass

    class IronCondorLeg:
        pass

    class IronCondorConfig:
        pass

    class HedgeInstrument:
        pass

    class HedgeRecommendation:
        pass

    class ScenarioParameters:
        pass

    class ScenarioResult:
        pass

    class AnalysisResult:
        pass

    class ExportFormat:
        pass

    class ExportRequest:
        pass
