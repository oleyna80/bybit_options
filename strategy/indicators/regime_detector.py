"""
Market regime detector for Sigma-Fractal (D1 logic).
"""
from typing import Dict, List, Optional

from strategy.indicators.bollinger import BollingerBands, SqueezeDetector
from strategy.indicators.fractals import detect_fractals


def _select_key_fractal(fractals: List[Dict], lower: float, upper: float) -> Optional[Dict]:
    candidates = [f for f in fractals if lower <= f["price"] <= upper]
    return candidates[-1] if candidates else None


def analyze_regime(d1_candles: List[Dict], bb_width_history: List[float]) -> Dict[str, Optional[object]]:
    if len(d1_candles) < 20:
        return {
            "regime": "UNKNOWN",
            "description": "Not enough D1 candles",
            "key_support": None,
            "key_resistance": None,
            "squeeze_active": False,
            "current_price": None,
            "bb_current": None,
            "recommended_strategy": None,
        }

    closes = [c["close"] for c in d1_candles]
    last_close = closes[-1]

    bb = BollingerBands()
    bands = bb.calculate(closes)

    fractals = detect_fractals(d1_candles)
    key_resistance = _select_key_fractal(
        fractals["fractals_up"],
        bands["upper_1sigma"],
        bands["upper_2sigma"],
    )
    key_support = _select_key_fractal(
        fractals["fractals_down"],
        bands["lower_2sigma"],
        bands["lower_1sigma"],
    )

    squeeze_data = SqueezeDetector().detect_squeeze(bb_width_history, bands["bb_width"])
    squeeze_active = squeeze_data["is_squeeze"]

    regime = "RANGE"
    description = "Цена внутри ключевых фракталов D1"

    if key_resistance and last_close > key_resistance["price"]:
        regime = "TREND_UP"
        description = "Цена выше ключевого сопротивления"
    elif key_support and last_close < key_support["price"]:
        regime = "TREND_DOWN"
        description = "Цена ниже ключевой поддержки"

    percentile_rank = squeeze_data.get("percentile_rank", 100.0)
    if percentile_rank < 25:
        vol_risk = "LOW"
    elif percentile_rank < 75:
        vol_risk = "MEDIUM"
    else:
        vol_risk = "HIGH"

    if squeeze_active:
        recommended_strategy = "Long Volatility"
    elif regime == "RANGE":
        recommended_strategy = "Iron Condor"
    else:
        recommended_strategy = "Directional Spread"

    return {
        "regime": regime,
        "description": description,
        "key_support": key_support["price"] if key_support else None,
        "key_resistance": key_resistance["price"] if key_resistance else None,
        "squeeze_active": squeeze_active,
        "current_price": last_close,
        "bb_current": bands,
        "recommended_strategy": recommended_strategy,
        "vol_risk": vol_risk,
    }


def _demo():
    import numpy as np

    candles = []
    for i in range(60):
        price = 90000 + np.sin(i / 5) * 1500
        candles.append(
            {
                "time": i,
                "open": price - 50,
                "high": price + 100,
                "low": price - 100,
                "close": price,
            }
        )

    widths = BollingerBands().bb_width_history([c["close"] for c in candles])
    result = analyze_regime(candles, widths)
    print(result)


if __name__ == "__main__":
    _demo()
