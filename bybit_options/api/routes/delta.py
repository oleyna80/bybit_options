"""Delta Analytics API endpoints."""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from datetime import datetime, date, timezone
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
    date_param: Optional[date] = Query(None, alias="date", description="Date (default: today)")
):
    """
    Get daily summary for a specific date.
    
    Example: GET /api/delta/summary?symbol=BTCUSDT&date=2026-01-20
    """
    analyzer = DeltaAnalyzer()
    
    try:
        date_obj = datetime.combine(date_param, datetime.min.time(), tzinfo=timezone.utc) if date_param else None
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
