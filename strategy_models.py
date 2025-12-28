"""
Pydantic data models for options trading strategies
Compatible with existing data_models.py structure
"""

from pydantic import BaseModel, Field, computed_field
from typing import Optional, Dict, List, Tuple
from enum import Enum
from datetime import datetime
from decimal import Decimal

# Re-export existing enums for compatibility
from data_models import PositionSide, OptionType, GreeksModel, PositionModel


class StrategyType(str, Enum):
    """Types of options strategies"""

    IRON_CONDOR = "IRON_CONDOR"
    STRADDLE = "STRADDLE"
    STRANGLE = "STRANGLE"
    VERTICAL_SPREAD = "VERTICAL_SPREAD"
    BUTTERFLY = "BUTTERFLY"
    CALENDAR_SPREAD = "CALENDAR_SPREAD"
    DIAGONAL_SPREAD = "DIAGONAL_SPREAD"


class IronCondorLeg(BaseModel):
    """Single leg of an Iron Condor strategy"""

    symbol: str = Field(description="Option symbol (e.g., BTC-19DEC25-90000-P)")
    side: PositionSide = Field(description="BUY or SELL")
    option_type: OptionType = Field(description="CALL or PUT")
    strike: float = Field(description="Strike price")
    size: float = Field(description="Number of contracts")
    greeks: GreeksModel = Field(
        default_factory=GreeksModel, description="Option Greeks"
    )
    mark_price: Optional[float] = Field(None, description="Current mark price")

    @computed_field
    @property
    def direction_multiplier(self) -> float:
        """Multiplier for Greeks based on position side"""
        return 1.0 if self.side == PositionSide.BUY else -1.0

    @computed_field
    @property
    def vega_contribution(self) -> float:
        """Vega contribution of this leg (signed)"""
        return self.greeks.vega_usd * self.size * self.direction_multiplier

    @computed_field
    @property
    def delta_contribution(self) -> float:
        """Delta contribution of this leg (signed)"""
        return self.greeks.delta_coin * self.size * self.direction_multiplier

    @computed_field
    @property
    def gamma_contribution(self) -> float:
        """Gamma contribution of this leg (signed)"""
        return self.greeks.gamma_coin * self.size * self.direction_multiplier

    @computed_field
    @property
    def theta_contribution(self) -> float:
        """Theta contribution of this leg (signed)"""
        return self.greeks.theta_usd * self.size * self.direction_multiplier

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "BTC-19DEC25-90000-P",
                "side": "Sell",
                "option_type": "P",
                "strike": 90000.0,
                "size": 1.0,
                "greeks": {
                    "delta_coin": 0.32,
                    "gamma_coin": 0.000045,
                    "vega_usd": 125.45,
                    "theta_usd": 45.67,
                },
                "mark_price": 1234.56,
            }
        }


class IronCondorConfig(BaseModel):
    """Configuration for Iron Condor strategy"""

    underlying: str = Field("BTC", description="Underlying asset (BTC, ETH, etc)")
    expiry: str = Field(description="Expiry date in format DDMMMYY (e.g., 19DEC25)")

    # Strike prices (must be ordered: LP < SP < SC < LC)
    long_put_strike: float = Field(description="Long Put strike (lowest)")
    short_put_strike: float = Field(description="Short Put strike")
    short_call_strike: float = Field(description="Short Call strike")
    long_call_strike: float = Field(description="Long Call strike (highest)")

    # Position sizes (default 1 contract each)
    sizes: Dict[str, float] = Field(
        default_factory=lambda: {
            "long_put": 1.0,
            "short_put": 1.0,
            "long_call": 1.0,
            "short_call": 1.0,
        },
        description="Size for each leg in contracts",
    )

    # Additional configuration
    target_credit: Optional[float] = Field(None, description="Target credit received")
    max_loss: Optional[float] = Field(None, description="Maximum loss allowed")

    @computed_field
    @property
    def put_spread_width(self) -> float:
        """Width of the put spread"""
        return self.short_put_strike - self.long_put_strike

    @computed_field
    @property
    def call_spread_width(self) -> float:
        """Width of the call spread"""
        return self.long_call_strike - self.short_call_strike

    @computed_field
    @property
    def is_symmetric(self) -> bool:
        """Check if the Iron Condor is symmetric"""
        return (
            abs(self.put_spread_width - self.call_spread_width)
            / max(self.put_spread_width, self.call_spread_width)
            < 0.1
        )  # Within 10%

    @computed_field
    @property
    def validation_errors(self) -> List[str]:
        """Validate the Iron Condor configuration"""
        errors = []

        # Check strike ordering
        if not (
            self.long_put_strike
            < self.short_put_strike
            < self.short_call_strike
            < self.long_call_strike
        ):
            errors.append("Strikes must be ordered: LP < SP < SC < LC")

        # Check spread widths
        if self.put_spread_width <= 0 or self.call_spread_width <= 0:
            errors.append("Spread distances must be positive")

        # Check position sizes
        for leg_name, size in self.sizes.items():
            if size <= 0:
                errors.append(f"Size for {leg_name} must be positive")

        return errors

    class Config:
        json_schema_extra = {
            "example": {
                "underlying": "BTC",
                "expiry": "19DEC25",
                "long_put_strike": 85000.0,
                "short_put_strike": 90000.0,
                "short_call_strike": 100000.0,
                "long_call_strike": 105000.0,
                "sizes": {
                    "long_put": 1.0,
                    "short_put": 1.0,
                    "long_call": 1.0,
                    "short_call": 1.0,
                },
            }
        }


