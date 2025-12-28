"""
Williams Fractals detector.
"""
from typing import Dict, List, Optional

from strategy.config import get_strategy_config


def detect_fractals(candles: List[Dict]) -> Dict[str, Optional[Dict]]:
    """
    Detect Williams fractals on candle list.

    Candle format:
        {"time": int, "high": float, "low": float, ...}
    """
    config = get_strategy_config()
    bars = config.fractal_bars
    if bars != 5:
        # Current implementation uses standard 5-bar Williams fractal.
        bars = 5

    fractals_up = []
    fractals_down = []

    if len(candles) < bars:
        return {
            "fractals_up": fractals_up,
            "fractals_down": fractals_down,
            "last_fractal_up": None,
            "last_fractal_down": None,
        }

    for i in range(2, len(candles) - 2):
        h = candles[i]["high"]
        l = candles[i]["low"]

        if (
            h > candles[i - 1]["high"]
            and h > candles[i - 2]["high"]
            and h > candles[i + 1]["high"]
            and h > candles[i + 2]["high"]
        ):
            fractals_up.append(
                {
                    "price": h,
                    "time": candles[i]["time"],
                    "index": i,
                    "type": "resistance",
                }
            )

        if (
            l < candles[i - 1]["low"]
            and l < candles[i - 2]["low"]
            and l < candles[i + 1]["low"]
            and l < candles[i + 2]["low"]
        ):
            fractals_down.append(
                {
                    "price": l,
                    "time": candles[i]["time"],
                    "index": i,
                    "type": "support",
                }
            )

    return {
        "fractals_up": fractals_up,
        "fractals_down": fractals_down,
        "last_fractal_up": fractals_up[-1] if fractals_up else None,
        "last_fractal_down": fractals_down[-1] if fractals_down else None,
    }


def _demo():
    # Simple demo data
    candles = [
        {"time": i, "open": 100 + i, "high": 110 + i, "low": 90 + i, "close": 100 + i}
        for i in range(20)
    ]
    result = detect_fractals(candles)
    print(result)


if __name__ == "__main__":
    _demo()
