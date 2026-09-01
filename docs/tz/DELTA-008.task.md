# 🎯 Задача: DELTA-008 — API Endpoints

**Статус:** 🟡 READY FOR EXECUTION  
**Приоритет:** HIGH (для фронтенда)  
**Оценка времени:** 1-2 часа  
**Исполнитель:** Backend Developer  
**Зависит от:** DELTA-005 (DeltaAnalyzer) — должна быть выполнена ✅

---

## 📋 Контекст

`DeltaAnalyzer` готов и может предоставлять метрики. Теперь нужен REST API для фронтенда и внешних интеграций.

**Полное ТЗ проекта:** [delta_volume_analytics.tz.md](delta_volume_analytics.tz.md)  
**Предыдущая задача:** DELTA-006 (FractalEnricher) ✅

**Текущая задача:** Создать REST API endpoints для Delta Analytics.

---

## 🎯 Цель

Создать REST API endpoints для доступа к Delta метрикам из фронтенда.

**Ключевые характеристики:**
- FastAPI router `/api/delta/*`
- Pydantic response models
- Использует `DeltaAnalyzer`
- Кэширование опционально (для MVP не обязательно)

---

## ✅ Acceptance Criteria

- [ ] AC1: Endpoint `GET /api/delta/metrics` — time series метрик
- [ ] AC2: Endpoint `GET /api/delta/summary` — daily summary
- [ ] AC3: Endpoint `GET /api/delta/cvd` — cumulative volume delta
- [ ] AC4: Endpoint `GET /api/delta/divergence` — детекция расхождений
- [ ] AC5: Endpoint `GET /api/delta/imbalance` — orderbook imbalance
- [ ] AC6: Endpoint `GET /api/delta/oi-change` — OI change
- [ ] AC7: Pydantic response models
- [ ] AC8: Router подключён к FastAPI app
- [ ] AC9: Unit tests проходят

---

## 📁 Файлы

### Создать:

```
bybit_options/api/routes/delta.py
tests/test_api/test_delta_routes.py
```

### Изменить:

```
bybit_options/api/routes/__init__.py  # Добавить импорт
bybit_options/api/app.py              # Подключить router
```

---

## 📝 Спецификации

### 1. API Router