class HedgeInstrument(BaseModel):
    """Instrument used for hedging"""

    instrument_type: str = Field(description="Type of hedge (STRADDLE, STRANGLE, etc)")
    call_symbol: Optional[str] = Field(None, description="Call option symbol")
    put_symbol: Optional[str] = Field(None, description="Put option symbol")
    strike: Optional[float] = Field(None, description="Strike price (for single leg)")
    unit_vega: float = Field(description="Vega per unit of hedge instrument")
    unit_delta: float = Field(description="Delta per unit of hedge instrument")
    unit_gamma: float = Field(description="Gamma per unit of hedge instrument")
    unit_theta: float = Field(description="Theta per unit of hedge instrument")
    mark_price: Optional[float] = Field(None, description="Current mark price")

    class Config:
        json_schema_extra = {
            "example": {
                "instrument_type": "STRADDLE",
                "call_symbol": "BTC-19DEC25-95000-C",
                "put_symbol": "BTC-19DEC25-95000-P",
                "unit_vega": 245.67,
                "unit_delta": 0.05,
                "unit_gamma": 0.00012,
                "unit_theta": -45.67,
                "mark_price": 2345.67,
            }
        }


class HedgeRecommendation(BaseModel):
    """Recommendation for hedging a position"""

    instrument: HedgeInstrument = Field(description="Hedge instrument to use")
    optimal_quantity: float = Field(description="Optimal quantity to hedge")
    hedge_cost: Optional[float] = Field(None, description="Cost of hedge (premium)")
    effectiveness: float = Field(description="Effectiveness of hedge (0-100%)")

    # Impact on portfolio Greeks after hedge
    delta_impact: float = Field(0.0, description="Change in portfolio delta")
    gamma_impact: float = Field(0.0, description="Change in portfolio gamma")
    vega_impact: float = Field(0.0, description="Change in portfolio vega")
    theta_impact: float = Field(0.0, description="Change in portfolio theta")

    @computed_field
    @property
    def is_cost_effective(self) -> bool:
        """Check if hedge is cost-effective"""
        if self.hedge_cost is None:
            return True
        # Simple heuristic: hedge cost should be less than 10% of position value
        return self.hedge_cost < 1000  # Placeholder - should be based on position size

    class Config:
        json_schema_extra = {
            "example": {
                "instrument": {"instrument_type": "STRADDLE", "unit_vega": 245.67},
                "optimal_quantity": 0.21,
                "hedge_cost": 1234.56,
                "effectiveness": 92.5,
                "delta_impact": 0.03,
                "vega_impact": 51.38,
            }
        }


class ScenarioParameters(BaseModel):
    """Parameters for scenario analysis"""

    price_range_pct: Tuple[float, float] = Field(
        (-15.0, 15.0), description="Price range as % from current"
    )
    iv_range_pct: Tuple[float, float] = Field(
        (-10.0, 20.0), description="IV range as % from current"
    )
    time_horizon_days: float = Field(
        7.0, description="Time horizon for analysis (days)"
    )
    price_steps: int = Field(50, description="Number of price steps in simulation")
    iv_steps: int = Field(20, description="Number of IV steps in simulation")

    class Config:
        json_schema_extra = {
            "example": {
                "price_range_pct": (-15.0, 15.0),
                "iv_range_pct": (-10.0, 20.0),
                "time_horizon_days": 7.0,
                "price_steps": 50,
                "iv_steps": 20,
            }
        }


class ScenarioResult(BaseModel):
    """Result of a single scenario simulation"""

    underlying_price: float = Field(description="Simulated underlying price")
    iv_change_pct: float = Field(description="Simulated IV change (%)")
    time_elapsed_days: float = Field(description="Time elapsed (days)")

    # P&L components
    pnl_total: float = Field(description="Total P&L")
    pnl_delta: float = Field(description="P&L from delta")
    pnl_gamma: float = Field(description="P&L from gamma")
    pnl_vega: float = Field(description="P&L from vega")
    pnl_theta: float = Field(description="P&L from theta")

    # Greeks after scenario
    delta_after: float = Field(description="Delta after scenario")
    gamma_after: float = Field(description="Gamma after scenario")
    vega_after: float = Field(description="Vega after scenario")
    theta_after: float = Field(description="Theta after scenario")

    class Config:
        json_schema_extra = {
            "example": {
                "underlying_price": 95000.0,
                "iv_change_pct": 5.0,
                "time_elapsed_days": 7.0,
                "pnl_total": 1234.56,
                "pnl_delta": 567.89,
                "pnl_gamma": 234.56,
                "pnl_vega": 345.67,
                "pnl_theta": 86.44,
            }
        }


