"""Greeks and risk metric models."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, computed_field


class GreeksModel(BaseModel):
    """Option Greeks - aggregatable metrics."""

    delta_coin: float = Field(0.0, description="Delta in base coin units")
    gamma_coin: float = Field(0.0, description="Gamma in base coin units")
    vega_usd: float = Field(0.0, description="Vega in USD")
    theta_usd: float = Field(0.0, description="Theta in USD per day")

    def __add__(self, other: "GreeksModel") -> "GreeksModel":
        """Allow aggregation of Greeks."""
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
    """Slippage and liquidity metrics."""

    bid: float = Field(description="Best bid price")
    ask: float = Field(description="Best ask price")
    mark_price: float = Field(description="Mark price")
    spread_abs: float = Field(description="Absolute spread (Ask - Bid)")
    spread_pct: float = Field(description="Spread as % of mark price")
    mid_price: float = Field(description="(Bid + Ask) / 2")

    @computed_field
    @property
    def slippage_risk(self) -> str:
        """Classify slippage risk level."""
        if self.spread_pct < 0.5:
            return "LOW"
        if self.spread_pct < 2.0:
            return "MEDIUM"
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
    """Implied Volatility metrics."""

    position_iv: Optional[float] = Field(None, description="IV of the position")
    atm_iv: Optional[float] = Field(None, description="ATM IV for comparison")
    iv_diff_pct: Optional[float] = Field(None, description="% difference from ATM")

    @computed_field
    @property
    def is_expensive(self) -> Optional[bool]:
        """Is this position expensive relative to ATM?"""
        if self.iv_diff_pct is None:
            return None
        return self.iv_diff_pct > 10.0

    class Config:
        json_schema_extra = {
            "example": {"position_iv": 0.72, "atm_iv": 0.65, "iv_diff_pct": 10.77}
        }


class GammaRentMetrics(BaseModel):
    """Gamma Rent calculation (Theta/Gamma ratio)."""

    theta_usd: float = Field(description="Theta in USD/day")
    gamma_coin: float = Field(description="Gamma in coin units")
    gamma_rent: Optional[float] = Field(
        None, description="Raw Theta/Gamma - maintains directional information"
    )

    @computed_field
    @property
    def gamma_rent_normalized(self) -> Optional[float]:
        """Normalized gamma rent: USD/day per 1.0 coin of gamma."""
        if self.gamma_rent is None or abs(self.gamma_coin) < 1e-10:
            return None
        return self.theta_usd / self.gamma_coin if self.gamma_coin != 0 else None

    @computed_field
    @property
    def interpretation(self) -> str:
        """Human-readable interpretation."""
        if self.gamma_rent is None or self.gamma_rent == 0:
            return "N/A - No gamma exposure"

        if self.gamma_rent > 0:
            return "Earning theta while holding gamma (unusual structure)"

        abs_rent = abs(self.gamma_rent)
        if abs_rent > 10000:
            return f"Expensive gamma (paying ${abs_rent:,.0f}/day per coin)"
        if abs_rent > 1000:
            return f"Moderate gamma cost (${abs_rent:,.0f}/day per coin)"
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
