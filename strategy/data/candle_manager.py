"""
Candle manager for D1/H4/H1 data from Bybit.
"""
from typing import List, Dict, Optional

from bybit_connector import BybitConnector


class CandleManager:
    """Fetch and normalize candles from Bybit."""

    def __init__(self, connector: BybitConnector):
        self.connector = connector

    async def get_d1_candles(self, symbol: str = "BTCUSDT", days: int = 120) -> List[Dict]:
        """Fetch daily candles (D1)."""
        return await self._fetch_candles(symbol=symbol, interval="D", limit=days)

    async def get_h4_candles(self, symbol: str = "BTCUSDT", limit: int = 240) -> List[Dict]:
        """Fetch 4-hour candles (H4)."""
        return await self._fetch_candles(symbol=symbol, interval="240", limit=limit)

    async def get_h1_candles(self, symbol: str = "BTCUSDT", limit: int = 240) -> List[Dict]:
        """Fetch 1-hour candles (H1)."""
        return await self._fetch_candles(symbol=symbol, interval="60", limit=limit)

    async def _fetch_candles(
        self,
        symbol: str,
        interval: str,
        limit: int,
        start_time_ms: Optional[int] = None,
        end_time_ms: Optional[int] = None,
    ) -> List[Dict]:
        raw = await self.connector.get_kline_history(
            category="linear",
            symbol=symbol,
            interval=interval,
            start_time_ms=start_time_ms,
            end_time_ms=end_time_ms,
            limit=limit,
        )
        # Bybit returns newest first; keep chronological order
        candles = [self._parse_kline(item) for item in reversed(raw or [])]
        return candles

    @staticmethod
    def _parse_kline(kline: List[str]) -> Dict:
        # [timestamp, open, high, low, close, volume, turnover]
        return {
            "time": int(kline[0]) // 1000,
            "open": float(kline[1]),
            "high": float(kline[2]),
            "low": float(kline[3]),
            "close": float(kline[4]),
            "volume": float(kline[5]),
        }

