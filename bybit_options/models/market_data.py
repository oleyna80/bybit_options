"""Market data models and API responses."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class PerpetualOHLCV(BaseModel):
    """Daily OHLCV data for Perpetual Futures (e.g., BTC-PERPETUAL)."""

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
    """Daily Implied Volatility snapshot for ATM monthly option."""

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
    """Daily calculated IV Rank (0-100) based on 30-day rolling window."""

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


class PriceHistoryResponse(BaseModel):
    """Response model for price history API."""

    symbol: str = Field(description="Symbol, e.g., BTC-PERPETUAL")
    candles: List[PerpetualOHLCV] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "BTC-PERPETUAL",
                "candles": [],
            }
        }


class IVHistoryResponse(BaseModel):
    """Response model for IV history API."""

    base_coin: str = Field(description="Base coin, e.g., BTC")
    iv_data: List[OptionIVDaily] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "base_coin": "BTC",
                "iv_data": [],
            }
        }


class IVRankHistoryResponse(BaseModel):
    """Response model for IV Rank history API."""

    base_coin: str = Field(description="Base coin, e.g., BTC")
    iv_rank_data: List[IVRankDaily] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "base_coin": "BTC",
                "iv_rank_data": [],
            }
        }


class OptionBoardOption(BaseModel):
    """Single option entry in the options board response."""

    symbol: str
    clean_symbol: str
    base_coin: str
    expiry: str
    strike: float
    type: str
    type_code: str
    moneyness: str
    prices: dict
    spread: dict
    iv: dict
    greeks: dict
    liquidity: dict
    value_analysis: dict


class OptionsBoardResponse(BaseModel):
    """Response model for options board API."""

    base_coin: str
    underlying_price: float
    options: List[OptionBoardOption] = Field(default_factory=list)
    options_count: int = 0
    series: List[str] = Field(default_factory=list)
    expiry: Optional[str] = None
    option_type: Optional[str] = None
    sort_by: str
    sort_order: str
    limit: int
