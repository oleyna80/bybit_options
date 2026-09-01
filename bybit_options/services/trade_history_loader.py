"""Trade history loader for backfill and incremental sync."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Mapping, Sequence

from bybit_options.models.trade_history import ExecutionRecord, OrderRecord
from bybit_options.services.bybit_connector import BybitConnector
from bybit_options.storage.repositories import OrderRepository, TradeRepository

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LoaderWindow:
    start: datetime
    end: datetime


class TradeHistoryLoader:
    """Backfill and sync trades/orders history with cursor pagination."""

    def __init__(
        self,
        connector: BybitConnector,
        trade_repository: TradeRepository,
        order_repository: OrderRepository,
        *,
        window_days: int = 6,
    ) -> None:
        self.connector = connector
        self.trade_repository = trade_repository
        self.order_repository = order_repository
        self.window_days = min(window_days, 7)

    async def backfill(self, days: int = 180, category: str = "option") -> None:
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=days)
        windows = self._build_windows(start, now, window_days=self.window_days)

        logger.info(
            "Trade history backfill: days=%s windows=%s category=%s",
            days,
            len(windows),
            category,
        )

        for idx, window in enumerate(windows, start=1):
            logger.info(
                "Backfill window %s/%s: %s -> %s",
                idx,
                len(windows),
                window.start.isoformat(),
                window.end.isoformat(),
            )
            executions = await self._fetch_executions(window, category=category)
            orders = await self._fetch_orders(window, category=category)
            await self._persist_window(executions, orders, category=category)

    async def sync(self, category: str = "option") -> None:
        now = datetime.now(timezone.utc)
        last_exec = await self.trade_repository.get_last_exec_time()
        if last_exec is None:
            start = now - timedelta(days=7)
        else:
            start = max(last_exec, now - timedelta(days=7))
        end = now

        window = LoaderWindow(start=start, end=end)
        logger.info(
            "Trade history sync: start=%s end=%s category=%s",
            window.start.isoformat(),
            window.end.isoformat(),
            category,
        )

        executions = await self._fetch_executions(window, category=category)
        orders = await self._fetch_orders(window, category=category)
        await self._persist_window(executions, orders, category=category)

    async def _persist_window(
        self,
        executions: Sequence[ExecutionRecord],
        orders: Sequence[OrderRecord],
        *,
        category: str,
    ) -> None:
        trade_rows = [
            self._execution_to_row(record, category=category) for record in executions
        ]
        order_rows = [self._order_to_row(record, category=category) for record in orders]

        inserted_trades, updated_trades = await self.trade_repository.upsert_trades(
            trade_rows
        )
        inserted_orders, updated_orders = await self.order_repository.upsert_orders(
            order_rows
        )

        logger.info(
            "Persisted window: trades=%s (+%s/~%s) orders=%s (+%s/~%s)",
            len(trade_rows),
            inserted_trades,
            updated_trades,
            len(order_rows),
            inserted_orders,
            updated_orders,
        )

    async def _fetch_executions(
        self, window: LoaderWindow, *, category: str
    ) -> list[ExecutionRecord]:
        cursor: str | None = None
        all_records: list[ExecutionRecord] = []
        page = 0

        while True:
            page += 1
            response = await self.connector.get_execution_history(
                category=category,
                start_time=self._to_ms(window.start),
                end_time=self._to_ms(window.end),
                limit=50,
                cursor=cursor,
            )
            records = response.result.records
            all_records.extend(records)

            logger.info(
                "Execution page %s: fetched=%s total=%s cursor=%s",
                page,
                len(records),
                len(all_records),
                response.result.next_page_cursor,
            )

            cursor = response.result.next_page_cursor
            if not cursor:
                break

        return all_records

    async def _fetch_orders(
        self, window: LoaderWindow, *, category: str
    ) -> list[OrderRecord]:
        cursor: str | None = None
        all_records: list[OrderRecord] = []
        page = 0

        while True:
            page += 1
            response = await self.connector.get_order_history(
                category=category,
                start_time=self._to_ms(window.start),
                end_time=self._to_ms(window.end),
                limit=20,
                cursor=cursor,
            )
            records = response.result.records
            all_records.extend(records)

            logger.info(
                "Order page %s: fetched=%s total=%s cursor=%s",
                page,
                len(records),
                len(all_records),
                response.result.next_page_cursor,
            )

            cursor = response.result.next_page_cursor
            if not cursor:
                break

        return all_records

    @staticmethod
    def _build_windows(
        start: datetime, end: datetime, *, window_days: int
    ) -> list[LoaderWindow]:
        if start >= end:
            return []

        days = max(1, min(window_days, 7))
        step = timedelta(days=days)
        windows: list[LoaderWindow] = []
        cursor = start
        while cursor < end:
            next_end = min(cursor + step, end)
            windows.append(LoaderWindow(start=cursor, end=next_end))
            cursor = next_end
        return windows

    @staticmethod
    def _to_ms(value: datetime) -> int:
        return int(value.timestamp() * 1000)

    @staticmethod
    def _execution_to_row(
        record: ExecutionRecord, *, category: str
    ) -> Mapping[str, object]:
        return {
            "exec_id": record.exec_id,
            "order_id": record.order_id,
            "symbol": record.symbol,
            "category": category,
            "side": record.side or "Buy",
            "qty": record.exec_qty,
            "price": record.exec_price,
            "exec_fee": record.exec_fee,
            "exec_time": record.exec_time,
            "timestamp": record.exec_time,
            "size": record.exec_qty,
            "exec_price": record.exec_price,
            "fee": record.exec_fee or 0,
            "role": "Maker",
            "raw_data": record.dict(by_alias=True),
        }

    @staticmethod
    def _order_to_row(
        record: OrderRecord, *, category: str
    ) -> Mapping[str, object]:
        return {
            "order_id": record.order_id,
            "symbol": record.symbol,
            "category": category,
            "side": record.side or "Buy",
            "order_type": record.order_type,
            "qty": record.qty,
            "price": record.price,
            "avg_price": record.avg_price,
            "cum_exec_qty": record.cum_exec_qty,
            "cum_exec_fee": record.cum_exec_fee,
            "status": record.order_status or "UNKNOWN",
            "created_time": record.created_time,
            "updated_time": record.updated_time,
            "raw_data": record.dict(by_alias=True),
        }
