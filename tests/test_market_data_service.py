import unittest

from bybit_options.services.market_data_service import MarketDataService


class FakeBybitConnector:
    async def get_positions(self, category: str, settle_coin: str | None = None):
        if category == "linear":
            return [
                {
                    "symbol": "BTCUSDT",
                    "size": "1",
                    "side": "Buy",
                }
            ]
        if category == "option":
            return [
                {
                    "symbol": "BTC-19DEC25-100000-C-USDT",
                    "size": "2",
                    "side": "Sell",
                }
            ]
        return []


class TestMarketDataService(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_all_positions_tags_categories(self) -> None:
        service = MarketDataService(FakeBybitConnector())

        positions = await service.fetch_all_positions()

        self.assertEqual(len(positions), 2)
        categories = {pos.get("_category") for pos in positions}
        self.assertEqual(categories, {"linear", "option"})


if __name__ == "__main__":
    unittest.main()
