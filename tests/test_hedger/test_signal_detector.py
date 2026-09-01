"""
Unit tests for SignalDetector.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from bybit_options.services.hedger.signal_detector import SignalDetector
from bybit_options.services.hedger.models import FractalSignal

@pytest.fixture
def mock_db_pool():
    pool = MagicMock()
    pool.fetchval = AsyncMock()
    pool.fetch = AsyncMock()
    return pool

@pytest.fixture
def detector(mock_db_pool):
    return SignalDetector(mock_db_pool)

@pytest.mark.asyncio
async def test_detect_no_price(detector):
    """Test when no price data is available."""
    detector.db.fetchval.return_value = None
    result = await detector.detect()
    assert result is None

@pytest.mark.asyncio
async def test_detect_h4_long_breakout(detector):
    """Test detection of H4 Long breakout."""
    # Setup price
    detector.db.fetchval.return_value = 100000.0  # Current price
    
    # Setup H4 fractals: High at 99000, Low at 90000
    # H4 check is first
    detector.db.fetch.side_effect = [
        # First call (H4)
        [
            {"price": 99000.0, "type": "HIGH"},
            {"price": 90000.0, "type": "LOW"}
        ]
    ]
    
    result = await detector.detect()
    
    assert result is not None
    assert result.timeframe == "H4"
    assert result.direction == "LONG"
    assert result.fractal_price == 99000.0
    assert result.current_price == 100000.0
    assert result.is_bullish is True

@pytest.mark.asyncio
async def test_detect_h1_short_breakout_no_h4(detector):
    """Test detection of H1 Short breakout when H4 is stable."""
    # Setup price
    detector.db.fetchval.return_value = 89000.0  # Current price
    
    # Setup: 
    # H4 fractals: High 105000, Low 80000 (Current 89000 is inside range, no breakout)
    # H1 fractals: High 95000, Low 90000 (Current 89000 < 90000 -> Breakout Short)
    
    detector.db.fetch.side_effect = [
        # H4 response
        [
            {"price": 105000.0, "type": "HIGH"},
            {"price": 80000.0, "type": "LOW"}
        ],
        # H1 response
        [
            {"price": 95000.0, "type": "HIGH"},
            {"price": 90000.0, "type": "LOW"}
        ]
    ]
    
    result = await detector.detect()
    
    assert result is not None
    assert result.timeframe == "H1"
    assert result.direction == "SHORT"
    assert result.fractal_price == 90000.0
    assert result.is_bearish is True

@pytest.mark.asyncio
async def test_detect_priority_h4_over_h1(detector):
    """Test that H4 signal takes precedence over H1."""
    # Setup price
    detector.db.fetchval.return_value = 110000.0
    
    # H4 Breakout High (100k)
    # H1 Breakout High (105k)
    # Should return H4 and STOP there
    
    detector.db.fetch.side_effect = [
        # H4
        [{"price": 100000.0, "type": "HIGH"}]
    ]
    
    result = await detector.detect()
    
    assert result is not None
    assert result.timeframe == "H4"
    
    # Ensure H1 was not fetched (fetch called only once)
    assert detector.db.fetch.call_count == 1
    args = detector.db.fetch.call_args[0]
    assert args[1] == "H4"

@pytest.mark.asyncio
async def test_no_breakout(detector):
    """Test when price is inside fractals."""
    detector.db.fetchval.return_value = 95000.0
    
    # Both H4 and H1 ranges cover 95000
    detector.db.fetch.side_effect = [
        # H4: 90k - 100k
        [{"price": 100000.0, "type": "HIGH"}, {"price": 90000.0, "type": "LOW"}],
        # H1: 94k - 96k
        [{"price": 96000.0, "type": "HIGH"}, {"price": 94000.0, "type": "LOW"}]
    ]
    
    result = await detector.detect()
    assert result is None
