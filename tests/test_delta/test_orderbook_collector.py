import pytest
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock

from bybit_options.services.delta.collectors.orderbook_collector import (
    OrderbookCollector,
)


@pytest.fixture
def mock_connector():
    connector = AsyncMock()
    connector.get_orderbook_snapshot = AsyncMock()
    return connector


@pytest.fixture
def mock_storage():
    storage = AsyncMock()
    storage.save_orderbook_snapshots.return_value = 1
    return storage


def _sample_snapshot():
    class Snapshot:
        def __init__(self):
            self.exchange = "bybit"
            self.symbol = "BTCUSDT"
            self.timestamp = datetime(2026, 1, 20, 12, 0, 0)
            self.imbalance = Decimal("0.1764705")

    return Snapshot()


@pytest.mark.asyncio
async def test_collect_once_saves_snapshot(mock_connector, mock_storage):
    mock_connector.get_orderbook_snapshot.return_value = _sample_snapshot()

    collector = OrderbookCollector(
        connector=mock_connector,
        storage=mock_storage,
        symbols=["BTCUSDT"],
        interval_seconds=5,
    )

    saved = await collector.collect_once()

    assert saved == 1
    assert mock_storage.save_orderbook_snapshots.called
    snapshots = mock_storage.save_orderbook_snapshots.call_args[0][0]
    assert len(snapshots) == 1
    assert snapshots[0].symbol == "BTCUSDT"
    assert snapshots[0].timestamp.tzinfo == timezone.utc


@pytest.mark.asyncio
async def test_handles_api_error(mock_connector, mock_storage):
    mock_connector.get_orderbook_snapshot.side_effect = Exception("boom")

    collector = OrderbookCollector(
        connector=mock_connector,
        storage=mock_storage,
        symbols=["BTCUSDT"],
    )

    saved = await collector.collect_once()

    assert saved == 0
    assert collector.stats["errors"] == 1