class AnalysisResult(BaseModel):
    """Complete analysis result for a strategy"""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    strategy_type: StrategyType = Field(description="Type of strategy analyzed")
    config: IronCondorConfig = Field(description="Strategy configuration")

    # Current market data
    underlying_price: float = Field(description="Current underlying price")
    current_iv: float = Field(description="Current implied volatility")

    # Strategy legs with market data
    legs: List[IronCondorLeg] = Field(default_factory=list, description="Strategy legs")

    # Aggregated Greeks
    net_vega: float = Field(description="Net vega exposure")
    net_delta: float = Field(description="Net delta exposure")
    net_gamma: float = Field(description="Net gamma exposure")
    net_theta: float = Field(description="Net theta exposure")

    # Hedge recommendations
    hedge_recommendation: Optional[HedgeRecommendation] = Field(
        None, description="Vega hedge recommendation"
    )

    # Scenario analysis
    scenario_results: List[ScenarioResult] = Field(
        default_factory=list, description="Scenario simulation results"
    )

    # Risk metrics
    max_profit: Optional[float] = Field(None, description="Maximum possible profit")
    max_loss: Optional[float] = Field(None, description="Maximum possible loss")
    breakeven_points: List[float] = Field(
        default_factory=list, description="Breakeven price points"
    )

    # Warnings and recommendations
    warnings: List[str] = Field(default_factory=list, description="Risk warnings")
    recommendations: List[str] = Field(
        default_factory=list, description="Action recommendations"
    )

    @computed_field
    @property
    def is_vega_neutral(self) -> bool:
        """Check if position is vega neutral (within tolerance)"""
        return abs(self.net_vega) < 10.0  # Within $10 vega exposure

    @computed_field
    @property
    def is_delta_neutral(self) -> bool:
        """Check if position is delta neutral (within tolerance)"""
        return abs(self.net_delta) < 0.1  # Within 0.1 BTC delta

    @computed_field
    @property
    def risk_summary(self) -> Dict[str, str]:
        """Generate risk summary"""
        summary = {}

        # Vega risk
        if abs(self.net_vega) > 100:
            summary["vega"] = "HIGH - Significant vega exposure"
        elif abs(self.net_vega) > 50:
            summary["vega"] = "MEDIUM - Moderate vega exposure"
        else:
            summary["vega"] = "LOW - Minimal vega exposure"

        # Delta risk
        if abs(self.net_delta) > 0.5:
            summary["delta"] = "HIGH - Significant directional exposure"
        elif abs(self.net_delta) > 0.2:
            summary["delta"] = "MEDIUM - Moderate directional exposure"
        else:
            summary["delta"] = "LOW - Near delta neutral"

        # Gamma risk
        if self.net_gamma < -0.0005:
            summary["gamma"] = "HIGH - Negative gamma (vulnerable to large moves)"
        elif self.net_gamma < -0.0001:
            summary["gamma"] = "MEDIUM - Some negative gamma"
        else:
            summary["gamma"] = "LOW - Minimal gamma risk"

        # Theta risk
        if self.net_theta > 50:
            summary["theta"] = "POSITIVE - Earning time decay"
        elif self.net_theta > 0:
            summary["theta"] = "SLIGHTLY POSITIVE - Small time decay benefit"
        elif self.net_theta < -50:
            summary["theta"] = "NEGATIVE - Paying time decay"
        else:
            summary["theta"] = "NEUTRAL - Minimal time decay impact"

        return summary

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2025-12-26T12:00:00Z",
                "strategy_type": "IRON_CONDOR",
                "underlying_price": 95000.0,
                "current_iv": 0.65,
                "net_vega": -51.38,
                "net_delta": 0.28,
                "net_gamma": -0.00034,
                "net_theta": 14.44,
                "max_profit": 2345.67,
                "max_loss": -1234.56,
                "breakeven_points": [88500.0, 101500.0],
                "warnings": ["Negative gamma exposure", "Short vega position"],
                "recommendations": ["Consider vega hedge with ATM straddle"],
            }
        }


class ExportFormat(str, Enum):
    """Formats for exporting analysis results"""

    JSON = "json"
    CSV = "csv"
    HTML = "html"
    TEXT = "text"
    PNG = "png"


class ExportRequest(BaseModel):
    """Request for exporting analysis results"""

    analysis_result: AnalysisResult = Field(description="Analysis result to export")
    format: ExportFormat = Field(description="Export format")
    include_graphs: bool = Field(True, description="Include graphs in export")
    include_raw_data: bool = Field(False, description="Include raw data in export")

    class Config:
        json_schema_extra = {
            "example": {
                "analysis_result": {
                    "timestamp": "2025-12-26T12:00:00Z",
                    "strategy_type": "IRON_CONDOR",
                },
                "format": "json",
                "include_graphs": True,
                "include_raw_data": False,
            }
        }
