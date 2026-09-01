"""Collector for Bybit large trades via REST polling."""

from __future__ import annotations

from collections import OrderedDict
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional

from loguru import logger

from bybit_options.models.delta_models import LargeTradeModel
from bybit_options.services.bybit_connector import BybitConnector
from bybit_options.services.delta.database_config import db
from bybit_options.services.delta.storage_service import StorageService

from .base_collector import BaseCollector


class LargeTradeCollector(BaseCollector):
    """Collector for large trades (whale trades) from Bybit REST API."""

    DEFAULT_THRESHOLDS = {
        "BTCUSDT": Decimal("5.0"),
        "ETHUSDT": Decimal("50.0"),
    }
    _MAX_SEEN_IDS = 2000

    def __init__(
        self,
        connector: BybitConnector,
        storage: StorageService,
        symbols: Optional[List[str]] = None,
        interval_seconds: int = 10,
        category: str = "linear",
    ) -> None:
        super().__init__(interval_seconds=interval_seconds)
        self.connector = connector
        self.storage = storage
        self.symbols = symbols or ["BTCUSDT", "ETHUSDT"]
        self.category = category
        self.thresholds = self.DEFAULT_THRESHOLDS.copy()
        self._seen_trade_ids: Dict[str, OrderedDict[str, None]] = {
            symbol: OrderedDict() for symbol in self.symbols
        }

    async def load_thresholds_from_db(self) -> None:
        """Load thresholds from delta_config table."""
        try:
            async with db.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT symbol, threshold_qty FROM delta_config WHERE active = true"
                )

            for row in rows:
                self.thresholds[row["symbol"]] = Decimal(str(row["threshold_qty"]))

            logger.info(f"📋 Loaded thresholds: {self.thresholds}")
        except Exception as exc:
            logger.warning(
                "⚠️ Could not load thresholds from DB, using defaults: "
                f"{exc}"
            )

    async def collect_once(self) -> int:
        """Execute one collection cycle."""
        collected_trades: List[LargeTradeModel] = []

        for symbol in self.symbols:
            try:
                raw_trades = await self.connector.get_recent_trades_raw(
                    symbol=symbol,
                    category=self.category,
                    limit=500,
                )

                if not raw_trades:
                    continue

                threshold = self.thresholds.get(
                    symbol,
                    self.DEFAULT_THRESHOLDS.get(symbol, Decimal("5"))
                )
                seen_ids = self._seen_trade_ids.setdefault(symbol, OrderedDict())

                for trade in raw_trades:
                    trade_id = trade.get("execId")
                    if not trade_id:
                        continue
                    if trade_id in seen_ids:
                        continue

                    quantity = Decimal(str(trade.get("size") or trade.get("qty") or 0))
                    if quantity < threshold:
                        continue

                    timestamp_ms = trade.get("time") or trade.get("execTime")
                    if not timestamp_ms:
                        continue

                    model = LargeTradeModel(
                        exchange="bybit",
                        market_type="perpetual",
                        symbol=symbol,
                        trade_id=trade_id,
                        price=Decimal(str(trade.get("price") or 0)),
                        quantity=quantity,
                        side=trade.get("side", "Buy"),
                        timestamp=datetime.fromtimestamp(
                            int(timestamp_ms) / 1000,
                            tz=timezone.utc,
                        ),
                    )
                    collected_trades.append(model)

                    seen_ids[trade_id] = None
                    if len(seen_ids) > self._MAX_SEEN_IDS:
                        seen_ids.popitem(last=False)
            except Exception as exc:
                self.stats["errors"] += 1
                logger.error(f"❌ Error fetching {symbol}: {exc}")

        if not collected_trades:
            return 0

        self.stats["items_collected"] += len(collected_trades)
        saved = await self.storage.save_large_trades(collected_trades)

        if saved > 0:
            logger.info(
                f"🐋 Collected {len(collected_trades)} whale trades, "
                f"saved {saved} new"
            )

        return saved
