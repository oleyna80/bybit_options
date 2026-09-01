import unittest

from option_board_utils import fetch_option_tickers


class _FakeConnector:
    def __init__(self):
        self.requested = []

    async def get_tickers(self, category: str, symbol: str):
        self.requested.append((category, symbol))
        return [{"symbol": symbol}]


class TestOptionBoardUtils(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_option_tickers_preserves_suffix(self) -> None:
        connector = _FakeConnector()
        symbols = [
            "BTC-10JAN26-90000-C-USDT",
            "BTC-10JAN26-90000-P",
        ]

        results = await fetch_option_tickers(connector, symbols, batch_size=10)

        self.assertEqual(
            connector.requested,
            [
                ("option", "BTC-10JAN26-90000-C-USDT"),
                ("option", "BTC-10JAN26-90000-P-USDT"),
            ],
        )
        self.assertEqual(set(results.keys()), set(symbols))


if __name__ == "__main__":
    unittest.main()
