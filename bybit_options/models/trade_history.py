"""Pydantic models for Bybit trade and order history."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, validator


def _parse_ms_timestamp(value: Optional[str | int]) -> Optional[datetime]:
    if value is None:
        return None
    return datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc)


class ExecutionRecord(BaseModel):
    exec_id: str = Field(alias="execId")
    order_id: Optional[str] = Field(default=None, alias="orderId")
    symbol: str
    side: Optional[str] = None
    exec_qty: Decimal = Field(alias="execQty")
    exec_price: Decimal = Field(alias="execPrice")
    exec_fee: Optional[Decimal] = Field(default=None, alias="execFee")
    exec_time: datetime = Field(alias="execTime")

    @validator("exec_time", pre=True)
    def _parse_exec_time(cls, value):
        parsed = _parse_ms_timestamp(value)
        if parsed is None:
            raise ValueError("execTime is required")
        return parsed

    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            Decimal: lambda v: str(v),
            datetime: lambda v: v.isoformat(),
        }


class ExecutionHistoryResult(BaseModel):
    records: List[ExecutionRecord] = Field(default_factory=list, alias="list")
    next_page_cursor: Optional[str] = Field(default=None, alias="nextPageCursor")

    class Config:
        allow_population_by_field_name = True


class ExecutionHistoryResponse(BaseModel):
    ret_code: int = Field(alias="retCode")
    ret_msg: str = Field(alias="retMsg")
    result: ExecutionHistoryResult = Field(default_factory=ExecutionHistoryResult)

    class Config:
        allow_population_by_field_name = True


class OrderRecord(BaseModel):
    order_id: str = Field(alias="orderId")
    symbol: str
    side: Optional[str] = None
    order_type: Optional[str] = Field(default=None, alias="orderType")
    qty: Decimal = Field(alias="qty")
    price: Optional[Decimal] = Field(default=None, alias="price")
    avg_price: Optional[Decimal] = Field(default=None, alias="avgPrice")
    cum_exec_qty: Optional[Decimal] = Field(default=None, alias="cumExecQty")
    cum_exec_fee: Optional[Decimal] = Field(default=None, alias="cumExecFee")
    order_status: Optional[str] = Field(default=None, alias="orderStatus")
    created_time: datetime = Field(alias="createdTime")
    updated_time: Optional[datetime] = Field(default=None, alias="updatedTime")

    @validator("created_time", "updated_time", pre=True)
    def _parse_order_time(cls, value):
        return _parse_ms_timestamp(value)

    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            Decimal: lambda v: str(v),
            datetime: lambda v: v.isoformat(),
        }


class OrderHistoryResult(BaseModel):
    records: List[OrderRecord] = Field(default_factory=list, alias="list")
    next_page_cursor: Optional[str] = Field(default=None, alias="nextPageCursor")

    class Config:
        allow_population_by_field_name = True


class OrderHistoryResponse(BaseModel):
    ret_code: int = Field(alias="retCode")
    ret_msg: str = Field(alias="retMsg")
    result: OrderHistoryResult = Field(default_factory=OrderHistoryResult)

    class Config:
        allow_population_by_field_name = True
