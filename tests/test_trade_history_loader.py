from datetime import datetime, timedelta, timezone

import pytest

from bybit_options.models.trade_history import (
    ExecutionHistoryResponse,
    OrderHistoryResponse,
)
from bybit_options.services.trade_history_loader import TradeHistoryLoader


class _StubTradeRepo:
    def __init__(self) -> None:
        self.upserts: list[list[dict]] = []

    async def upsert_trades(self, trades):
        self.upserts.append(list(trades))
        return len(trades), 0

    async def get_last_exec_time(self):
        return None


class _StubOrderRepo:
    def __init__(self) -> None:
        self.upserts: list[list[dict]] = []

    async def upsert_orders(self, orders):
        self.upserts.append(list(orders))
        return len(orders), 0

    async def get_last_created_time(self):
        return None


class _StubConnector:
    def __init__(self, execution_pages, order_pages) -> None:
        self.execution_pages = execution_pages
        self.order_pages = order_pages
        self.execution_calls = []
        self.order_calls = []

    async def get_execution_history(self, **kwargs):
        self.execution_calls.append(kwargs)
        return ExecutionHistoryResponse.parse_obj(self.execution_pages.pop(0))

    async def get_order_history(self, **kwargs):
        self.order_calls.append(kwargs)
        return OrderHistoryResponse.parse_obj(self.order_pages.pop(0))


def _build_exec_page(cursor: str | None, exec_id: str):
    return {
        "retCode": 0,
        "retMsg": "OK",
        "result": {
            "list": [
                {
                    "execId": exec_id,
                    "orderId": "o1",
                    "symbol": "BTC-30JAN26-100000-C",
                    "side": "Buy",
                    "execQty": "0.1",
                    "execPrice": "1000.5",
                    "execFee": "0.5",
                    "execTime": "1705334400000",
                }
            ],
            "nextPageCursor": cursor,
        },
    }


def _build_order_page(cursor: str | None, order_id: str):
    return {
        "retCode": 0,
        "retMsg": "OK",
        "result": {
            "list": [
                {
                    "orderId": order_id,
                    "symbol": "BTC-30JAN26-100000-C",
                    "side": "Buy",
                    "orderType": "Limit",
                    "qty": "0.1",
                    "price": "1000.0",
                    "avgPrice": "1000.5",
                    "cumExecQty": "0.1",
                    "cumExecFee": "0.5",
                    "orderStatus": "Filled",
                    "createdTime": "1705334400000",
                    "updatedTime": "1705334500000",
                }
            ],
            "nextPageCursor": cursor,
        },
    }


def test_build_windows_max_seven_days():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    end = start + timedelta(days=20)
    windows = TradeHistoryLoader._build_windows(start, end, window_days=7)

    assert windows
    for window in windows:
        assert window.end - window.start <= timedelta(days=7)

    assert windows[0].start == start
    assert windows[-1].end == end


@pytest.mark.asyncio
async def test_cursor_pagination_and_upsert_calls():
    connector = _StubConnector(
        execution_pages=[
            _build_exec_page("cursor-1", "e1"),
            _build_exec_page(None, "e2"),
        ],
        order_pages=[
            _build_order_page("cursor-2", "o1"),
            _build_order_page(None, "o2"),
        ],
    )
    trade_repo = _StubTradeRepo()
    order_repo = _StubOrderRepo()

    loader = TradeHistoryLoader(connector, trade_repo, order_repo, window_days=6)
    window = loader._build_windows(
        datetime(2026, 1, 1, tzinfo=timezone.utc),
        datetime(2026, 1, 2, tzinfo=timezone.utc),
        window_days=6,
    )[0]

    executions = await loader._fetch_executions(window, category="option")
    orders = await loader._fetch_orders(window, category="option")
    await loader._persist_window(executions, orders, category="option")

    assert len(connector.execution_calls) == 2
    assert len(connector.order_calls) == 2
    assert len(trade_repo.upserts) == 1
    assert len(order_repo.upserts) == 1


class _StubRepoWithTime(_StubTradeRepo):
    def __init__(self, last_exec):
        super().__init__()
        self._last_exec = last_exec

    async def get_last_exec_time(self):
        return self._last_exec


@pytest.mark.asyncio
async def test_sync_clamps_start_to_seven_days():
    now = datetime.now(timezone.utc)
    last_exec = now - timedelta(days=30)
    trade_repo = _StubRepoWithTime(last_exec)
    order_repo = _StubOrderRepo()
    connector = _StubConnector(
        execution_pages=[_build_exec_page(None, "e1")],
        order_pages=[_build_order_page(None, "o1")],
    )
    loader = TradeHistoryLoader(connector, trade_repo, order_repo, window_days=6)

    await loader.sync(category="option")

    call = connector.execution_calls[0]
    start_time = call["start_time"]
    expected_start = int((now - timedelta(days=7)).timestamp() * 1000)
    assert start_time >= expected_start
