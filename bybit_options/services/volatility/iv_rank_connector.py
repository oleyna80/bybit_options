"""
IV Rank Connector - Wrapper for existing iv_rank_service.
Provides clean async interface for Volatility Intelligence module.
"""

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime, timedelta

from loguru import logger


@dataclass
class IVRankData:
    """Current IV Rank context."""
    symbol: str
    iv_rank: float           # 0-100
    current_iv: float        # Current ATM IV (annualized, e.g., 0.65 = 65%)
    min_iv_30d: float
    max_iv_30d: float
    timestamp: datetime
    
    @property
    def regime(self) -> str:
        """Volatility regime based on IV Rank."""
        if self.iv_rank > 70:
            return "HIGH"
        elif self.iv_rank < 30:
            return "LOW"
        else:
            return "NORMAL"


class IVRankConnector:
    """
    Async connector to IV Rank data.
    Uses existing iv_rank_daily table from database.
    """
    
    async def get_current(self, symbol: str = "BTC") -> Optional[IVRankData]:
        """
        Get latest IV Rank for symbol.
        
        Args:
            symbol: Base coin (BTC, ETH)
        
        Returns:
            IVRankData or None if no data
        """
        try:
            from bybit_options.services.delta.database_config import db
            
            query = """
                SELECT 
                    timestamp,
                    iv_rank,
                    current_iv,
                    min_iv_30d,
                    max_iv_30d
                FROM iv_rank_daily
                WHERE underlying = $1
                ORDER BY timestamp DESC
                LIMIT 1
            """
            
            row = await db.fetchrow(query, symbol)
            
            if not row:
                logger.warning(f"No IV Rank data found for {symbol}")
                return None
            
            return IVRankData(
                symbol=symbol,
                iv_rank=float(row["iv_rank"]),
                current_iv=float(row["current_iv"]),
                min_iv_30d=float(row["min_iv_30d"]),
                max_iv_30d=float(row["max_iv_30d"]),
                timestamp=row["timestamp"]
            )
            
        except Exception as e:
            logger.error(f"Failed to get IV Rank for {symbol}: {e}")
            return None
    
    async def get_history(
        self, 
        symbol: str = "BTC", 
        days: int = 365
    ) -> List[IVRankData]:
        """
        Get IV Rank history for charting.
        
        Args:
            symbol: Base coin (BTC, ETH)
            days: Number of days to fetch
        
        Returns:
            List of IVRankData ordered by timestamp ASC
        """
        try:
            from bybit_options.services.delta.database_config import db
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            query = """
                SELECT 
                    timestamp,
                    iv_rank,
                    current_iv,
                    min_iv_30d,
                    max_iv_30d
                FROM iv_rank_daily
                WHERE underlying = $1
                AND timestamp >= $2
                ORDER BY timestamp ASC
            """
            
            rows = await db.fetch(query, symbol, cutoff_date)
            
            return [
                IVRankData(
                    symbol=symbol,
                    iv_rank=float(row["iv_rank"]),
                    current_iv=float(row["current_iv"]),
                    min_iv_30d=float(row["min_iv_30d"]),
                    max_iv_30d=float(row["max_iv_30d"]),
                    timestamp=row["timestamp"]
                )
                for row in rows
            ]
            
        except Exception as e:
            logger.error(f"Failed to get IV Rank history for {symbol}: {e}")
            return []
