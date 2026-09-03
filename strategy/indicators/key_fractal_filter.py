"""
Key Fractal Filter for Sigma-Fractal strategy.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from strategy.indicators.alligator import shift_forward, smma
from strategy.indicators.bollinger import BollingerBands

logger = logging.getLogger(__name__)


class KeyFractalFilter:
    """Filter fractals by Alligator Teeth and Bollinger Bands conditions."""

    def __init__(
        self,
        teeth_period: int = 8,
        teeth_shift: int = 5,
        bollinger: Optional[BollingerBands] = None,
    ) -> None:
        self.teeth_period = teeth_period
        self.teeth_shift = teeth_shift
        self.bollinger = bollinger or BollingerBands()

    def filter_fractals(self, candles: List[Dict], fractals_result: Dict) -> List[Dict]:
        if not candles:
            return []

        closes = [float(candle["close"]) for candle in candles]
        teeth_series = self._build_teeth_series(closes)

        filtered: List[Dict] = []
        for fractal in fractals_result.get("fractals_up", []) or []:
            result = self._evaluate_fractal(
                fractal=fractal,
                direction="UP",
                closes=closes,
                teeth_series=teeth_series,
            )
            if result:
                filtered.append(result)

        for fractal in fractals_result.get("fractals_down", []) or []:
            result = self._evaluate_fractal(
                fractal=fractal,
                direction="DOWN",
                closes=closes,
                teeth_series=teeth_series,
            )
            if result:
                filtered.append(result)

        return filtered

    def _build_teeth_series(self, closes: List[float]) -> List[Optional[float]]:
        return shift_forward(smma(closes, self.teeth_period), self.teeth_shift)

    def _evaluate_fractal(
        self,
        fractal: Dict,
        direction: str,
        closes: List[float],
        teeth_series: List[Optional[float]],
    ) -> Optional[Dict]:
        index = fractal.get("index")
        time_value = fractal.get("time")
        try:
            price = float(fractal.get("price"))
        except (TypeError, ValueError):
            self._log_skip(
                reason="invalid_price",
                direction=direction,
                index=index,
                time_value=time_value,
                price=fractal.get("price"),
                teeth=None,
            )
            return None

        if index is None or not isinstance(index, int) or index < 0 or index >= len(closes):
            self._log_skip(
                reason="invalid_index",
                direction=direction,
                index=index,
                time_value=time_value,
                price=price,
                teeth=None,
            )
            return None

        teeth_value = teeth_series[index] if index < len(teeth_series) else None
        if teeth_value is None:
            self._log_skip(
                reason="missing_teeth",
                direction=direction,
                index=index,
                time_value=time_value,
                price=price,
                teeth=None,
            )
            return None

        try:
            bb = self.bollinger.calculate(closes[: index + 1])
        except ValueError as exc:
            self._log_skip(
                reason="bb_unavailable",
                direction=direction,
                index=index,
                time_value=time_value,
                price=price,
                teeth=teeth_value,
                details=str(exc),
            )
            return None

        if direction == "UP":
            teeth_condition = price > teeth_value
            bb_condition = bb["upper_1sigma"] < price < bb["upper_2sigma"]
        else:
            teeth_condition = price < teeth_value
            bb_condition = bb["lower_2sigma"] < price < bb["lower_1sigma"]

        if not teeth_condition:
            self._log_skip(
                reason="teeth_condition_failed",
                direction=direction,
                index=index,
                time_value=time_value,
                price=price,
                teeth=teeth_value,
            )
            return None

        if not bb_condition:
            self._log_skip(
                reason="bb_condition_failed",
                direction=direction,
                index=index,
                time_value=time_value,
                price=price,
                teeth=teeth_value,
                details=(
                    f"bb_upper_1sigma={bb['upper_1sigma']}, "
                    f"bb_upper_2sigma={bb['upper_2sigma']}, "
                    f"bb_lower_1sigma={bb['lower_1sigma']}, "
                    f"bb_lower_2sigma={bb['lower_2sigma']}"
                ),
            )
            return None

        return {
            "index": index,
            "time": time_value,
            "price": price,
            "direction": direction,
            "teeth": float(teeth_value),
            "bb_upper_1sigma": float(bb["upper_1sigma"]),
            "bb_upper_2sigma": float(bb["upper_2sigma"]),
            "bb_lower_1sigma": float(bb["lower_1sigma"]),
            "bb_lower_2sigma": float(bb["lower_2sigma"]),
        }

    def _log_skip(
        self,
        reason: str,
        direction: str,
        index: Optional[int],
        time_value: Optional[int],
        price: Optional[float],
        teeth: Optional[float],
        details: Optional[str] = None,
    ) -> None:
        message = (
            "KeyFractalFilter skip: "
            f"reason={reason} direction={direction} index={index} time={time_value} "
            f"price={price} teeth={teeth}"
        )
        if details:
            message = f"{message} details={details}"
        logger.info(message)
