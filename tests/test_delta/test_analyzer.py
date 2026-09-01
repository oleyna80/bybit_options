"""Tests for DeltaAnalyzer."""

import pytest
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from bybit_options.services.delta.analyzer import DeltaAnalyzer


@pytest.fixture
def mock_db_connection():
    """Mock database connection."""
    conn = AsyncMock()
    return conn


@pytest.fixture
def mock_db_pool(mock_db_connection):
    """Mock database pool with proper async context manager."""
    
    class MockAcquire:
        def __init__(self, conn):
            self.conn = conn
            
        async def __aenter__(self):
            return self.conn
            
        async def __aexit__(self, *args):
            pass
    
    pool = MagicMock()
    pool.acquire = MagicMock(return_value=MockAcquire(mock_db_connection))
    return pool


@pytest.mark.asyncio
async def test_get_hourly_delta_with_data(mock_db_pool, mock_db_connection):
    """Test get_hourly_delta with valid data."""
    mock_db_connection.fetchrow.return_value = {
        "symbol": "BTCUSDT",
        "buy_volume": 150.5,
        "sell_volume": 120.3,
        "filtered_delta": 30.2,
        "trade_count": 45,
        "avg_price": 93000.50,
        "timestamp_start": datetime.now(timezone.utc),
        "timestamp_end": datetime.now(timezone.utc)
    }
    
    with patch('bybit_options.services.delta.analyzer.db', mock_db_pool):
        analyzer = DeltaAnalyzer()
        result = await analyzer.get_hourly_delta("BTCUSDT", hours=1)
    
    assert result["symbol"] == "BTCUSDT"
    assert result["period_hours"] == 1
    assert result["filtered_delta"] == Decimal("30.2")
    assert result["trade_count"] == 45
    assert result["buy_volume"] == Decimal("150.5")
    assert result["sell_volume"] == Decimal("120.3")


@pytest.mark.asyncio
async def test_get_hourly_delta_no_data(mock_db_pool, mock_db_connection):
    """Test get_hourly_delta with no data."""
    mock_db_connection.fetchrow.return_value = None
    
    with patch('bybit_options.services.delta.analyzer.db', mock_db_pool):
        analyzer = DeltaAnalyzer()
        result = await analyzer.get_hourly_delta("BTCUSDT", hours=1)
    
    assert result["symbol"] == "BTCUSDT"
    assert result["filtered_delta"] == Decimal("0")
    assert result["trade_count"] == 0


@pytest.mark.asyncio
async def test_get_daily_delta(mock_db_pool, mock_db_connection):
    """Test get_daily_delta."""
    test_date = datetime(2026, 1, 20, 12, 0, 0, tzinfo=timezone.utc)
    
    mock_db_connection.fetchrow.return_value = {
        "symbol": "BTCUSDT",
        "buy_volume": 500.0,
        "sell_volume": 400.0,
        "filtered_delta": 100.0,
        "trade_count": 120,
        "avg_price": 93500.0,
        "timestamp_start": test_date,
        "timestamp_end": test_date
    }
    
    with patch('bybit_options.services.delta.analyzer.db', mock_db_pool):
        analyzer = DeltaAnalyzer()
        result = await analyzer.get_daily_delta("BTCUSDT", date=test_date)
    
    assert result["symbol"] == "BTCUSDT"
    assert result["filtered_delta"] == Decimal("100.0")
    assert result["date"] == test_date.date()


@pytest.mark.asyncio
async def test_get_cumulative_delta(mock_db_pool, mock_db_connection):
    """Test get_cumulative_delta."""
    mock_rows = [
        {
            "bucket": datetime.now(timezone.utc),
            "buy_volume": 100,
            "sell_volume": 80,
            "filtered_delta": 20
        },
        {
            "bucket": datetime.now(timezone.utc),
            "buy_volume": 150,
            "sell_volume": 100,
            "filtered_delta": 50
        }
    ]
    
    mock_db_connection.fetch.return_value = mock_rows
    
    with patch('bybit_options.services.delta.analyzer.db', mock_db_pool):
        analyzer = DeltaAnalyzer()
        result = await analyzer.get_cumulative_delta("BTCUSDT", days=7)
    
    assert result["symbol"] == "BTCUSDT"
    assert result["days"] == 7
    assert result["current_cvd"] == Decimal("70")  # 20 + 50
    assert len(result["series"]) == 2
    assert result["series"][0]["cvd"] == Decimal("20")
    assert result["series"][1]["cvd"] == Decimal("70")


