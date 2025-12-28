"""
Deribit client for DVOL and index price fetching.
"""
import asyncio
import logging
from typing import Any, Dict, Optional

import aiohttp

from strategy.config import get_strategy_config

logger = logging.getLogger(__name__)


class DeribitClient:
    """Async Deribit public API client"""

    def __init__(self, base_url: Optional[str] = None, timeout: int = 10):
        config = get_strategy_config()
        self.base_url = base_url or config.deribit_base_url
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def _ensure_session(self):
        if self._session is None:
            self._session = aiohttp.ClientSession(timeout=self.timeout)

    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None

    async def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        await self._ensure_session()
        url = f"{self.base_url}{path}"

        try:
            async with self._session.get(url, params=params) as resp:
                if resp.status == 429:
                    logger.warning("Deribit rate limit hit (429). Backing off briefly.")
                    await asyncio.sleep(0.5)
                resp.raise_for_status()
                return await resp.json()
        except Exception as exc:
            logger.error("Deribit request failed: %s %s", path, exc)
            raise

    async def get_volatility_index(self, currency: str = "BTC") -> Dict[str, Any]:
        """
        Fetch the latest DVOL snapshot for a currency.

        Returns:
            {"dvol": float, "timestamp": int}
        """
        params = {"currency": currency.upper()}
        data = await self._get("/public/get_historical_volatility", params=params)
        result = data.get("result", [])
        if not result:
            raise ValueError("Deribit DVOL response empty")

        # Result is list of [timestamp_ms, value]
        timestamp_ms, dvol_value = result[-1]
        return {
            "dvol": float(dvol_value),
            "timestamp": int(timestamp_ms),
        }

    async def get_index_price(self, currency: str = "BTC") -> Dict[str, Any]:
        """
        Fetch current index price for currency.

        Returns:
            {"index_price": float, "timestamp": int}
        """
        index_name = f"{currency.lower()}_usd"
        data = await self._get("/public/get_index_price", params={"index_name": index_name})
        result = data.get("result", {})
        return {
            "index_price": float(result.get("index_price", 0.0)),
            "timestamp": int(result.get("timestamp", 0)),
        }


async def main():
    logging.basicConfig(level=logging.INFO)
    async with DeribitClient() as client:
        dvol = await client.get_volatility_index("BTC")
        index_price = await client.get_index_price("BTC")
        print(f"DVOL: {dvol}")
        print(f"BTC Index Price: ${index_price['index_price']:.2f}")


if __name__ == "__main__":
    asyncio.run(main())
