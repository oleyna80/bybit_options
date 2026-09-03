import logging
import unittest

from strategy.indicators.key_fractal_filter import KeyFractalFilter


class TestKeyFractalFilter(unittest.TestCase):
    def setUp(self) -> None:
        self.candles = [
            {
                "time": index,
                "open": float(index),
                "high": float(index),
                "low": float(index),
                "close": float(index),
                "volume": 1.0,
            }
            for index in range(30)
        ]
        self.base_fractals = {
            "fractals_up": [],
            "fractals_down": [],
            "last_fractal_up": None,
            "last_fractal_down": None,
        }

    def test_up_passes_both_conditions(self) -> None:
        self.candles[25]["high"] = 25.5
        self.candles[25]["close"] = 25.0
        fractals = dict(self.base_fractals)
        fractals["fractals_up"] = [
            {"price": 25.5, "time": 25, "index": 25, "type": "resistance"}
        ]

        filt = KeyFractalFilter()
        result = filt.filter_fractals(self.candles, fractals)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["direction"], "UP")
        self.assertEqual(result[0]["index"], 25)
        self.assertIn("bb_upper_1sigma", result[0])

    def test_up_fails_teeth_condition(self) -> None:
        self.candles[25]["high"] = 10.0
        self.candles[25]["close"] = 25.0
        fractals = dict(self.base_fractals)
        fractals["fractals_up"] = [
            {"price": 10.0, "time": 25, "index": 25, "type": "resistance"}
        ]

        filt = KeyFractalFilter()
        result = filt.filter_fractals(self.candles, fractals)

        self.assertEqual(result, [])

    def test_up_fails_bb_condition(self) -> None:
        self.candles[25]["high"] = 40.0
        self.candles[25]["close"] = 25.0
        fractals = dict(self.base_fractals)
        fractals["fractals_up"] = [
            {"price": 40.0, "time": 25, "index": 25, "type": "resistance"}
        ]

        filt = KeyFractalFilter()
        result = filt.filter_fractals(self.candles, fractals)

        self.assertEqual(result, [])

    def test_down_passes_both_conditions(self) -> None:
        # Calculate BB first to find a valid price in lower zone
        filt = KeyFractalFilter()
        bb = filt.bollinger.calculate([c["close"] for c in self.candles[:26]])
        # Price should be between lower_2sigma and lower_1sigma, and below teeth
        valid_price = (bb["lower_1sigma"] + bb["lower_2sigma"]) / 2
        
        self.candles[25]["low"] = valid_price
        self.candles[25]["close"] = 25.0
        fractals = dict(self.base_fractals)
        fractals["fractals_down"] = [
            {"price": valid_price, "time": 25, "index": 25, "type": "support"}
        ]

        result = filt.filter_fractals(self.candles, fractals)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["direction"], "DOWN")

    def test_boundary_equality_fails(self) -> None:
        self.candles[25]["high"] = 25.5
        self.candles[25]["close"] = 25.0
        fractals = dict(self.base_fractals)
        fractals["fractals_up"] = [
            {"price": 25.5, "time": 25, "index": 25, "type": "resistance"}
        ]

        filt = KeyFractalFilter()
        bb = filt.bollinger.calculate([c["close"] for c in self.candles[:26]])
        fractals["fractals_up"][0]["price"] = bb["upper_1sigma"]

        result = filt.filter_fractals(self.candles, fractals)

        self.assertEqual(result, [])

    def test_missing_teeth_or_bb_logs_and_skips(self) -> None:
        candles = self.candles[:10]
        fractals = dict(self.base_fractals)
        fractals["fractals_up"] = [
            {"price": 10.0, "time": 5, "index": 5, "type": "resistance"}
        ]

        filt = KeyFractalFilter()
        with self.assertLogs(level=logging.INFO) as captured:
            result = filt.filter_fractals(candles, fractals)

        self.assertEqual(result, [])
        self.assertTrue(
            any("missing_teeth" in message or "bb_unavailable" in message for message in captured.output)
        )


if __name__ == "__main__":
    unittest.main()
