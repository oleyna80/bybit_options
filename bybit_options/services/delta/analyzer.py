"""Delta Volume Analyzer for calculating metrics from TimescaleDB."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, List, Optional

from loguru import logger

from bybit_options.services.delta.database_config import db


class DeltaAnalyzer:
    """
    Analyzer for Delta Volume metrics.
    
    Features:
    - Query TimescaleDB continuous aggregates
    - Calculate CVD (Cumulative Volume Delta)
    - Detect price/delta divergences
    - Orderbook imbalance analysis
    - Open Interest change tracking
    """

    def __init__(self, exchange: str = "bybit"):
        self.exchange = exchange

    async def get_hourly_delta(
        self,
        symbol: str,
        hours: int = 1
    ) -> Dict:
        """
        Get delta metrics for the last N hours.
        
        Args:
            symbol: Trading pair (e.g., "BTCUSDT")
            hours: Number of hours to look back
            
        Returns:
            {
                "symbol": "BTCUSDT",
                "period_hours": 1,
                "buy_volume": Decimal("150.5"),
                "sell_volume": Decimal("120.3"),
                "filtered_delta": Decimal("30.2"),
                "trade_count": 45,
                "avg_price": Decimal("93000.50"),
                "timestamp_start": datetime,
                "timestamp_end": datetime
            }
        """
        query = """
            SELECT
                symbol,
                SUM(buy_volume) as buy_volume,
                SUM(sell_volume) as sell_volume,
                SUM(filtered_delta) as filtered_delta,
                SUM(trade_count) as trade_count,
                AVG(avg_price) as avg_price,
                MIN(bucket) as timestamp_start,
                MAX(bucket) as timestamp_end
            FROM delta_metrics_1h
            WHERE exchange = $1
              AND symbol = $2
              AND bucket >= NOW() - INTERVAL '1 hour' * $3
            GROUP BY symbol
        """
        
        async with db.acquire() as conn:
            row = await conn.fetchrow(query, self.exchange, symbol, hours)
            
        if not row:
            return {
                "symbol": symbol,
                "period_hours": hours,
                "buy_volume": Decimal("0"),
                "sell_volume": Decimal("0"),
                "filtered_delta": Decimal("0"),
                "trade_count": 0,
                "avg_price": None,
                "timestamp_start": None,
                "timestamp_end": None
            }
            
        return {
            "symbol": row["symbol"],
            "period_hours": hours,
            "buy_volume": Decimal(str(row["buy_volume"] or 0)),
            "sell_volume": Decimal(str(row["sell_volume"] or 0)),
            "filtered_delta": Decimal(str(row["filtered_delta"] or 0)),
            "trade_count": int(row["trade_count"] or 0),
            "avg_price": Decimal(str(row["avg_price"])) if row["avg_price"] else None,
            "timestamp_start": row["timestamp_start"],
            "timestamp_end": row["timestamp_end"]
        }

    async def get_daily_delta(
        self,
        symbol: str,
        date: Optional[datetime] = None
    ) -> Dict:
        """
        Get delta metrics for a specific day.
        
        Args:
            symbol: Trading pair
            date: Date to analyze (default: today)
            
        Returns:
            Same structure as get_hourly_delta
        """
        if date is None:
            date = datetime.now(timezone.utc)
            
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        query = """
            SELECT
                symbol,
                SUM(buy_volume) as buy_volume,
                SUM(sell_volume) as sell_volume,
                SUM(filtered_delta) as filtered_delta,
                SUM(trade_count) as trade_count,
                AVG(avg_price) as avg_price,
                MIN(bucket) as timestamp_start,
                MAX(bucket) as timestamp_end
            FROM delta_metrics_1h
            WHERE exchange = $1
              AND symbol = $2
              AND bucket >= $3
              AND bucket < $4
            GROUP BY symbol
        """
        
        async with db.acquire() as conn:
            row = await conn.fetchrow(
                query, self.exchange, symbol, start_of_day, end_of_day
            )
            
        if not row:
            return {
                "symbol": symbol,
                "date": date.date(),
                "buy_volume": Decimal("0"),
                "sell_volume": Decimal("0"),
                "filtered_delta": Decimal("0"),
                "trade_count": 0,
                "avg_price": None,
                "timestamp_start": None,
                "timestamp_end": None
            }
            
        return {
            "symbol": row["symbol"],
            "date": date.date(),
            "buy_volume": Decimal(str(row["buy_volume"] or 0)),
            "sell_volume": Decimal(str(row["sell_volume"] or 0)),
            "filtered_delta": Decimal(str(row["filtered_delta"] or 0)),
            "trade_count": int(row["trade_count"] or 0),
            "avg_price": Decimal(str(row["avg_price"])) if row["avg_price"] else None,
            "timestamp_start": row["timestamp_start"],
            "timestamp_end": row["timestamp_end"]
        }

    async def get_cumulative_delta(
        self,
        symbol: str,
        days: int = 7
    ) -> Dict:
        """
        Get CVD (Cumulative Volume Delta) over N days.
        
        Returns time series of cumulative delta.
        """
        query = """
            SELECT
                bucket,
                buy_volume,
                sell_volume,
                filtered_delta
            FROM delta_metrics_1h
            WHERE exchange = $1
              AND symbol = $2
              AND bucket >= NOW() - INTERVAL '1 day' * $3
            ORDER BY bucket ASC
        """
        
        async with db.acquire() as conn:
            rows = await conn.fetch(query, self.exchange, symbol, days)
            
        cvd = Decimal("0")
        series = []
        
        for row in rows:
            delta = Decimal(str(row["filtered_delta"] or 0))
            cvd += delta
            series.append({
                "timestamp": row["bucket"],
                "delta": delta,
                "cvd": cvd,
                "buy_volume": Decimal(str(row["buy_volume"] or 0)),
                "sell_volume": Decimal(str(row["sell_volume"] or 0))
            })
            
        return {
            "symbol": symbol,
            "days": days,
            "current_cvd": cvd,
            "series": series
        }

    async def detect_divergence(
        self,
        symbol: str,
        fractal_direction: str,  # "bullish" or "bearish"
        lookback_hours: int = 24
    ) -> bool:
        """
        Detect price/delta divergence.
        
        Logic:
        - Bullish fractal + negative delta = bearish divergence (sell signal)
        - Bearish fractal + positive delta = bullish divergence (buy signal)
        
        Returns:
            True if divergence detected
        """
        metrics = await self.get_hourly_delta(symbol, lookback_hours)
        delta = metrics["filtered_delta"]
        
        if fractal_direction == "bullish" and delta < 0:
            logger.info(
                f"🔴 Bearish divergence: {symbol} bullish fractal but delta={delta}"
            )
            return True
        elif fractal_direction == "bearish" and delta > 0:
            logger.info(
                f"🟢 Bullish divergence: {symbol} bearish fractal but delta={delta}"
            )
            return True
            
        return False

    async def get_orderbook_imbalance(
        self,
        symbol: str,
        minutes: int = 5
    ) -> Dict:
        """
        Get average orderbook imbalance over last N minutes.
        
        Returns:
            {
                "symbol": "BTCUSDT",
                "avg_imbalance": Decimal("0.15"),  # positive = bid pressure
                "max_imbalance": Decimal("0.25"),
                "min_imbalance": Decimal("0.05"),
                "sample_count": 60
            }
        """
        query = """
            SELECT
                AVG(imbalance) as avg_imbalance,
                MAX(imbalance) as max_imbalance,
                MIN(imbalance) as min_imbalance,
                COUNT(*) as sample_count
            FROM orderbook_snapshots
            WHERE exchange = $1
              AND symbol = $2
              AND timestamp >= NOW() - INTERVAL '1 minute' * $3
        """
        
        async with db.acquire() as conn:
            row = await conn.fetchrow(query, self.exchange, symbol, minutes)
            
        return {
            "symbol": symbol,
            "minutes": minutes,
            "avg_imbalance": Decimal(str(row["avg_imbalance"] or 0)),
            "max_imbalance": Decimal(str(row["max_imbalance"] or 0)),
            "min_imbalance": Decimal(str(row["min_imbalance"] or 0)),
            "sample_count": int(row["sample_count"] or 0)
        }

    async def get_oi_change(
        self,
        symbol: str,
        hours: int = 24
    ) -> Dict:
        """
        Get Open Interest change over last N hours.
        
        Returns:
            {
                "symbol": "BTCUSDT",
                "oi_current": Decimal("50000.123"),
                "oi_start": Decimal("48000.000"),
                "oi_change": Decimal("2000.123"),
                "oi_change_pct": Decimal("4.17")
            }
        """
        query = """
            SELECT
                timestamp,
                open_interest
            FROM open_interest
            WHERE exchange = $1
              AND symbol = $2
              AND timestamp >= NOW() - INTERVAL '1 hour' * $3
            ORDER BY timestamp ASC
        """
        
        async with db.acquire() as conn:
            rows = await conn.fetch(query, self.exchange, symbol, hours)
            
        if not rows or len(rows) < 2:
            return {
                "symbol": symbol,
                "hours": hours,
                "oi_current": None,
                "oi_start": None,
                "oi_change": None,
                "oi_change_pct": None
            }
            
        oi_start = Decimal(str(rows[0]["open_interest"]))
        oi_current = Decimal(str(rows[-1]["open_interest"]))
        oi_change = oi_current - oi_start
        oi_change_pct = (oi_change / oi_start * 100) if oi_start > 0 else Decimal("0")
        
        return {
            "symbol": symbol,
            "hours": hours,
            "oi_current": oi_current,
            "oi_start": oi_start,
            "oi_change": oi_change,
            "oi_change_pct": oi_change_pct
        }
