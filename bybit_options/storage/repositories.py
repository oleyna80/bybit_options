"""Storage boundary interfaces (repository contracts).

These Protocols define how the domain/services talk to persistence without
depending on a specific database/ORM implementation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping, Protocol, Sequence


class TradeRepository(Protocol):
    async def existing_exec_ids(self, exec_ids: Sequence[str]) -> set[str]:
        """Return subset of exec_ids already present in storage."""

    async def insert_trades(self, trades: Sequence[Mapping[str, Any]]) -> int:
        """Insert trades into storage. Returns inserted count."""

    async def upsert_trades(
        self, trades: Sequence[Mapping[str, Any]]
    ) -> tuple[int, int]:
        """Upsert trades into storage. Returns (inserted, updated)."""

    async def get_last_exec_time(self) -> datetime | None:
        """Return latest exec_time (fallback to timestamp) if available."""


class OrderRepository(Protocol):
    async def upsert_orders(
        self, orders: Sequence[Mapping[str, Any]]
    ) -> tuple[int, int]:
        """Upsert orders into storage. Returns (inserted, updated)."""

    async def get_last_created_time(self) -> datetime | None:
        """Return latest created_time for stored orders."""


class PortfolioSnapshotRepository(Protocol):
    async def insert_snapshot(self, snapshot: Mapping[str, Any]) -> int:
        """Insert portfolio snapshot row. Returns inserted count."""
