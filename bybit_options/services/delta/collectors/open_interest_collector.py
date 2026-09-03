"""Collector for Bybit Open Interest via REST polling."""

from __future__ import annotations

from datetime import timezone
from decimal import Decimal
from typing import List, Optional

from loguru import logger

from bybit_options.models.delta_models import OpenInterestModel
from bybit_options.services.bybit_connector import BybitConnector
from bybit_options.services.delta.storage_service import StorageService

from .base_collector import BaseCollector


class OpenInterestCollector(BaseCollector):
    """
    Collector for Open Interest from Bybit REST API.

    Features:
    - Polls /v5/market/open-interest every N seconds (default 60)
    - Saves to TimescaleDB
    """

    DEFAULT_SYMBOLS = ["BTCUSDT", "ETHUSDT"]

    def __init__(
        self,
        connector: BybitConnector,
        storage: StorageService,
        symbols: Optional[List[str]] = None,
        interval_seconds: int = 60,
        category: str = "linear",
    ) -> None:
        super().__init__(interval_seconds=interval_seconds)
        self.connector = connector
        self.storage = storage
        self.symbols = symbols or self.DEFAULT_SYMBOLS
        self.category = category

    async def collect_once(self) -> int:
        """Execute one collection cycle."""
        items: List[OpenInterestModel] = []

        for symbol in self.symbols:
            try:
                # Get LATEST OI (limit=1)
                data = await self.connector.get_open_interest(
                    symbol=symbol,
                    category=self.category,
                    interval="5min",
                    limit=1,
                )

                # Bybit returns a LIST, we need the latest one
                if data and isinstance(data, list) and len(data) > 0:
                    latest = data[0]
                    self._ensure_utc(latest)
                    items.append(latest)

            except Exception as exc:
                self.stats["errors"] += 1
                logger.error(f"❌ Error fetching OI for {symbol}: {exc}")

        if not items:
            return 0

        self.stats["items_collected"] += len(items)
        saved = await self.storage.save_open_interest(items)

        if saved > 0:
            for item in items:
                logger.debug(f"📊 {item.symbol} OI: {item.open_interest}")

        return saved

    @staticmethod
    def _ensure_utc(item: OpenInterestModel) -> None:
        if item.timestamp.tzinfo is None:
            item.timestamp = item.timestamp.replace(tzinfo=timezone.utc)
        else:
            item.timestamp = item.timestamp.astimezone(timezone.utc)
