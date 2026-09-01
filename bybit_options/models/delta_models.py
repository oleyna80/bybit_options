"""
Delta System Data Models
========================
Pydantic models for normalized multi-exchange data.

Database Mappings:
- LargeTradeModel → delta_analytics_db.large_trades
- OrderbookSnapshotModel → delta_analytics_db.orderbook_snapshots
- DeltaMetricsModel → delta_analytics_db.delta_metrics
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal
from datetime import datetime, timezone
from decimal import Decimal


class LargeTradeModel(BaseModel):
    """
    Normalized model for large trades (>= 5 BTC or >= 50 ETH).
    
    Validation:
    - BTC pairs: quantity >= 5
    - ETH pairs: quantity >= 50
    """
    exchange: Literal['bybit', 'deribit', 'binance', 'okx']
    market_type: Literal['spot', 'perpetual', 'futures', 'options']
    symbol: str
    price: Decimal = Field(description="Exact price (no float rounding)")
    quantity: Decimal = Field(description="Trade volume")
    side: Literal['Buy', 'Sell']
    trade_id: str = Field(description="Unique ID from exchange")
    timestamp: datetime
    
    @validator('quantity')
    def validate_large_trade_threshold(cls, v, values):
        """Ensure trade meets minimum threshold"""
        symbol = values.get('symbol', '')
        
        if 'ETH' in symbol.upper():
            if v < Decimal('50'):
                raise ValueError(f"ETH trade must be >= 50 ETH, got {v}")
        else:
            if v < Decimal('5'):
                raise ValueError(f"Trade must be >= 5, got {v}")
        
        return v
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v),
            datetime: lambda v: v.isoformat()
        }


class OrderbookLevel(BaseModel):
    """Single price level: [price, size]"""
    price: Decimal
    size: Decimal


class OrderbookSnapshotModel(BaseModel):
    """
    Normalized orderbook snapshot (top 20 levels).
    
    Fields:
    - bids/asks: Top 20 levels
    - imbalance: (bid - ask) / (bid + ask), range [-1, 1]
    """
    exchange: Literal['bybit', 'deribit', 'binance', 'okx']
    symbol: str
    timestamp: datetime
    bids: List[OrderbookLevel] = Field(max_items=20)
    asks: List[OrderbookLevel] = Field(max_items=20)
    bid_volume_total: Decimal
    ask_volume_total: Decimal
    imbalance: Optional[Decimal] = Field(default=None, ge=-1.0, le=1.0)
    
    @validator('imbalance', pre=True, always=True)
    def calculate_imbalance(cls, v, values):
        """Auto-calculate imbalance if not provided"""
        if v is not None:
            return v
        
        bid_vol = values.get('bid_volume_total', Decimal('0'))
        ask_vol = values.get('ask_volume_total', Decimal('0'))
        total = bid_vol + ask_vol
        
        if total == 0:
            return Decimal('0')
        
        return (bid_vol - ask_vol) / total
    
    @classmethod
    def from_raw_orderbook(
        cls,
        exchange: str,
        symbol: str,
        bids_raw: List[List],
        asks_raw: List[List],
        timestamp: Optional[datetime] = None
    ):
        """Factory method: create from raw exchange data"""
        bids = [
            OrderbookLevel(price=Decimal(str(p)), size=Decimal(str(s)))
            for p, s in bids_raw[:20]
        ]
        
        asks = [
            OrderbookLevel(price=Decimal(str(p)), size=Decimal(str(s)))
            for p, s in asks_raw[:20]
        ]
        
        bid_total = sum(b.size for b in bids)
        ask_total = sum(a.size for a in asks)
        
        return cls(
            exchange=exchange,
            symbol=symbol,
            timestamp=timestamp or datetime.now(timezone.utc),
            bids=bids,
            asks=asks,
            bid_volume_total=bid_total,
            ask_volume_total=ask_total
            # imbalance calculated by validator
        )
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v),
            datetime: lambda v: v.isoformat()
        }


class DeltaMetricsModel(BaseModel):
    """Computed Delta metrics for a time interval"""
    exchange: str
    symbol: str
    interval: Literal['1m', '5m', '15m', '1h']
    timestamp: datetime
    
    filtered_buy_volume: Decimal = Decimal('0')
    filtered_sell_volume: Decimal = Decimal('0')
    filtered_delta: Decimal = Decimal('0')
    large_trades_count: int = 0
    
    absorbed_bid_liquidity: Optional[Decimal] = None
    absorbed_ask_liquidity: Optional[Decimal] = None
    open_interest: Optional[Decimal] = None
    open_interest_delta: Optional[Decimal] = None
    avg_imbalance: Optional[Decimal] = None
    max_imbalance: Optional[Decimal] = None
    
    @validator('filtered_delta', pre=True, always=True)
    def calculate_filtered_delta(cls, v, values):
        """Auto-calculate delta if not provided"""
        if v != Decimal('0'):
            return v
        
        buy = values.get('filtered_buy_volume', Decimal('0'))
        sell = values.get('filtered_sell_volume', Decimal('0'))
        return buy - sell
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v),
            datetime: lambda v: v.isoformat()
        }


class OpenInterestModel(BaseModel):
    """
    Open Interest Data Model.
    
    Collection:
    - Interval: 1m or 5m
    - Source: /v5/market/open-interest
    """
    exchange: Literal['bybit', 'deribit', 'binance', 'okx']
    symbol: str
    open_interest: Decimal
    timestamp: datetime
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v),
            datetime: lambda v: v.isoformat()
        }