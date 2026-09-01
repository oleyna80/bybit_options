"""
Alligator indicator (SMMA) for Sigma-Fractal strategy.

Input:
    candles: list of dicts compatible with KlineLoader.load_klines()
        [{"time", "open", "high", "low", "close", "volume"}, ...]

Shift rule:
    SMMA is calculated as a full series aligned to input indices, then shifted
    forward by N bars (i -> i + shift). Unassigned positions are filled with
    None to make the rule testable.

Insufficient data handling:
    If there is not enough data to compute or shift a line for the current bar,
    return None for that line instead of raising.
"""

from __future__ import annotations

from typing import Dict, List, Optional


def smma(prices: List[float], period: int) -> List[Optional[float]]:
    """Compute Smoothed Moving Average (SMMA) series.

    Returns a list of the same length as prices. The first (period - 1) values
    are None, and the first SMMA value is the SMA of the initial period.
    """
    if period <= 0:
        raise ValueError("period must be positive")
    if not prices:
        return []
    if len(prices) < period:
        return [None] * len(prices)

    smma_values: List[Optional[float]] = [None] * len(prices)
    first_value = sum(prices[:period]) / period
    smma_values[period - 1] = float(first_value)

    for i in range(period, len(prices)):
        prev = smma_values[i - 1]
        if prev is None:
            continue
        smma_values[i] = float(((prev * (period - 1)) + prices[i]) / period)

    return smma_values


def shift_forward(values: List[Optional[float]], shift: int) -> List[Optional[float]]:
    """Shift series forward by N bars; fill unassigned positions with None."""
    if shift < 0:
        raise ValueError("shift must be non-negative")
    if not values:
        return []
    if shift == 0:
        return list(values)

    shifted: List[Optional[float]] = [None] * len(values)
    for index, value in enumerate(values):
        if value is None:
            continue
        target_index = index + shift
        if target_index < len(values):
            shifted[target_index] = value

    return shifted


class AlligatorIndicator:
    """Calculate Alligator (Jaw/Teeth/Lips) for the current bar."""

    def __init__(
        self,
        jaw_period: int = 13,
        teeth_period: int = 8,
        lips_period: int = 5,
        jaw_shift: int = 8,
        teeth_shift: int = 5,
        lips_shift: int = 3,
    ) -> None:
        self.jaw_period = jaw_period
        self.teeth_period = teeth_period
        self.lips_period = lips_period
        self.jaw_shift = jaw_shift
        self.teeth_shift = teeth_shift
        self.lips_shift = lips_shift

    def calculate(self, candles: List[Dict]) -> Dict[str, Optional[float]]:
        """Return current bar values for jaw/teeth/lips.

        Args:
            candles: list of OHLCV dicts (see module docstring).

        Returns:
            {"jaw": float|None, "teeth": float|None, "lips": float|None}
        """
        if not candles:
            return {"jaw": None, "teeth": None, "lips": None}

        closes = [float(candle["close"]) for candle in candles]

        jaw_series = shift_forward(smma(closes, self.jaw_period), self.jaw_shift)
        teeth_series = shift_forward(smma(closes, self.teeth_period), self.teeth_shift)
        lips_series = shift_forward(smma(closes, self.lips_period), self.lips_shift)

        return {
            "jaw": jaw_series[-1] if jaw_series else None,
            "teeth": teeth_series[-1] if teeth_series else None,
            "lips": lips_series[-1] if lips_series else None,
        }
