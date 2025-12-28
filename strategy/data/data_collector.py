"""
Hourly data collection pipeline for Sigma-Fractal.
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict

from sqlalchemy import text

from database import AsyncSessionLocal
from strategy.config import get_strategy_config
from strategy.data.deribit_client import DeribitClient

logger = logging.getLogger(__name__)


class DataCollector:
    """Collects DVOL snapshots and computes IV Rank."""

    def __init__(self, client: Optional[DeribitClient] = None):
        self.client = client or DeribitClient()
        self.config = get_strategy_config()

    async def collect_dvol_snapshot(self) -> Dict[str, Optional[float]]:
        """Fetch DVOL, compute IVR over 30 days, and store to DB."""
        snapshot = await self.client.get_volatility_index("BTC")
        timestamp = datetime.now(timezone.utc)
        dvol_value = float(snapshot["dvol"])

        ivr = await self._calculate_ivr(dvol_value, timestamp)
        await self._store_snapshot(timestamp, dvol_value, ivr)

        return {
            "dvol": dvol_value,
            "ivr": ivr,
            "timestamp": timestamp.isoformat(),
        }

    async def _calculate_ivr(self, current_dvol: float, now: datetime) -> Optional[float]:
        window_start = now - timedelta(days=30)

        query = text(
            """
            SELECT MIN(dvol) AS min_dvol, MAX(dvol) AS max_dvol
            FROM dvol_history
            WHERE timestamp >= :start_time
            """
        )

        async with AsyncSessionLocal() as session:
            result = await session.execute(query, {"start_time": window_start})
            row = result.fetchone()

        if not row or row[0] is None or row[1] is None:
            return None

        min_dvol, max_dvol = float(row[0]), float(row[1])
        if max_dvol - min_dvol <= 0:
            return None

        return ((current_dvol - min_dvol) / (max_dvol - min_dvol)) * 100

    async def _store_snapshot(self, timestamp: datetime, dvol: float, ivr: Optional[float]):
        insert_query = text(
            """
            INSERT INTO dvol_history (timestamp, dvol, ivr)
            VALUES (:timestamp, :dvol, :ivr)
            ON CONFLICT (timestamp) DO UPDATE SET
                dvol = EXCLUDED.dvol,
                ivr = EXCLUDED.ivr
            """
        )

        async with AsyncSessionLocal() as session:
            await session.execute(
                insert_query,
                {"timestamp": timestamp, "dvol": dvol, "ivr": ivr},
            )
            await session.commit()

    async def run_collection_loop(self):
        interval = self.config.collection_interval_minutes * 60
        logger.info("Starting DVOL collection loop every %s seconds", interval)

        while True:
            try:
                result = await self.collect_dvol_snapshot()
                logger.info("DVOL snapshot saved: %s", result)
            except Exception as exc:
                logger.error("DVOL collection failed: %s", exc, exc_info=True)

            await asyncio.sleep(interval)


async def main():
    logging.basicConfig(level=logging.INFO)
    collector = DataCollector()
    async with collector.client:
        await collector.run_collection_loop()


if __name__ == "__main__":
    asyncio.run(main())
