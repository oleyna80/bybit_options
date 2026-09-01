"""Collector for Bybit orderbook snapshots via REST polling."""

from __future__ import annotations

from datetime import timezone
from decimal import Decimal
from typing import List, Optional

from loguru import logger

from bybit_options.models.delta_models import OrderbookSnapshotModel
from bybit_options.services.bybit_connector import BybitConnector
from bybit_options.services.delta.storage_service import StorageService

from .base_collector import BaseCollector


class OrderbookCollector(BaseCollector):
    """Collector for orderbook snapshots from Bybit REST API."""

    DEFAULT_SYMBOLS = ["BTCUSDT", "ETHUSDT"]

    def __init__(
        self,
        connector: BybitConnector,
        storage: StorageService,
        symbols: Optional[List[str]] = None,
        interval_seconds: int = 5,
        depth: int = 20,
        category: str = "linear",
    ) -> None:
        super().__init__(interval_seconds=interval_seconds)
        self.connector = connector
        self.storage = storage
        self.symbols = symbols or self.DEFAULT_SYMBOLS
        self.depth = depth
        self.category = category

    async def collect_once(self) -> int:
        """Execute one collection cycle."""
        snapshots: List[OrderbookSnapshotModel] = []

        for symbol in self.symbols:
            try:
                snapshot = await self.connector.get_orderbook_snapshot(
                    symbol=symbol,
                    category=self.category,
                    depth=self.depth,
                )
                self._ensure_utc(snapshot)
                snapshots.append(snapshot)
            except Exception as exc:
                self.stats["errors"] += 1
                logger.error(f"❌ Error fetching orderbook {symbol}: {exc}")

        if not snapshots:
            return 0

        self.stats["items_collected"] += len(snapshots)
        saved = await self.storage.save_orderbook_snapshots(snapshots)

        if saved > 0:
            for snapshot in snapshots:
                imbalance = snapshot.imbalance or Decimal("0")
                if imbalance > 0:
                    direction = "📈 BID"
                elif imbalance < 0:
                    direction = "📉 ASK"
                else:
                    direction = "➡️ FLAT"
                logger.debug(
                    f"📊 {snapshot.symbol} orderbook: {direction} pressure "
                    f"{abs(float(imbalance) * 100):.1f}%"
                )

        return saved

    @staticmethod
    def _ensure_utc(snapshot: OrderbookSnapshotModel) -> None:
        if snapshot.timestamp.tzinfo is None:
            snapshot.timestamp = snapshot.timestamp.replace(tzinfo=timezone.utc)
        else:
            snapshot.timestamp = snapshot.timestamp.astimezone(timezone.utc)
