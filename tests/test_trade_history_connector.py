import unittest
from datetime import timezone

import aiohttp

from bybit_options.services.bybit_connector import BybitConnector


class DummyRequestInfo:
    real_url = "https://api.bybit.com"


class TestTradeHistoryConnector(unittest.IsolatedAsyncioTestCase):
    async def test_execution_history_cursor_and_parsing(self) -> None:
        connector = BybitConnector(api_key="key", api_secret="secret")
        captured: dict[str, object] = {}

        async def fake_signed_request_with_retry(method: str, endpoint: str, params: dict):
            captured["method"] = method
            captured["endpoint"] = endpoint
            captured["params"] = params
            return {
                "retCode": 0,
                "retMsg": "OK",
                "result": {
                    "list": [
                        {
                            "execId": "e1",
                            "orderId": "o1",
                            "symbol": "BTC-30JAN26-100000-C",
                            "side": "Buy",
                            "execQty": "0.1",
                            "execPrice": "1000.5",
                            "execFee": "0.5",
                            "execTime": "1705334400000",
                        }
                    ],
                    "nextPageCursor": "next-cursor",
                },
            }

        connector._signed_request_with_retry = fake_signed_request_with_retry  # type: ignore[assignment]

        response = await connector.get_execution_history(
            category="option",
            start_time=1705330000000,
            end_time=1705340000000,
            limit=50,
            cursor="cursor-1",
        )

        self.assertEqual(captured["endpoint"], "/v5/execution/list")
        self.assertEqual(captured["params"].get("cursor"), "cursor-1")
        self.assertEqual(response.result.next_page_cursor, "next-cursor")
        self.assertEqual(response.result.records[0].exec_id, "e1")
        self.assertEqual(response.result.records[0].exec_time.tzinfo, timezone.utc)

    async def test_order_history_cursor_and_parsing(self) -> None:
        connector = BybitConnector(api_key="key", api_secret="secret")
        captured: dict[str, object] = {}

        async def fake_signed_request_with_retry(method: str, endpoint: str, params: dict):
            captured["method"] = method
            captured["endpoint"] = endpoint
            captured["params"] = params
            return {
                "retCode": 0,
                "retMsg": "OK",
                "result": {
                    "list": [
                        {
                            "orderId": "o1",
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
                    "nextPageCursor": "next-order-cursor",
                },
            }

        connector._signed_request_with_retry = fake_signed_request_with_retry  # type: ignore[assignment]

        response = await connector.get_order_history(
            category="option",
            start_time=1705330000000,
            end_time=1705340000000,
            limit=20,
            cursor="cursor-2",
        )

        self.assertEqual(captured["endpoint"], "/v5/order/history")
        self.assertEqual(captured["params"].get("cursor"), "cursor-2")
        self.assertEqual(response.result.next_page_cursor, "next-order-cursor")
        self.assertEqual(response.result.records[0].order_id, "o1")
        self.assertEqual(response.result.records[0].created_time.tzinfo, timezone.utc)

    async def test_rate_limit_retry_on_retcode(self) -> None:
        connector = BybitConnector(api_key="key", api_secret="secret")
        called: dict[str, object] = {}

        async def fake_signed_request_with_retry(method: str, endpoint: str, params: dict):
            return {"retCode": 10006, "retMsg": "rate limit", "result": {}}

        async def fake_retry(func, *args, **kwargs):
            called["func"] = func
            called["args"] = args
            return {
                "retCode": 0,
                "retMsg": "OK",
                "result": {"list": [], "nextPageCursor": ""},
            }

        connector._signed_request_with_retry = fake_signed_request_with_retry  # type: ignore[assignment]
        connector._retry_with_backoff = fake_retry  # type: ignore[assignment]

        response = await connector.get_execution_history(
            category="option",
            start_time=1705330000000,
            end_time=1705340000000,
            limit=50,
            cursor=None,
        )

        self.assertEqual(response.ret_code, 0)
        self.assertEqual(called["args"][0], "GET")
        self.assertEqual(called["args"][1], "/v5/execution/list")

    async def test_rate_limit_retry_on_http_429(self) -> None:
        connector = BybitConnector(api_key="key", api_secret="secret")
        call_count = 0

        async def fake_retry(func, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise aiohttp.ClientResponseError(
                    request_info=DummyRequestInfo(),
                    history=(),
                    status=429,
                    message="rate limit",
                    headers={},
                )
            return {"retCode": 0, "retMsg": "OK", "result": {}}

        connector._retry_with_backoff = fake_retry  # type: ignore[assignment]

        response = await connector._signed_request_with_retry(
            "GET",
            "/v5/test",
            {"foo": "bar"},
        )

        self.assertEqual(response["retCode"], 0)
        self.assertEqual(call_count, 2)


if __name__ == "__main__":
    unittest.main()
