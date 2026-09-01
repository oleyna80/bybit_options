"""
Kline loader for Fractal Collector (FRAC-001).

Supports: H1, H4, D1 (Daily), W1 (Weekly)

Usage (async):
    loader = KlineLoader(connector)
    candles = await loader.load_klines(symbol="BTCUSDT", timeframe="H1", limit=200)

Output format (time is ISO 8601 UTC string):
    [{"time", "open", "high", "low", "close", "volume"}, ...]
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List

from bybit_options.services.bybit_connector import BybitConnector

logger = logging.getLogger(__name__)

TIMEFRAME_INTERVALS = {
    "H1": "60",
    "H4": "240",
    "D1": "D",   # Daily
    "W1": "W",   # Weekly
}


class KlineLoader:
    """Fetch and normalize klines from Bybit for H1/H4/D1/W1 timeframes."""

    def __init__(
        self,
        connector: BybitConnector,
        category: str = "linear",
        max_retries: int = 3,
        backoff_seconds: float = 0.5,
    ) -> None:
        self.connector = connector
        self.category = category
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds

    async def load_klines(self, symbol: str, timeframe: str, limit: int = 200) -> List[Dict]:
        """
        Load klines from Bybit and normalize them.

        Args:
            symbol: Trading pair, e.g. "BTCUSDT"
            timeframe: "H1", "H4", "D1", or "W1"
            limit: number of candles to fetch (default 200)

        Returns:
            List of normalized candles in chronological order.
        """
        interval = self._normalize_timeframe(timeframe)
        if limit <= 0:
            raise ValueError("limit must be positive")

        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                raw = await self.connector.get_kline_history(
                    category=self.category,
                    symbol=symbol,
                    interval=interval,
                    limit=limit,
                )
                if not raw:
                    raise RuntimeError("Empty kline response")

                # Bybit returns newest first; keep chronological order
                return [self._parse_kline(item) for item in reversed(raw)]
            except Exception as exc:  # noqa: BLE001 - required for retry
                last_error = exc
                logger.warning(
                    "Kline fetch failed (attempt %s/%s) for %s %s: %s",
                    attempt,
                    self.max_retries,
                    symbol,
                    timeframe,
                    exc,
                    exc_info=True,
                )

                if attempt < self.max_retries:
                    await asyncio.sleep(self.backoff_seconds * (2 ** (attempt - 1)))

        if last_error:
            raise last_error

        return []

    @staticmethod
    def _normalize_timeframe(timeframe: str) -> str:
        try:
            return TIMEFRAME_INTERVALS[timeframe.upper()]
        except KeyError as exc:
            raise ValueError("timeframe must be H1, H4, D1, or W1") from exc

    @staticmethod
    def _parse_kline(kline: List[str]) -> Dict:
        # [timestamp, open, high, low, close, volume, turnover]
        timestamp_ms = int(kline[0])
        timestamp = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
        return {
            "time": timestamp.isoformat(),
            "open": float(kline[1]),
            "high": float(kline[2]),
            "low": float(kline[3]),
            "close": float(kline[4]),
            "volume": float(kline[5]),
        }
