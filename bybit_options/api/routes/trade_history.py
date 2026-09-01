"""Trade history API routes (HIST-006)."""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from bybit_options.models import PortfolioRiskModel
from bybit_options.orchestration.analysis_orchestrator import AnalysisOrchestrator
from database import get_db

router = APIRouter(prefix="/api", tags=["History"])


class _BaseResponseModel(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
        json_encoders={
            Decimal: lambda v: str(v),
            datetime: lambda v: v.isoformat(),
        },
    )


class TradeItem(_BaseResponseModel):
    exec_id: str
    order_id: Optional[str] = None
    symbol: str
    category: Optional[str] = None
    side: Optional[str] = None
    qty: Optional[Decimal] = None
    price: Optional[Decimal] = None
    exec_fee: Optional[Decimal] = None
    exec_time: Optional[datetime] = None
    timestamp: Optional[datetime] = None
    size: Optional[Decimal] = None
    exec_price: Optional[Decimal] = None
    fee: Optional[Decimal] = None
    role: Optional[str] = None
    raw_data: Optional[dict[str, Any]] = None


class OrderItem(_BaseResponseModel):
    order_id: str
    symbol: str
    category: Optional[str] = None
    side: Optional[str] = None
    order_type: Optional[str] = None
    qty: Optional[Decimal] = None
    price: Optional[Decimal] = None
    avg_price: Optional[Decimal] = None
    cum_exec_qty: Optional[Decimal] = None
    cum_exec_fee: Optional[Decimal] = None
    status: Optional[str] = None
    created_time: Optional[datetime] = None
    updated_time: Optional[datetime] = None
    raw_data: Optional[dict[str, Any]] = None


class PortfolioSnapshotItem(_BaseResponseModel):
    id: int
    snapshot_time: datetime
    equity: Optional[Decimal] = None
    available_balance: Optional[Decimal] = None
    margin_used: Optional[Decimal] = None
    total_delta: Optional[Decimal] = None
    total_gamma: Optional[Decimal] = None
    total_vega: Optional[Decimal] = None
    total_theta: Optional[Decimal] = None
    btc_price: Optional[Decimal] = None
    positions: Optional[Any] = None


class TradeListResponse(_BaseResponseModel):
    items: list[TradeItem]
    limit: int
    next_cursor: Optional[str] = None


class OrderListResponse(_BaseResponseModel):
    items: list[OrderItem]
    limit: int
    next_cursor: Optional[str] = None


class PortfolioSnapshotListResponse(_BaseResponseModel):
    items: list[PortfolioSnapshotItem]
    limit: int
    next_cursor: Optional[str] = None


@dataclass(frozen=True)
class CursorValue:
    time: datetime
    id: str


def _encode_cursor(cursor: CursorValue) -> str:
    payload = {
        "time": cursor.time.isoformat(),
        "id": cursor.id,
    }
    raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("utf-8")


def _decode_cursor(cursor: str) -> CursorValue:
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        raw = base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8")
        payload = json.loads(raw)
        time_value = payload["time"]
        cursor_id = str(payload["id"])
    except Exception as exc:  # noqa: BLE001 - map to 400
        raise ValueError("Invalid cursor") from exc

    if isinstance(time_value, str) and time_value.endswith("Z"):
        time_value = time_value[:-1] + "+00:00"

    try:
        parsed_time = datetime.fromisoformat(time_value)
    except Exception as exc:  # noqa: BLE001 - map to 400
        raise ValueError("Invalid cursor time") from exc

    if parsed_time.tzinfo is None:
        parsed_time = parsed_time.replace(tzinfo=timezone.utc)

    return CursorValue(time=parsed_time, id=cursor_id)


async def _get_orchestrator() -> AnalysisOrchestrator:
    from bybit_options.api.app import _connector

    if not _connector:
        raise HTTPException(503, "Service not initialized")
    return AnalysisOrchestrator(_connector)


