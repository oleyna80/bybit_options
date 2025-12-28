"""
Bollinger Bands and squeeze detection.
"""
from typing import Dict, List

import numpy as np

from strategy.config import get_strategy_config


class BollingerBands:
    """Calculate double Bollinger Bands (1σ, 2σ)."""

    def __init__(self):
        self.config = get_strategy_config()

    def calculate(self, prices: List[float]) -> Dict[str, float]:
        period = self.config.bb_period
        if len(prices) < period:
            raise ValueError("Not enough prices for Bollinger calculation")

        window = np.array(prices[-period:], dtype=float)
        middle = float(np.mean(window))
        std = float(np.std(window, ddof=0))

        upper_1sigma = middle + self.config.bb_std_inner * std
        lower_1sigma = middle - self.config.bb_std_inner * std
        upper_2sigma = middle + self.config.bb_std_outer * std
        lower_2sigma = middle - self.config.bb_std_outer * std

        bb_width = ((upper_2sigma - lower_2sigma) / middle) * 100 if middle else 0.0

        return {
            "upper_2sigma": float(upper_2sigma),
            "upper_1sigma": float(upper_1sigma),
            "middle": float(middle),
            "lower_1sigma": float(lower_1sigma),
            "lower_2sigma": float(lower_2sigma),
            "bb_width": float(bb_width),
        }

    def bb_width_history(self, prices: List[float]) -> List[float]:
        period = self.config.bb_period
        if len(prices) < period:
            return []

        widths = []
        for i in range(period, len(prices) + 1):
            window = np.array(prices[i - period : i], dtype=float)
            middle = float(np.mean(window))
            std = float(np.std(window, ddof=0))
            upper_2sigma = middle + self.config.bb_std_outer * std
            lower_2sigma = middle - self.config.bb_std_outer * std
            bb_width = ((upper_2sigma - lower_2sigma) / middle) * 100 if middle else 0.0
            widths.append(float(bb_width))

        return widths


class SqueezeDetector:
    """Detect squeeze based on BB width percentile."""

    def __init__(self):
        self.config = get_strategy_config()

    def detect_squeeze(self, bb_width_history: List[float], current_width: float) -> Dict[str, float]:
        if not bb_width_history:
            return {"is_squeeze": False, "percentile_rank": 100.0}

        percentile = float(np.percentile(bb_width_history, self.config.squeeze_percentile))
        is_squeeze = current_width < percentile

        percentile_rank = float(
            np.sum(np.array(bb_width_history) <= current_width) / len(bb_width_history) * 100
        )

        return {
            "is_squeeze": bool(is_squeeze),
            "percentile_rank": percentile_rank,
        }


def _demo():
    prices = [100 + np.sin(i / 5) * 5 for i in range(60)]
    bb = BollingerBands()
    bands = bb.calculate(prices)
    widths = bb.bb_width_history(prices)

    squeeze = SqueezeDetector().detect_squeeze(widths, bands["bb_width"])
    print(bands)
    print(squeeze)


if __name__ == "__main__":
    _demo()
