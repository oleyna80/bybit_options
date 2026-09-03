"""Tests for FractalEnricher."""

import pytest
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from bybit_options.services.delta.enricher import FractalEnricher


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


@pytest.fixture
def sample_fractal():
    """Sample fractal record."""
    return {
        "id": 1,
        "timestamp": datetime.now(timezone.utc),
        "timeframe": "1h",
        "base_coin": "BTC",
        "type": "up",
        "price": Decimal("93000"),
        "symbol": "BTCUSDT",
        "candle_time": datetime.now(timezone.utc),
        "fractal_type": "up"
    }


@pytest.mark.asyncio
async def test_calculate_confidence_bullish_perfect(sample_fractal):
    """Test confidence calculation for perfect bullish signal."""
    enricher = FractalEnricher()
    
    delta_1h = {"filtered_delta": Decimal("15")}  # Positive + strong
    delta_4h = {"filtered_delta": Decimal("20")}
    delta_24h = {"filtered_delta": Decimal("30")}
    oi_change = {"oi_change": Decimal("1000")}  # Positive
    imbalance = {"avg_imbalance": Decimal("0.15")}  # Positive
    
    score = enricher._calculate_confidence(
        sample_fractal, delta_1h, delta_4h, delta_24h, oi_change, imbalance
    )
    
    # 30 (alignment) + 20 (OI) + 20 (imbalance) + 30 (strong) = 100
    assert score == 100


@pytest.mark.asyncio
async def test_calculate_confidence_bearish_perfect():
    """Test confidence calculation for perfect bearish signal."""
    enricher = FractalEnricher()
    
    fractal = {"type": "down", "fractal_type": "down"}
    delta_1h = {"filtered_delta": Decimal("-15")}  # Negative + strong
    delta_4h = {"filtered_delta": Decimal("-20")}
    delta_24h = {"filtered_delta": Decimal("-30")}
    oi_change = {"oi_change": Decimal("1000")}  # Positive
    imbalance = {"avg_imbalance": Decimal("-0.15")}  # Negative
    
    score = enricher._calculate_confidence(
        fractal, delta_1h, delta_4h, delta_24h, oi_change, imbalance
    )
    
    # 30 (alignment) + 20 (OI) + 20 (imbalance) + 30 (strong) = 100
    assert score == 100


@pytest.mark.asyncio
async def test_calculate_confidence_weak_signal(sample_fractal):
    """Test confidence calculation for weak signal."""
    enricher = FractalEnricher()
    
    delta_1h = {"filtered_delta": Decimal("2")}  # Positive but weak
    delta_4h = {"filtered_delta": Decimal("3")}
    delta_24h = {"filtered_delta": Decimal("5")}
    oi_change = {"oi_change": Decimal("-500")}  # Negative
    imbalance = {"avg_imbalance": Decimal("0.05")}  # Weak
    
    score = enricher._calculate_confidence(
        sample_fractal, delta_1h, delta_4h, delta_24h, oi_change, imbalance
    )
    
    # Only 30 (alignment) = 30
    assert score == 30


@pytest.mark.asyncio
async def test_calculate_confidence_divergence(sample_fractal):
    """Test confidence calculation for divergence (low score)."""
    enricher = FractalEnricher()
    
    # Bullish fractal but negative delta = divergence
    delta_1h = {"filtered_delta": Decimal("-5")}
    delta_4h = {"filtered_delta": Decimal("-10")}
    delta_24h = {"filtered_delta": Decimal("-15")}
    oi_change = {"oi_change": Decimal("100")}
    imbalance = {"avg_imbalance": Decimal("-0.1")}
    
    score = enricher._calculate_confidence(
        sample_fractal, delta_1h, delta_4h, delta_24h, oi_change, imbalance
    )
    
    # Only 20 (OI) = 20
    assert score == 20


@pytest.mark.asyncio
async def test_find_unenriched_fractals(mock_db_pool, mock_db_connection):
    """Test finding unenriched fractals."""
    mock_db_connection.fetch.return_value = [
        {
            "id": 1,
            "timestamp": datetime.now(timezone.utc),
            "timeframe": "1h",
            "base_coin": "BTC",
            "type": "up",
            "price": Decimal("93000"),
            "symbol": "BTCUSDT",
            "candle_time": datetime.now(timezone.utc),
            "fractal_type": "up"
        }
    ]
    
    with patch('bybit_options.services.delta.enricher.db', mock_db_pool):
        enricher = FractalEnricher()
        fractals = await enricher.find_unenriched_fractals(limit=50)
    
    assert len(fractals) == 1
    assert fractals[0]["id"] == 1
    assert fractals[0]["symbol"] == "BTCUSDT"


@pytest.mark.asyncio
async def test_update_fractal(mock_db_pool, mock_db_connection):
    """Test updating fractal with enrichment data."""
    enrichment = {
        "delta_1h": Decimal("10"),
        "delta_4h": Decimal("20"),
        "delta_24h": Decimal("30"),
        "oi_delta_24h": Decimal("1000"),
        "orderbook_imbalance": Decimal("0.15"),
        "confidence_score": 80,
        "enriched_at": datetime.now(timezone.utc)
    }
    
    with patch('bybit_options.services.delta.enricher.db', mock_db_pool):
        enricher = FractalEnricher()
        success = await enricher.update_fractal(1, enrichment)
    
    assert success is True
    assert mock_db_connection.execute.called
