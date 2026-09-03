"""
Bybit Options Data Helper
"""
import asyncio
from typing import Dict, Optional
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from bybit_options.services.bybit_connector import BybitConnector
from config import get_config


class BybitOptionsData:
    """Helper to fetch options data from Bybit API"""

    def __init__(self, connector: Optional[BybitConnector] = None):
        self.connector = connector

    async def _ensure_connector(self) -> BybitConnector:
        if not self.connector:
            config = get_config()
            self.connector = BybitConnector(
                api_key=config.bybit.api_key,
                api_secret=config.bybit.api_secret,
                testnet=config.bybit.testnet
            )
        await self.connector._init_session()
        return self.connector

    async def close(self) -> None:
        if self.connector:
            await self.connector.close()

    async def get_option_mark_iv(self, symbol: str) -> Optional[float]:
        """
        Get Mark IV for specific option

        Args:
            symbol: e.g., "BTC-27DEC25-100000-C"

        Returns:
            Mark IV as float (e.g., 0.53 = 53%) or None if not found
        """
        try:
            connector = await self._ensure_connector()
            result = await connector.get_tickers(
                category='option',
                symbol=symbol
            )

            if result and len(result) > 0:
                ticker = result[0]
                if isinstance(ticker, dict):
                    mark_iv = ticker.get('markIv')
                    if mark_iv:
                        return float(mark_iv)

            return None

        except Exception as e:
            print(f"Error fetching Mark IV for {symbol}: {e}")
            return None

    async def get_options_chain_ivs(self, base_coin: str = 'BTC') -> Dict[str, float]:
        """
        Get Mark IVs for entire options chain

        Args:
            base_coin: 'BTC', 'ETH', etc.

        Returns:
            Dict mapping symbol -> Mark IV
        """
        try:
            connector = await self._ensure_connector()
            result = await connector.get_tickers(
                category='option',
                base_coin=base_coin
            )

            ivs = {}
            for ticker in result:
                if not isinstance(ticker, dict):
                    continue
                symbol = ticker.get('symbol')
                mark_iv = ticker.get('markIv')
                if symbol and mark_iv:
                    ivs[symbol] = float(mark_iv)

            return ivs

        except Exception as e:
            print(f"Error fetching options chain IVs: {e}")
            return {}


if __name__ == "__main__":
    async def test():
        helper = BybitOptionsData()
        try:
            print("Fetching Mark IV for BTC-27DEC25-100000-C...")
            iv = await helper.get_option_mark_iv("BTC-27DEC25-100000-C")
            if iv:
                print(f"  Mark IV: {iv*100:.2f}%")
            else:
                print("  Not found (option may not exist)")

            print("\nFetching BTC options chain IVs...")
            ivs = await helper.get_options_chain_ivs('BTC')
            print(f"  Found {len(ivs)} options")
            if ivs:
                for symbol, iv in list(ivs.items())[:5]:
                    print(f"    {symbol}: {iv*100:.2f}%")
        finally:
            await helper.close()

    asyncio.run(test())