@pytest.mark.asyncio
async def test_detect_divergence_bearish(mock_db_pool, mock_db_connection):
    """Test bearish divergence detection (bullish fractal + negative delta)."""
    mock_db_connection.fetchrow.return_value = {
        "symbol": "BTCUSDT",
        "buy_volume": 50,
        "sell_volume": 100,
        "filtered_delta": -50,  # Negative delta
        "trade_count": 10,
        "avg_price": 93000,
        "timestamp_start": datetime.now(timezone.utc),
        "timestamp_end": datetime.now(timezone.utc)
    }
    
    with patch('bybit_options.services.delta.analyzer.db', mock_db_pool):
        analyzer = DeltaAnalyzer()
        divergence = await analyzer.detect_divergence("BTCUSDT", "bullish")
    
    assert divergence is True


@pytest.mark.asyncio
async def test_detect_divergence_bullish(mock_db_pool, mock_db_connection):
    """Test bullish divergence detection (bearish fractal + positive delta)."""
    mock_db_connection.fetchrow.return_value = {
        "symbol": "BTCUSDT",
        "buy_volume": 100,
        "sell_volume": 50,
        "filtered_delta": 50,  # Positive delta
        "trade_count": 10,
        "avg_price": 93000,
        "timestamp_start": datetime.now(timezone.utc),
        "timestamp_end": datetime.now(timezone.utc)
    }
    
    with patch('bybit_options.services.delta.analyzer.db', mock_db_pool):
        analyzer = DeltaAnalyzer()
        divergence = await analyzer.detect_divergence("BTCUSDT", "bearish")
    
    assert divergence is True


@pytest.mark.asyncio
async def test_detect_no_divergence(mock_db_pool, mock_db_connection):
    """Test no divergence (bullish fractal + positive delta)."""
    mock_db_connection.fetchrow.return_value = {
        "symbol": "BTCUSDT",
        "buy_volume": 100,
        "sell_volume": 50,
        "filtered_delta": 50,  # Positive delta
        "trade_count": 10,
        "avg_price": 93000,
        "timestamp_start": datetime.now(timezone.utc),
        "timestamp_end": datetime.now(timezone.utc)
    }
    
    with patch('bybit_options.services.delta.analyzer.db', mock_db_pool):
        analyzer = DeltaAnalyzer()
        divergence = await analyzer.detect_divergence("BTCUSDT", "bullish")
    
    assert divergence is False


@pytest.mark.asyncio
async def test_get_orderbook_imbalance(mock_db_pool, mock_db_connection):
    """Test get_orderbook_imbalance."""
    mock_db_connection.fetchrow.return_value = {
        "avg_imbalance": 0.15,
        "max_imbalance": 0.25,
        "min_imbalance": 0.05,
        "sample_count": 60
    }
    
    with patch('bybit_options.services.delta.analyzer.db', mock_db_pool):
        analyzer = DeltaAnalyzer()
        result = await analyzer.get_orderbook_imbalance("BTCUSDT", minutes=5)
    
    assert result["symbol"] == "BTCUSDT"
    assert result["minutes"] == 5
    assert result["avg_imbalance"] == Decimal("0.15")
    assert result["sample_count"] == 60


@pytest.mark.asyncio
async def test_get_oi_change(mock_db_pool, mock_db_connection):
    """Test get_oi_change."""
    mock_rows = [
        {"timestamp": datetime.now(timezone.utc), "open_interest": 48000.0},
        {"timestamp": datetime.now(timezone.utc), "open_interest": 50000.0}
    ]
    
    mock_db_connection.fetch.return_value = mock_rows
    
    with patch('bybit_options.services.delta.analyzer.db', mock_db_pool):
        analyzer = DeltaAnalyzer()
        result = await analyzer.get_oi_change("BTCUSDT", hours=24)
    
    assert result["symbol"] == "BTCUSDT"
    assert result["oi_start"] == Decimal("48000.0")
    assert result["oi_current"] == Decimal("50000.0")
    assert result["oi_change"] == Decimal("2000.0")
    # (2000 / 48000) * 100 = 4.166...
    assert abs(result["oi_change_pct"] - Decimal("4.166666666666666666666666667")) < Decimal("0.01")


@pytest.mark.asyncio
async def test_get_oi_change_no_data(mock_db_pool, mock_db_connection):
    """Test get_oi_change with insufficient data."""
    mock_db_connection.fetch.return_value = []
    
    with patch('bybit_options.services.delta.analyzer.db', mock_db_pool):
        analyzer = DeltaAnalyzer()
        result = await analyzer.get_oi_change("BTCUSDT", hours=24)
    
    assert result["oi_current"] is None
    assert result["oi_change"] is None