@router.get("/trades", response_model=TradeListResponse)
async def get_trades(
    symbol: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    from_time: Optional[datetime] = Query(None, alias="from"),
    to_time: Optional[datetime] = Query(None, alias="to"),
    limit: int = Query(100, ge=1, le=500),
    cursor: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    cursor_value: Optional[CursorValue] = None
    if cursor:
        try:
            cursor_value = _decode_cursor(cursor)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    query = text(
        """
        SELECT
            exec_id,
            order_id,
            symbol,
            category,
            side,
            qty,
            price,
            exec_fee,
            exec_time,
            timestamp,
            size,
            exec_price,
            fee,
            role,
            raw_data
        FROM trades
        WHERE (:symbol IS NULL OR symbol = :symbol)
          AND (:category IS NULL OR category = :category)
          AND (:from_time IS NULL OR COALESCE(exec_time, timestamp) >= :from_time)
          AND (:to_time IS NULL OR COALESCE(exec_time, timestamp) <= :to_time)
          AND (
            :cursor_time IS NULL
            OR COALESCE(exec_time, timestamp) < :cursor_time
            OR (COALESCE(exec_time, timestamp) = :cursor_time AND exec_id < :cursor_id)
          )
        ORDER BY COALESCE(exec_time, timestamp) DESC, exec_id DESC
        LIMIT :limit_plus
        """
    )

    params = {
        "symbol": symbol,
        "category": category,
        "from_time": from_time,
        "to_time": to_time,
        "cursor_time": cursor_value.time if cursor_value else None,
        "cursor_id": cursor_value.id if cursor_value else None,
        "limit_plus": limit + 1,
    }

    result = await db.execute(query, params)
    rows = result.mappings().all()
    sliced = rows[:limit]

    items = [TradeItem(**row) for row in sliced]
    next_cursor = None
    if len(rows) > limit and sliced:
        last = sliced[-1]
        sort_time = last.get("exec_time") or last.get("timestamp")
        if sort_time is not None:
            next_cursor = _encode_cursor(CursorValue(time=sort_time, id=str(last["exec_id"])))

    return TradeListResponse(items=items, limit=limit, next_cursor=next_cursor)


@router.get("/orders", response_model=OrderListResponse)
async def get_orders(
    symbol: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    from_time: Optional[datetime] = Query(None, alias="from"),
    to_time: Optional[datetime] = Query(None, alias="to"),
    limit: int = Query(100, ge=1, le=500),
    cursor: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    cursor_value: Optional[CursorValue] = None
    if cursor:
        try:
            cursor_value = _decode_cursor(cursor)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    query = text(
        """
        SELECT
            order_id,
            symbol,
            category,
            side,
            order_type,
            qty,
            price,
            avg_price,
            cum_exec_qty,
            cum_exec_fee,
            status,
            created_time,
            updated_time,
            raw_data
        FROM orders
        WHERE (:symbol IS NULL OR symbol = :symbol)
          AND (:category IS NULL OR category = :category)
          AND (:status IS NULL OR status = :status)
          AND (:from_time IS NULL OR created_time >= :from_time)
          AND (:to_time IS NULL OR created_time <= :to_time)
          AND (
            :cursor_time IS NULL
            OR created_time < :cursor_time
            OR (created_time = :cursor_time AND order_id < :cursor_id)
          )
        ORDER BY created_time DESC, order_id DESC
        LIMIT :limit_plus
        """
    )

    params = {
        "symbol": symbol,
        "category": category,
        "status": status,
        "from_time": from_time,
        "to_time": to_time,
        "cursor_time": cursor_value.time if cursor_value else None,
        "cursor_id": cursor_value.id if cursor_value else None,
        "limit_plus": limit + 1,
    }

    result = await db.execute(query, params)
    rows = result.mappings().all()
    sliced = rows[:limit]

    items = [OrderItem(**row) for row in sliced]
    next_cursor = None
    if len(rows) > limit and sliced:
        last = sliced[-1]
        sort_time = last.get("created_time")
        if sort_time is not None:
            next_cursor = _encode_cursor(CursorValue(time=sort_time, id=str(last["order_id"])))

    return OrderListResponse(items=items, limit=limit, next_cursor=next_cursor)


@router.get("/portfolio/history", response_model=PortfolioSnapshotListResponse)
async def get_portfolio_history(
    from_time: Optional[datetime] = Query(None, alias="from"),
    to_time: Optional[datetime] = Query(None, alias="to"),
    limit: int = Query(100, ge=1, le=500),
    cursor: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    cursor_value: Optional[CursorValue] = None
    if cursor:
        try:
            cursor_value = _decode_cursor(cursor)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    cursor_id = None
    if cursor_value:
        try:
            cursor_id = int(cursor_value.id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid cursor id") from exc

    query = text(
        """
        SELECT
            id,
            snapshot_time,
            equity,
            available_balance,
            margin_used,
            total_delta,
            total_gamma,
            total_vega,
            total_theta,
            btc_price,
            positions
        FROM portfolio_snapshots
        WHERE (:from_time IS NULL OR snapshot_time >= :from_time)
          AND (:to_time IS NULL OR snapshot_time <= :to_time)
          AND (
            :cursor_time IS NULL
            OR snapshot_time < :cursor_time
            OR (snapshot_time = :cursor_time AND id < :cursor_id)
          )
        ORDER BY snapshot_time DESC, id DESC
        LIMIT :limit_plus
        """
    )

    params = {
        "from_time": from_time,
        "to_time": to_time,
        "cursor_time": cursor_value.time if cursor_value else None,
        "cursor_id": cursor_id,
        "limit_plus": limit + 1,
    }

    result = await db.execute(query, params)
    rows = result.mappings().all()
    sliced = rows[:limit]

    items = [PortfolioSnapshotItem(**row) for row in sliced]
    next_cursor = None
    if len(rows) > limit and sliced:
        last = sliced[-1]
        sort_time = last.get("snapshot_time")
        if sort_time is not None:
            next_cursor = _encode_cursor(CursorValue(time=sort_time, id=str(last["id"])))

    return PortfolioSnapshotListResponse(
        items=items,
        limit=limit,
        next_cursor=next_cursor,
    )


@router.get("/portfolio/current", response_model=PortfolioRiskModel)
async def get_portfolio_current(
    orchestrator: AnalysisOrchestrator = Depends(_get_orchestrator),
):
    try:
        return await orchestrator.run_full_analysis(fetch_enhanced_metrics=True)
    except Exception as exc:  # noqa: BLE001 - map to 500
        raise HTTPException(status_code=500, detail=str(exc)) from exc
