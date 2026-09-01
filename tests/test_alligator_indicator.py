import unittest

from strategy.indicators.alligator import AlligatorIndicator, shift_forward, smma


class TestSmma(unittest.TestCase):
    def test_smma_on_synthetic_series(self) -> None:
        prices = [1, 2, 3, 4, 5]
        result = smma(prices, period=3)

        self.assertEqual(len(result), 5)
        self.assertIsNone(result[0])
        self.assertIsNone(result[1])
        self.assertAlmostEqual(result[2], 2.0, places=6)
        self.assertAlmostEqual(result[3], 2.6666666667, places=6)
        self.assertAlmostEqual(result[4], 3.4444444444, places=6)


class TestShiftForward(unittest.TestCase):
    def test_shift_applies_forward_and_fills_none(self) -> None:
        values = [1.0, 2.0, 3.0]
        shifted = shift_forward(values, shift=1)

        self.assertEqual(shifted, [None, 1.0, 2.0])


class TestAlligatorIndicator(unittest.TestCase):
    def test_current_bar_value_with_shift(self) -> None:
        closes = [1, 2, 3, 4, 5, 6]
        candles = [{"close": price} for price in closes]

        indicator = AlligatorIndicator(
            jaw_period=3,
            teeth_period=3,
            lips_period=3,
            jaw_shift=2,
            teeth_shift=2,
            lips_shift=2,
        )
        result = indicator.calculate(candles)

        self.assertAlmostEqual(result["jaw"], 2.6666666667, places=6)
        self.assertAlmostEqual(result["teeth"], 2.6666666667, places=6)
        self.assertAlmostEqual(result["lips"], 2.6666666667, places=6)

    def test_insufficient_data_returns_none(self) -> None:
        candles = [{"close": 100.0}, {"close": 101.0}]
        indicator = AlligatorIndicator(jaw_period=5, teeth_period=5, lips_period=5)

        result = indicator.calculate(candles)

        self.assertIsNone(result["jaw"])
        self.assertIsNone(result["teeth"])
        self.assertIsNone(result["lips"])


if __name__ == "__main__":
    unittest.main()
