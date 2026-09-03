"""Portfolio and aggregation models."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, computed_field

from bybit_options.models.greeks import GreeksModel
from bybit_options.models.positions import PositionModel


class CoinHolding(BaseModel):
    """Coin holdings in wallet."""

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


class CoinRiskModel(BaseModel):
    """Risk aggregation for a single base coin."""

    base_coin: str

    total_greeks: GreeksModel = Field(default_factory=GreeksModel)
    futures_greeks: GreeksModel = Field(default_factory=GreeksModel)
    options_greeks: GreeksModel = Field(default_factory=GreeksModel)

    series_greeks: Dict[str, GreeksModel] = Field(default_factory=dict)

    underlying_price: Optional[float] = None

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
    """Account margin and risk metrics."""

    account_type: str = Field(description="UNIFIED or CONTRACT")

    total_equity: float = Field(description="Total account equity")
    available_balance: float = Field(description="Available for trading")
    used_margin: float = Field(description="Margin in use")

    initial_margin: float = Field(0.0, description="Initial margin requirement")
    maintenance_margin: float = Field(0.0, description="Maintenance margin")
    margin_ratio: Optional[float] = Field(
        None, description="Used margin / Total equity %"
    )

    unrealized_pnl: float = Field(0.0, description="Unrealized P&L")
    realized_pnl: float = Field(0.0, description="Realized P&L")

    holdings: List[CoinHolding] = Field(
        default_factory=list, description="Coin holdings in wallet"
    )

    @computed_field
    @property
    def health_status(self) -> str:
        """Account health classification."""
        if self.margin_ratio is None:
            return "UNKNOWN"
        if self.margin_ratio < 50:
            return "HEALTHY"
        if self.margin_ratio < 75:
            return "MODERATE"
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
    """Complete portfolio risk snapshot."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)

    margin: MarginModel

    coin_risks: Dict[str, CoinRiskModel] = Field(default_factory=dict)

    total_vega_usd: float = 0.0
    total_theta_usd: float = 0.0

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