```python
# bybit_options/api/routes/delta.py

"""Delta Analytics API endpoints."""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field

from bybit_options.services.delta.analyzer import DeltaAnalyzer

router = APIRouter(prefix="/api/delta", tags=["Delta Analytics"])


# ============================================================================
# Response Models
# ============================================================================

class DeltaMetricsResponse(BaseModel):
    """Response model for delta metrics."""
    symbol: str
    period_hours: int
    buy_volume: Decimal
    sell_volume: Decimal
    filtered_delta: Decimal
    trade_count: int
    avg_price: Optional[Decimal]
    timestamp_start: Optional[datetime]
    timestamp_end: Optional[datetime]


class DailySummaryResponse(BaseModel):
    """Response model for daily summary."""
    symbol: str
    date: date
    buy_volume: Decimal
    sell_volume: Decimal
    filtered_delta: Decimal
    trade_count: int
    avg_price: Optional[Decimal]


class CVDPoint(BaseModel):
    """Single point in CVD time series."""
    timestamp: datetime
    delta: Decimal
    cvd: Decimal
    buy_volume: Decimal
    sell_volume: Decimal


class CVDResponse(BaseModel):
    """Response model for CVD."""
    symbol: str
    days: int
    current_cvd: Decimal
    series: List[CVDPoint]


class DivergenceResponse(BaseModel):
    """Response model for divergence detection."""
    symbol: str
    fractal_direction: str
    lookback_hours: int
    divergence_detected: bool
    filtered_delta: Decimal


class ImbalanceResponse(BaseModel):
    """Response model for orderbook imbalance."""
    symbol: str
    minutes: int
    avg_imbalance: Decimal
    max_imbalance: Decimal
    min_imbalance: Decimal
    sample_count: int


class OIChangeResponse(BaseModel):
    """Response model for OI change."""
    symbol: str
    hours: int
    oi_current: Optional[Decimal]
    oi_start: Optional[Decimal]
    oi_change: Optional[Decimal]
    oi_change_pct: Optional[Decimal]


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/metrics", response_model=DeltaMetricsResponse)
async def get_delta_metrics(
    symbol: str = Query(..., description="Trading pair (e.g., BTCUSDT)"),
    hours: int = Query(1, ge=1, le=168, description="Lookback period in hours")
):
    """
    Get delta metrics for the last N hours.
    
    Example: GET /api/delta/metrics?symbol=BTCUSDT&hours=24
    """
    analyzer = DeltaAnalyzer()
    
    try:
        result = await analyzer.get_hourly_delta(symbol, hours=hours)
        return DeltaMetricsResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary", response_model=DailySummaryResponse)
async def get_daily_summary(
    symbol: str = Query(..., description="Trading pair"),
    date: Optional[date] = Query(None, description="Date (default: today)")
):
    """
    Get daily summary for a specific date.
    
    Example: GET /api/delta/summary?symbol=BTCUSDT&date=2026-01-20
    """
    analyzer = DeltaAnalyzer()
    
    try:
        date_obj = datetime.combine(date, datetime.min.time()) if date else None
        result = await analyzer.get_daily_delta(symbol, date=date_obj)
        return DailySummaryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cvd", response_model=CVDResponse)
async def get_cvd(
    symbol: str = Query(..., description="Trading pair"),
    days: int = Query(7, ge=1, le=30, description="Lookback period in days")
):
    """
    Get Cumulative Volume Delta time series.
    
    Example: GET /api/delta/cvd?symbol=BTCUSDT&days=7
    """
    analyzer = DeltaAnalyzer()
    
    try:
        result = await analyzer.get_cumulative_delta(symbol, days=days)
        return CVDResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/divergence", response_model=DivergenceResponse)
async def detect_divergence(
    symbol: str = Query(..., description="Trading pair"),
    fractal_direction: str = Query(..., description="Fractal direction: bullish or bearish"),
    lookback_hours: int = Query(24, ge=1, le=168, description="Lookback period")
):
    """
    Detect price/delta divergence.
    
    Example: GET /api/delta/divergence?symbol=BTCUSDT&fractal_direction=bullish&lookback_hours=24
    """
    if fractal_direction not in ["bullish", "bearish"]:
        raise HTTPException(
            status_code=400,
            detail="fractal_direction must be 'bullish' or 'bearish'"
        )
    
    analyzer = DeltaAnalyzer()
    
    try:
        divergence = await analyzer.detect_divergence(
            symbol, fractal_direction, lookback_hours
        )
        
        # Get delta for response
        metrics = await analyzer.get_hourly_delta(symbol, lookback_hours)
        
        return DivergenceResponse(
            symbol=symbol,
            fractal_direction=fractal_direction,
            lookback_hours=lookback_hours,
            divergence_detected=divergence,
            filtered_delta=metrics["filtered_delta"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/imbalance", response_model=ImbalanceResponse)
async def get_orderbook_imbalance(
    symbol: str = Query(..., description="Trading pair"),
    minutes: int = Query(5, ge=1, le=60, description="Lookback period in minutes")
):
    """
    Get average orderbook imbalance.
    
    Example: GET /api/delta/imbalance?symbol=BTCUSDT&minutes=5
    """
    analyzer = DeltaAnalyzer()
    
    try:
        result = await analyzer.get_orderbook_imbalance(symbol, minutes=minutes)
        return ImbalanceResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/oi-change", response_model=OIChangeResponse)
async def get_oi_change(
    symbol: str = Query(..., description="Trading pair"),
    hours: int = Query(24, ge=1, le=168, description="Lookback period in hours")
):
    """
    Get Open Interest change.
    
    Example: GET /api/delta/oi-change?symbol=BTCUSDT&hours=24
    """
    analyzer = DeltaAnalyzer()
    
    try:
        result = await analyzer.get_oi_change(symbol, hours=hours)
        return OIChangeResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 2. Update routes/__init__.py

```python
# bybit_options/api/routes/__init__.py

from .portfolio import router as portfolio_router
from .options_board import router as options_board_router
from .trade_history import router as trade_history_router
from .delta import router as delta_router  # NEW

__all__ = [
    "portfolio_router",
    "options_board_router",
    "trade_history_router",
    "delta_router",  # NEW
]
```

### 3. Update app.py

```python
# bybit_options/api/app.py

# ... existing imports ...
from bybit_options.api.routes import (
    portfolio_router,
    options_board_router,
    trade_history_router,
    delta_router,  # NEW
)

# ... existing code ...

# Include routers
app.include_router(portfolio_router)
app.include_router(options_board_router)
app.include_router(trade_history_router)
app.include_router(delta_router)  # NEW
```

---

## 🧪 Testing

```python
# tests/test_api/test_delta_routes.py

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from decimal import Decimal
from datetime import datetime, timezone

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
            }
        ]
    }
    
    with patch('bybit_options.api.routes.delta.DeltaAnalyzer', return_value=mock_analyzer):
        response = client.get("/api/delta/cvd?symbol=BTCUSDT&days=7")
    
    assert response.status_code == 200
    data = response.json()
    assert data["current_cvd"] == "150"
    assert len(data["series"]) == 1
```

---

## 📋 Checklist перед сдачей

- [ ] Файл `delta.py` создан
- [ ] Все 6 endpoints реализованы
- [ ] Pydantic models определены
- [ ] Router подключён к app
- [ ] Unit tests проходят
- [ ] Можно протестировать через Swagger: `http://localhost:8000/docs`

---

## 🚀 Следующий шаг

После выполнения → **Frontend Integration** — подключить API к React dashboard
