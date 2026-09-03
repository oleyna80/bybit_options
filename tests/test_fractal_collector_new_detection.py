from __future__ import annotations

from datetime import datetime, timezone

from strategy.data.fractal_collector import (
    build_fractal_key,
    identify_new_key_fractals,
)


def _fractal(time_value: datetime, direction: str = "UP") -> dict:
    return {
        "time": time_value,
        "direction": direction,
        "price": 100.0,
        "teeth": 99.0,
        "bb_upper_1sigma": 101.0,
        "bb_upper_2sigma": 102.0,
        "bb_lower_1sigma": 98.0,
        "bb_lower_2sigma": 97.0,
    }


def test_identify_new_key_fractals_filters_existing_and_duplicates() -> None:
    candle_time = datetime(2026, 1, 18, 0, 0, tzinfo=timezone.utc)
    other_time = datetime(2026, 1, 18, 1, 0, tzinfo=timezone.utc)

    existing = {
        build_fractal_key("BTCUSDT", "H1", "UP", candle_time),
    }

    items = [
        _fractal(candle_time, "UP"),
        _fractal(candle_time, "UP"),
        _fractal(other_time, "DOWN"),
    ]

    result = identify_new_key_fractals(
        items,
        symbol="BTCUSDT",
        timeframe="H1",
        existing_keys=existing,
    )

    assert len(result) == 1
    assert result[0]["direction"] == "DOWN"
    assert result[0]["time"] == other_time


def test_identify_new_key_fractals_skips_invalid_direction() -> None:
    candle_time = datetime(2026, 1, 18, 2, 0, tzinfo=timezone.utc)
    items = [_fractal(candle_time, "SIDE")]

    result = identify_new_key_fractals(
        items,
        symbol="BTCUSDT",
        timeframe="H4",
        existing_keys=set(),
    )

    assert result == []
