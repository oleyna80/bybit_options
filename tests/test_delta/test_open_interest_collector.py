import pytest
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock

from bybit_options.services.delta.collectors.open_interest_collector import (
    OpenInterestCollector,
)
from bybit_options.models.delta_models import OpenInterestModel


@pytest.fixture
def mock_connector():
    connector = AsyncMock()
    connector.get_open_interest = AsyncMock()
    return connector


@pytest.fixture
def mock_storage():
    storage = AsyncMock()
    storage.save_open_interest.return_value = 1
    return storage


def _sample_oi_model():
    return OpenInterestModel(
        exchange="bybit",
        symbol="BTCUSDT",
        open_interest=Decimal("50000.123"),
        timestamp=datetime.now(timezone.utc),
    )


@pytest.mark.asyncio
async def test_collect_once_saves_oi(mock_connector, mock_storage):
    # Mock connector returns a list of OI models
    mock_connector.get_open_interest.return_value = [_sample_oi_model()]

    collector = OpenInterestCollector(
        connector=mock_connector,
        storage=mock_storage,
        symbols=["BTCUSDT"],
        interval_seconds=60,
    )

    saved = await collector.collect_once()

    assert saved == 1
    assert mock_storage.save_open_interest.called
    items = mock_storage.save_open_interest.call_args[0][0]
    assert len(items) == 1
    assert items[0].symbol == "BTCUSDT"
    assert items[0].open_interest == Decimal("50000.123")


@pytest.mark.asyncio
async def test_handles_api_error(mock_connector, mock_storage):
    mock_connector.get_open_interest.side_effect = Exception("API Error")

    collector = OpenInterestCollector(
        connector=mock_connector,
        storage=mock_storage,
        symbols=["BTCUSDT"],
    )

    saved = await collector.collect_once()

    assert saved == 0
    assert collector.stats["errors"] == 1
