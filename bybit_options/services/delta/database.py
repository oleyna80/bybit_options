"""
Delta Analytics Service - Database Models
=========================================
SQLAlchemy ORM models for Delta Analytics.

Tables:
- large_trades: Individual whale trades.
- orderbook_snapshots: OB state and imbalance.
- delta_metrics: Aggregated delta candles.
"""

from sqlalchemy import Column, String, Integer, Numeric, DateTime, JSON
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class LargeTrade(Base):
    """
    Store individual large trades.
    Hypertable candidates (partitioned by timestamp).
    """
    __tablename__ = 'large_trades'

    timestamp = Column(DateTime(timezone=True), primary_key=True, nullable=False)
    trade_id = Column(String(64), primary_key=True, nullable=False)
    symbol = Column(String(20), nullable=False, index=True)
    exchange = Column(String(20), nullable=False)
    price = Column(Numeric(20, 8), nullable=False)
    quantity = Column(Numeric(20, 8), nullable=False)
    side = Column(String(4), nullable=False)  # 'Buy' or 'Sell'
    market_type = Column(String(10), nullable=False) # 'option', 'perp'

    def __repr__(self):
        return f"<LargeTrade(symbol={self.symbol}, side={self.side}, qty={self.quantity})>"


class OrderbookSnapshot(Base):
    """
    Store OB state and imbalance snapshots.
    """
    __tablename__ = 'orderbook_snapshots'

    timestamp = Column(DateTime(timezone=True), primary_key=True, nullable=False)
    symbol = Column(String(20), primary_key=True, nullable=False)
    exchange = Column(String(20), primary_key=True, nullable=False)
    
    bid_vol_total = Column(Numeric(20, 8), nullable=False)
    ask_vol_total = Column(Numeric(20, 8), nullable=False)
    imbalance = Column(Numeric(5, 4), nullable=False) # -1.0 to 1.0
    
    # Full snapshots stored as JSONB for replay/debugging
    bids_json = Column(JSON, nullable=True)
    asks_json = Column(JSON, nullable=True)

    def __repr__(self):
        return f"<OrderbookSnapshot(symbol={self.symbol}, imbalance={self.imbalance})>"


class DeltaMetrics(Base):
    """
    Aggregated Delta metrics for strategy consumption.
    """
    __tablename__ = 'delta_metrics'

    timestamp = Column(DateTime(timezone=True), primary_key=True, nullable=False)
    symbol = Column(String(20), primary_key=True, nullable=False)
    interval = Column(String(5), primary_key=True, nullable=False) # '1m', '5m'
    
    filtered_buy_volume = Column(Numeric(20, 8), default=0)
    filtered_sell_volume = Column(Numeric(20, 8), default=0)
    filtered_delta = Column(Numeric(20, 8), nullable=False)
    large_trades_count = Column(Integer, default=0)
    avg_imbalance = Column(Numeric(5, 4), nullable=True)

    def __repr__(self):
        return f"<DeltaMetrics(symbol={self.symbol}, interval={self.interval}, delta={self.filtered_delta})>"
