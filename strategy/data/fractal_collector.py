"""
Collector loop for Sigma-Fractal key fractals (FRAC-004).
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping, Sequence

from bybit_options.services.telegram_alerter import TelegramAlerter
from strategy.data.kline_loader import KlineLoader
from strategy.indicators.fractals import detect_fractals
from strategy.indicators.key_fractal_filter import KeyFractalFilter
from strategy.storage.fractal_storage import FractalStorage

logger = logging.getLogger(__name__)

TIMEFRAME_INTERVAL_SECONDS = {
    "H1": 5 * 60,       # Check every 5 minutes
    "H4": 15 * 60,      # Check every 15 minutes
    "D1": 60 * 60,      # Check every 1 hour
    "W1": 4 * 60 * 60,  # Check every 4 hours
}


def parse_candle_time(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    raise ValueError("Unsupported candle time format")


def build_fractal_key(
    symbol: str,
    timeframe: str,
    fractal_type: str,
    candle_time: datetime,
) -> tuple[str, str, str, datetime]:
    return (symbol, timeframe, fractal_type.upper(), candle_time)


def identify_new_key_fractals(
    key_fractals: Sequence[Mapping[str, Any]],
    *,
    symbol: str,
    timeframe: str,
    existing_keys: set[tuple[str, str, str, datetime]],
) -> list[Mapping[str, Any]]:
    new_items: list[Mapping[str, Any]] = []
    seen_keys: set[tuple[str, str, str, datetime]] = set()

    for fractal in key_fractals:
        direction = str(fractal.get("direction", "")).upper()
        if direction not in {"UP", "DOWN"}:
            logger.warning("Invalid key fractal direction: %s", direction)
            continue

        try:
            candle_time = parse_candle_time(fractal.get("time"))
        except Exception as exc:  # noqa: BLE001 - log and skip invalid entry
            logger.warning("Invalid key fractal time: %s", exc)
            continue

        key = build_fractal_key(symbol, timeframe, direction, candle_time)
        if key in existing_keys or key in seen_keys:
            continue

        seen_keys.add(key)
        new_items.append(fractal)

    return new_items


class CollectorLoop:
    """Async collector loop for key fractals (H1/H4/D1/W1)."""

    def __init__(
        self,
        *,
        symbol: str,
        kline_loader: KlineLoader,
        storage: FractalStorage,
        telegram_alerter: TelegramAlerter,
        key_filter: KeyFractalFilter | None = None,
    ) -> None:
        self.symbol = symbol
        self.kline_loader = kline_loader
        self.storage = storage
        self.telegram_alerter = telegram_alerter
        self.key_filter = key_filter or KeyFractalFilter()

        self._locks = {timeframe: asyncio.Lock() for timeframe in TIMEFRAME_INTERVAL_SECONDS}
        self._stop_event = asyncio.Event()
        self._tasks: list[asyncio.Task] = []

    async def run_once(self, timeframes: Iterable[str]) -> None:
        for timeframe in timeframes:
            await self._run_timeframe(timeframe)

    async def start(self, timeframes: Iterable[str]) -> None:
        self._stop_event.clear()
        self._tasks = []

        for timeframe in timeframes:
            interval = TIMEFRAME_INTERVAL_SECONDS.get(timeframe.upper())
            if not interval:
                raise ValueError(f"Unsupported timeframe: {timeframe}")

            task = asyncio.create_task(self._run_periodic(timeframe.upper(), interval))
            self._tasks.append(task)

        await self._stop_event.wait()

    async def stop(self) -> None:
        self._stop_event.set()
        for task in self._tasks:
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks = []

    async def _run_periodic(self, timeframe: str, interval_seconds: int) -> None:
        while not self._stop_event.is_set():
            started = asyncio.get_running_loop().time()
            try:
                await self._run_timeframe(timeframe)
            except Exception as exc:  # noqa: BLE001 - log and continue
                logger.error("Collector loop failed for %s: %s", timeframe, exc, exc_info=True)

            elapsed = asyncio.get_running_loop().time() - started
            sleep_for = max(0.0, interval_seconds - elapsed)
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=sleep_for)
            except asyncio.TimeoutError:
                continue

    async def _run_timeframe(self, timeframe: str) -> None:
        lock = self._locks.get(timeframe)
        if lock is None:
            raise ValueError(f"Unsupported timeframe: {timeframe}")
        if lock.locked():
            logger.info("Collector skip %s: previous run still active", timeframe)
            return

        async with lock:
            logger.info("Collector run start: %s %s", self.symbol, timeframe)
            candles = await self.kline_loader.load_klines(
                symbol=self.symbol,
                timeframe=timeframe,
                limit=200,
            )
            if not candles:
                logger.warning("Collector %s %s: no candles returned", self.symbol, timeframe)
                return

            fractals_result = detect_fractals(candles)
            key_fractals = self.key_filter.filter_fractals(candles, fractals_result)
            key_lookup = self._build_key_lookup(timeframe, key_fractals)

            records = self._build_fractal_records(
                candles=candles,
                fractals_result=fractals_result,
                timeframe=timeframe,
                key_lookup=key_lookup,
            )

            existing_keys = await self.storage.fetch_existing_keys(list(key_lookup.keys()))
            new_key_fractals = identify_new_key_fractals(
                key_fractals,
                symbol=self.symbol,
                timeframe=timeframe,
                existing_keys=existing_keys,
            )

            await self.storage.upsert_fractals(records)

            for fractal in new_key_fractals:
                await self._notify_new_key_fractal(timeframe, fractal)

            logger.info(
                "Collector run done: %s %s (fractals=%s key=%s new=%s)",
                self.symbol,
                timeframe,
                len(records),
                len(key_fractals),
                len(new_key_fractals),
            )

    def _build_key_lookup(
        self,
        timeframe: str,
        key_fractals: Sequence[Mapping[str, Any]],
    ) -> dict[tuple[str, str, str, datetime], Mapping[str, Any]]:
        lookup: dict[tuple[str, str, str, datetime], Mapping[str, Any]] = {}
        for fractal in key_fractals:
            direction = str(fractal.get("direction", "")).upper()
            if direction not in {"UP", "DOWN"}:
                continue
            try:
                candle_time = parse_candle_time(fractal.get("time"))
            except Exception:
                continue
            key = build_fractal_key(self.symbol, timeframe, direction, candle_time)
            lookup[key] = fractal
        return lookup

    def _build_fractal_records(
        self,
        *,
        candles: Sequence[Mapping[str, Any]],
        fractals_result: Mapping[str, Any],
        timeframe: str,
        key_lookup: Mapping[tuple[str, str, str, datetime], Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        closes = [float(candle["close"]) for candle in candles]
        teeth_series = self.key_filter._build_teeth_series(closes)

        records: list[dict[str, Any]] = []
        for direction, collection in (
            ("UP", fractals_result.get("fractals_up", []) or []),
            ("DOWN", fractals_result.get("fractals_down", []) or []),
        ):
            for fractal in collection:
                record = self._build_record(
                    candles=candles,
                    fractal=fractal,
                    direction=direction,
                    timeframe=timeframe,
                    closes=closes,
                    teeth_series=teeth_series,
                    key_lookup=key_lookup,
                )
                if record:
                    records.append(record)

        return records

    def _build_record(
        self,
        *,
        candles: Sequence[Mapping[str, Any]],
        fractal: Mapping[str, Any],
        direction: str,
        timeframe: str,
        closes: Sequence[float],
        teeth_series: Sequence[float | None],
        key_lookup: Mapping[tuple[str, str, str, datetime], Mapping[str, Any]],
    ) -> dict[str, Any] | None:
        index = fractal.get("index")
        if index is None or not isinstance(index, int) or index < 0 or index >= len(candles):
            return None

        try:
            price = float(fractal.get("price"))
        except (TypeError, ValueError):
            return None

        candle_time_raw = fractal.get("time")
        if candle_time_raw is None and index < len(candles):
            candle_time_raw = candles[index].get("time")
        try:
            candle_time = parse_candle_time(candle_time_raw)
        except Exception:
            return None

        key = build_fractal_key(self.symbol, timeframe, direction, candle_time)
        is_key_fractal = key in key_lookup
        teeth_value = teeth_series[index] if index < len(teeth_series) else None

        bb_upper_1sigma = None
        bb_upper_2sigma = None
        bb_lower_1sigma = None
        bb_lower_2sigma = None

        try:
            bb = self.key_filter.bollinger.calculate(list(closes)[: index + 1])
            bb_upper_1sigma = float(bb["upper_1sigma"])
            bb_upper_2sigma = float(bb["upper_2sigma"])
            bb_lower_1sigma = float(bb["lower_1sigma"])
            bb_lower_2sigma = float(bb["lower_2sigma"])
        except Exception:
            pass

        if is_key_fractal:
            key_item = key_lookup.get(key) or {}
            bb_upper_1sigma = key_item.get("bb_upper_1sigma", bb_upper_1sigma)
            bb_upper_2sigma = key_item.get("bb_upper_2sigma", bb_upper_2sigma)
            bb_lower_1sigma = key_item.get("bb_lower_1sigma", bb_lower_1sigma)
            bb_lower_2sigma = key_item.get("bb_lower_2sigma", bb_lower_2sigma)
            teeth_value = key_item.get("teeth", teeth_value)

        return {
            "symbol": self.symbol,
            "timeframe": timeframe,
            "fractal_type": direction,
            "price": price,
            "candle_time": candle_time,
            "bb_upper_1sigma": bb_upper_1sigma,
            "bb_lower_1sigma": bb_lower_1sigma,
            "bb_upper_2sigma": bb_upper_2sigma,
            "bb_lower_2sigma": bb_lower_2sigma,
            "alligator_teeth": float(teeth_value) if teeth_value is not None else None,
            "is_key_fractal": is_key_fractal,
            "type": "HIGH" if direction == "UP" else "LOW",
        }

    async def _notify_new_key_fractal(self, timeframe: str, fractal: Mapping[str, Any]) -> None:
        direction = str(fractal.get("direction", "")).upper()
        candle_time = fractal.get("time")
        price = fractal.get("price")
        teeth = fractal.get("teeth")
        upper_1 = fractal.get("bb_upper_1sigma")
        upper_2 = fractal.get("bb_upper_2sigma")
        lower_1 = fractal.get("bb_lower_1sigma")
        lower_2 = fractal.get("bb_lower_2sigma")

        logger.info(
            "New key fractal: %s %s %s price=%s candle=%s",
            self.symbol,
            timeframe,
            direction,
            price,
            candle_time,
        )

        message = (
            "*New Key Fractal*\n"
            f"Symbol: `{self.symbol}`\n"
            f"Timeframe: `{timeframe}`\n"
            f"Type: `{direction}`\n"
            f"Price: `{price}`\n"
            f"Candle: `{candle_time}`\n"
            f"Teeth: `{teeth}`\n"
            f"BB 1σ: `{lower_1}` / `{upper_1}`\n"
            f"BB 2σ: `{lower_2}` / `{upper_2}`"
        )

        if not self.telegram_alerter.enabled:
            logger.info("Telegram disabled; skip alert for %s %s", self.symbol, timeframe)
            return

        await self.telegram_alerter.send_message(message)
