import unittest

from bybit_options.core.risk_engine import RiskEngine
from bybit_options.models import PositionType


class TestRiskEngine(unittest.TestCase):
    def test_parse_symbol_option_usdt(self) -> None:
        parsed = RiskEngine.parse_symbol("BTC-19DEC25-100000-C-USDT")

        self.assertEqual(parsed.get("base"), "BTC")
        self.assertEqual(parsed.get("series"), "19DEC25")
        self.assertEqual(parsed.get("strike"), "100000")
        self.assertEqual(parsed.get("type"), "C")
        self.assertEqual(parsed.get("settlement"), "USDT")

    def test_calculate_position_greeks_option_sell_flips_sign(self) -> None:
        raw_position = {
            "symbol": "BTC-19DEC25-100000-C-USDT",
            "size": 2,
            "side": "Sell",
        }
        ticker_data = {
            "delta": "0.5",
            "gamma": "0.1",
            "vega": "1.5",
            "theta": "-0.2",
        }

        greeks = RiskEngine.calculate_position_greeks(
            raw_position=raw_position,
            ticker_data=ticker_data,
            pos_type=PositionType.OPTION,
        )

        self.assertAlmostEqual(greeks.delta_coin, -1.0)
        self.assertAlmostEqual(greeks.gamma_coin, -0.2)
        self.assertAlmostEqual(greeks.vega_usd, -3.0)
        self.assertAlmostEqual(greeks.theta_usd, 0.4)

    def test_calculate_iv_metrics_positive_diff(self) -> None:
        metrics = RiskEngine.calculate_iv_metrics(position_iv=0.6, atm_iv=0.5)

        self.assertIsNotNone(metrics)
        self.assertAlmostEqual(metrics.iv_diff_pct, 20.0)


if __name__ == "__main__":
    unittest.main()
