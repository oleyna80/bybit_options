"""Tests for Delta Analytics API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from decimal import Decimal
from datetime import datetime, timezone, date

from bybit_options.api.app import app

client = TestClient(app)


@pytest.fixture
def mock_analyzer():
    """Mock DeltaAnalyzer."""
    analyzer = AsyncMock()
    return analyzer


def test_get_delta_metrics(mock_analyzer):
    """Test GET /api/delta/metrics."""
    mock_analyzer.get_hourly_delta.return_value = {
        "symbol": "BTCUSDT",
        "period_hours": 1,
        "buy_volume": Decimal("100"),
        "sell_volume": Decimal("80"),
        "filtered_delta": Decimal("20"),
        "trade_count": 50,
        "avg_price": Decimal("93000"),
        "timestamp_start": datetime.now(timezone.utc),
        "timestamp_end": datetime.now(timezone.utc)
    }
    
    with patch('bybit_options.api.routes.delta.DeltaAnalyzer', return_value=mock_analyzer):
        response = client.get("/api/delta/metrics?symbol=BTCUSDT&hours=1")
    
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "BTCUSDT"
    assert data["filtered_delta"] == "20"
    assert data["trade_count"] == 50


def test_get_daily_summary(mock_analyzer):
    """Test GET /api/delta/summary."""
    mock_analyzer.get_daily_delta.return_value = {
        "symbol": "BTCUSDT",
        "date": date(2026, 1, 20),
        "buy_volume": Decimal("500"),
        "sell_volume": Decimal("400"),
        "filtered_delta": Decimal("100"),
        "trade_count": 200,
        "avg_price": Decimal("93500"),
        "timestamp_start": datetime.now(timezone.utc),
        "timestamp_end": datetime.now(timezone.utc)
    }
    
    with patch('bybit_options.api.routes.delta.DeltaAnalyzer', return_value=mock_analyzer):
        response = client.get("/api/delta/summary?symbol=BTCUSDT&date=2026-01-20")
    
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "BTCUSDT"
    assert data["filtered_delta"] == "100"


def test_get_cvd(mock_analyzer):
    """Test GET /api/delta/cvd."""
    mock_analyzer.get_cumulative_delta.return_value = {
        "symbol": "BTCUSDT",
        "days": 7,
        "current_cvd": Decimal("150"),
        "series": [
            {
                "timestamp": datetime.now(timezone.utc),
                "delta": Decimal("10"),
                "cvd": Decimal("10"),
                "buy_volume": Decimal("60"),
                "sell_volume": Decimal("50")
            },
            {
                "timestamp": datetime.now(timezone.utc),
                "delta": Decimal("20"),
                "cvd": Decimal("30"),
                "buy_volume": Decimal("70"),
                "sell_volume": Decimal("50")
            }
        ]
    }
    
    with patch('bybit_options.api.routes.delta.DeltaAnalyzer', return_value=mock_analyzer):
        response = client.get("/api/delta/cvd?symbol=BTCUSDT&days=7")
    
    assert response.status_code == 200
    data = response.json()
    assert data["current_cvd"] == "150"
    assert len(data["series"]) == 2
    assert data["series"][0]["cvd"] == "10"


def test_detect_divergence_bullish(mock_analyzer):
    """Test GET /api/delta/divergence with bullish fractal."""
    mock_analyzer.detect_divergence.return_value = True
    mock_analyzer.get_hourly_delta.return_value = {
        "symbol": "BTCUSDT",
        "period_hours": 24,
        "filtered_delta": Decimal("-50"),
        "buy_volume": Decimal("100"),
        "sell_volume": Decimal("150"),
        "trade_count": 50,
        "avg_price": Decimal("93000"),
        "timestamp_start": datetime.now(timezone.utc),
        "timestamp_end": datetime.now(timezone.utc)
    }
    
    with patch('bybit_options.api.routes.delta.DeltaAnalyzer', return_value=mock_analyzer):
        response = client.get(
            "/api/delta/divergence?symbol=BTCUSDT&fractal_direction=bullish&lookback_hours=24"
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["divergence_detected"] is True
    assert data["fractal_direction"] == "bullish"
    assert data["filtered_delta"] == "-50"


def test_detect_divergence_invalid_direction(mock_analyzer):
    """Test GET /api/delta/divergence with invalid direction."""
    with patch('bybit_options.api.routes.delta.DeltaAnalyzer', return_value=mock_analyzer):
        response = client.get(
            "/api/delta/divergence?symbol=BTCUSDT&fractal_direction=invalid&lookback_hours=24"
        )
    
    assert response.status_code == 400
    assert "must be 'bullish' or 'bearish'" in response.json()["detail"]


def test_get_orderbook_imbalance(mock_analyzer):
    """Test GET /api/delta/imbalance."""
    mock_analyzer.get_orderbook_imbalance.return_value = {
        "symbol": "BTCUSDT",
        "minutes": 5,
        "avg_imbalance": Decimal("0.15"),
        "max_imbalance": Decimal("0.25"),
        "min_imbalance": Decimal("0.05"),
        "sample_count": 60
    }
    
    with patch('bybit_options.api.routes.delta.DeltaAnalyzer', return_value=mock_analyzer):
        response = client.get("/api/delta/imbalance?symbol=BTCUSDT&minutes=5")
    
    assert response.status_code == 200
    data = response.json()
    assert data["avg_imbalance"] == "0.15"
    assert data["sample_count"] == 60


def test_get_oi_change(mock_analyzer):
    """Test GET /api/delta/oi-change."""
    mock_analyzer.get_oi_change.return_value = {
        "symbol": "BTCUSDT",
        "hours": 24,
        "oi_current": Decimal("50000"),
        "oi_start": Decimal("48000"),
        "oi_change": Decimal("2000"),
        "oi_change_pct": Decimal("4.17")
    }
    
    with patch('bybit_options.api.routes.delta.DeltaAnalyzer', return_value=mock_analyzer):
        response = client.get("/api/delta/oi-change?symbol=BTCUSDT&hours=24")
    
    assert response.status_code == 200
    data = response.json()
    assert data["oi_change"] == "2000"
    assert data["oi_change_pct"] == "4.17"


def test_get_oi_change_no_data(mock_analyzer):
    """Test GET /api/delta/oi-change with no data."""
    mock_analyzer.get_oi_change.return_value = {
        "symbol": "BTCUSDT",
        "hours": 24,
        "oi_current": None,
        "oi_start": None,
        "oi_change": None,
        "oi_change_pct": None
    }
    
    with patch('bybit_options.api.routes.delta.DeltaAnalyzer', return_value=mock_analyzer):
        response = client.get("/api/delta/oi-change?symbol=BTCUSDT&hours=24")
    
    assert response.status_code == 200
    data = response.json()
    assert data["oi_current"] is None
    assert data["oi_change"] is None
