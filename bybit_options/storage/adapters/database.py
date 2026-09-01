"""SQLAlchemy adapters for the repository interfaces.

Note: these adapters are intentionally thin; they bridge existing SQLAlchemy
models (e.g., `trade_logger.Trade`) to the new storage boundary.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping, Sequence

from sqlalchemy import bindparam, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bybit_options.storage.repositories import (
    OrderRepository,
    PortfolioSnapshotRepository,
    TradeRepository,
)

from trade_logger import Trade


class SQLAlchemyTradeRepository(TradeRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    async def existing_exec_ids(self, exec_ids: Sequence[str]) -> set[str]:
        if not exec_ids:
            return set()

        async with self._session_factory() as session:
            result = await session.execute(
                select(Trade.exec_id).where(Trade.exec_id.in_(list(exec_ids)))
            )
            return {row[0] for row in result.fetchall()}

    async def insert_trades(self, trades: Sequence[Mapping[str, Any]]) -> int:
        if not trades:
            return 0

        exec_ids = [str(t.get("exec_id")) for t in trades if t.get("exec_id")]
        existing = await self.existing_exec_ids(exec_ids)
        new_trades = [t for t in trades if t.get("exec_id") not in existing]

        if not new_trades:
            return 0

        async with self._session_factory() as session:
            for trade_data in new_trades:
                session.add(Trade(**dict(trade_data)))
            await session.commit()

        return len(new_trades)

    async def upsert_trades(
        self, trades: Sequence[Mapping[str, Any]]
    ) -> tuple[int, int]:
        if not trades:
            return 0, 0

        rows = [dict(item) for item in trades if item.get("exec_id")]
        if not rows:
            return 0, 0

        exec_ids = list({str(item["exec_id"]) for item in rows})
        existing = await self.existing_exec_ids(exec_ids)
        inserted = len(set(exec_ids) - existing)
        updated = len(existing)

        query = """
            INSERT INTO trades (
                exec_id,
                order_id,
                symbol,
                category,
                side,
                qty,
                price,
                exec_fee,
                exec_time,
                timestamp,
                size,
                exec_price,
                fee,
                role,
                raw_data
            ) VALUES (
                :exec_id,
                :order_id,
                :symbol,
                :category,
                :side,
                :qty,
                :price,
                :exec_fee,
                :exec_time,
                :timestamp,
                :size,
                :exec_price,
                :fee,
                :role,
                :raw_data
            )
            ON CONFLICT (exec_id) DO UPDATE SET
                exec_time = EXCLUDED.exec_time,
                qty = EXCLUDED.qty,
                price = EXCLUDED.price,
                exec_fee = EXCLUDED.exec_fee,
                category = EXCLUDED.category,
                raw_data = EXCLUDED.raw_data,
                order_id = EXCLUDED.order_id,
                symbol = EXCLUDED.symbol
        """

        async with self._session_factory() as session:
            await session.execute(text(query), rows)
            await session.commit()

        return inserted, updated

    async def get_last_exec_time(self) -> datetime | None:
        async with self._session_factory() as session:
            result = await session.execute(
                text("SELECT MAX(COALESCE(exec_time, timestamp)) FROM trades")
            )
            return result.scalar_one_or_none()


class SQLAlchemyOrderRepository(OrderRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    async def upsert_orders(
        self, orders: Sequence[Mapping[str, Any]]
    ) -> tuple[int, int]:
        if not orders:
            return 0, 0

        rows = [dict(item) for item in orders if item.get("order_id")]
        if not rows:
            return 0, 0

        order_ids = list({str(item["order_id"]) for item in rows})
        existing = await self._existing_order_ids(order_ids)
        inserted = len(set(order_ids) - existing)
        updated = len(existing)

        query = """
            INSERT INTO orders (
                order_id,
                symbol,
                category,
                side,
                order_type,
                qty,
                price,
                avg_price,
                cum_exec_qty,
                cum_exec_fee,
                status,
                created_time,
                updated_time,
                raw_data
            ) VALUES (
                :order_id,
                :symbol,
                :category,
                :side,
                :order_type,
                :qty,
                :price,
                :avg_price,
                :cum_exec_qty,
                :cum_exec_fee,
                :status,
                :created_time,
                :updated_time,
                :raw_data
            )
            ON CONFLICT (order_id) DO UPDATE SET
                symbol = EXCLUDED.symbol,
                category = EXCLUDED.category,
                side = EXCLUDED.side,
                order_type = EXCLUDED.order_type,
                qty = EXCLUDED.qty,
                price = EXCLUDED.price,
                avg_price = EXCLUDED.avg_price,
                cum_exec_qty = EXCLUDED.cum_exec_qty,
                cum_exec_fee = EXCLUDED.cum_exec_fee,
                status = EXCLUDED.status,
                updated_time = EXCLUDED.updated_time,
                raw_data = EXCLUDED.raw_data
        """

        async with self._session_factory() as session:
            await session.execute(text(query), rows)
            await session.commit()

        return inserted, updated

    async def get_last_created_time(self) -> datetime | None:
        async with self._session_factory() as session:
            result = await session.execute(
                text("SELECT MAX(created_time) FROM orders")
            )
            return result.scalar_one_or_none()

    async def _existing_order_ids(self, order_ids: Sequence[str]) -> set[str]:
        if not order_ids:
            return set()

        async with self._session_factory() as session:
            stmt = text("SELECT order_id FROM orders WHERE order_id IN :order_ids").bindparams(
                bindparam("order_ids", expanding=True)
            )
            result = await session.execute(stmt, {"order_ids": list(order_ids)})
            return {row[0] for row in result.fetchall()}


class SQLAlchemyPortfolioSnapshotRepository(PortfolioSnapshotRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    async def insert_snapshot(self, snapshot: Mapping[str, Any]) -> int:
        if not snapshot:
            return 0

        query = """
            INSERT INTO portfolio_snapshots (
                snapshot_time,
                equity,
                available_balance,
                margin_used,
                total_delta,
                total_gamma,
                total_vega,
                total_theta,
                btc_price,
                positions
            ) VALUES (
                :snapshot_time,
                :equity,
                :available_balance,
                :margin_used,
                :total_delta,
                :total_gamma,
                :total_vega,
                :total_theta,
                :btc_price,
                :positions
            )
        """

        async with self._session_factory() as session:
            await session.execute(text(query), dict(snapshot))
            await session.commit()

        return 1
