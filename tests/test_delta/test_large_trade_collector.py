import pytest
from decimal import Decimal
from unittest.mock import AsyncMock

from bybit_options.services.delta.collectors.large_trade_collector import (
    LargeTradeCollector,
)


@pytest.fixture
def mock_connector():
    connector = AsyncMock()
    connector.get_recent_trades_raw = AsyncMock()
    return connector


@pytest.fixture
def mock_storage():
    storage = AsyncMock()
    storage.save_large_trades.return_value = 1
    return storage


@pytest.mark.asyncio
async def test_filter_by_threshold(mock_connector, mock_storage):
    mock_connector.get_recent_trades_raw.return_value = [
        {
            "execId": "trade1",
            "symbol": "BTCUSDT",
            "price": "93000.00",
            "size": "6.5",
            "side": "Buy",
            "time": "1705702800000",
        },
        {
            "execId": "trade2",
            "symbol": "BTCUSDT",
            "price": "93000.00",
            "size": "0.5",
            "side": "Sell",
            "time": "1705702801000",
        },
    ]

    collector = LargeTradeCollector(
        connector=mock_connector,
        storage=mock_storage,
        symbols=["BTCUSDT"],
        interval_seconds=10,
    )

    saved = await collector.collect_once()

    assert saved == 1
    assert mock_storage.save_large_trades.called
    trades = mock_storage.save_large_trades.call_args[0][0]
    assert len(trades) == 1
    assert trades[0].quantity == Decimal("6.5")


@pytest.mark.asyncio
async def test_deduplication(mock_connector, mock_storage):
    mock_connector.get_recent_trades_raw.return_value = [
        {
            "execId": "trade1",
            "symbol": "BTCUSDT",
            "price": "93000.00",
            "size": "6.5",
            "side": "Buy",
            "time": "1705702800000",
        }
    ]

    collector = LargeTradeCollector(
        connector=mock_connector,
        storage=mock_storage,
        symbols=["BTCUSDT"],
    )

    await collector.collect_once()
    await collector.collect_once()

    assert mock_storage.save_large_trades.call_count == 1
