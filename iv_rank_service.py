"""
IV Rank Service - Async data access layer for IV Rank feature
Reads from PostgreSQL (schema created by backfill_historical_data.py)
"""
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from database import AsyncSessionLocal
from data_models import PerpetualOHLCV, IVRankDaily


class IVRankService:
    """Service for fetching IV Rank and related data"""
    
    @staticmethod
    async def get_perpetual_ohlcv(
        symbol: str = "BTCUSDT",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 730
    ) -> List[PerpetualOHLCV]:
        """
        Fetch perpetual futures OHLCV data
        Ordered by Timestamp ASC (Chronological) for Charting
        """
        async with AsyncSessionLocal() as session:
            # Construct base query
            query_str = """
                SELECT timestamp, open, high, low, close, volume
                FROM perpetual_ohlcv
                WHERE symbol = :symbol
            """
            params = {"symbol": symbol, "limit": limit}

            if start_date:
                query_str += " AND timestamp >= :start_date"
                params["start_date"] = start_date
            
            if end_date:
                query_str += " AND timestamp <= :end_date"
                params["end_date"] = end_date

            # Optimization: Sort ASC in DB directly for charting
            query_str += " ORDER BY timestamp DESC LIMIT :limit"

            result = await session.execute(text(query_str), params)
            rows = result.fetchall()
            
            # Convert to Pydantic
            data = [
                PerpetualOHLCV(
                    timestamp=row[0],
                    open=float(row[1]),
                    high=float(row[2]),
                    low=float(row[3]),
                    close=float(row[4]),
                    volume=float(row[5])
                )
                for row in rows
            ]
            
            # Return chronological order (ASC) for Recharts
            return data[::-1] # Faster than list(reversed())
    
    @staticmethod
    async def get_iv_rank_history(
        base_coin: str = "BTC",
        days: int = 365
    ) -> List[IVRankDaily]:
        """
        Fetch IV Rank historical data
        """
        # Fix: Calculate cutoff date in Python to avoid SQL injection/syntax errors with INTERVAL
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        async with AsyncSessionLocal() as session:
            query = text("""
                SELECT 
                    timestamp,
                    iv_rank,
                    current_iv,
                    min_iv_30d,
                    max_iv_30d
                FROM iv_rank_daily
                WHERE underlying = :base_coin
                AND timestamp >= :cutoff_date
                ORDER BY timestamp ASC
            """)
            
            result = await session.execute(query, {
                "base_coin": base_coin,
                "cutoff_date": cutoff_date
            })
            
            rows = result.fetchall()
            
            return [
                IVRankDaily(
                    timestamp=row[0],
                    iv_rank=float(row[1]),
                    current_iv=float(row[2]),
                    min_iv_30d=float(row[3]),
                    max_iv_30d=float(row[4])
                )
                for row in rows
            ]


# Singleton instance
_iv_rank_service = IVRankService()


def get_iv_rank_service() -> IVRankService:
    """Get IV Rank service instance"""
    return _iv_rank_service
