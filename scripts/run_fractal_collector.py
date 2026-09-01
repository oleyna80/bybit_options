#!/usr/bin/env python3
"""
Smoke runner for Fractal Collector KlineLoader (FRAC-001).

Usage:
    python scripts/run_fractal_collector.py --timeframe H1
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from typing import List, Dict

from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bybit_options.services.bybit_connector import BybitConnector
from strategy.data.kline_loader import KlineLoader


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fractal Collector KlineLoader smoke runner")
    parser.add_argument("--symbol", default="BTCUSDT", help="Symbol (default: BTCUSDT)")
    parser.add_argument("--timeframe", choices=["H1", "H4"], default="H1", help="Timeframe")
    parser.add_argument("--limit", type=int, default=200, help="Number of candles (default: 200)")
    return parser.parse_args()


def _print_summary(candles: List[Dict]) -> None:
    if not candles:
        print("No candles returned")
        return

    first = candles[0]
    last = candles[-1]

    print(f"count: {len(candles)}")
    print(f"first_time: {first['time']}")
    print(f"last_time: {last['time']}")
    print("sample OHLC:")
    for item in candles[:2]:
        print(
            f"  {item['time']} | O={item['open']} H={item['high']} L={item['low']} C={item['close']} V={item['volume']}"
        )


async def main() -> None:
    args = _parse_args()
    load_dotenv()

    api_key = os.getenv("BYBIT_API_KEY")
    api_secret = os.getenv("BYBIT_API_SECRET")
    testnet = os.getenv("BYBIT_TESTNET", "false").lower() == "true"
    rate_limit = int(os.getenv("BYBIT_RATE_LIMIT", "50"))

    if not api_key or not api_secret:
        raise ValueError("BYBIT_API_KEY and BYBIT_API_SECRET must be set")

    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    connector = BybitConnector(
        api_key=api_key,
        api_secret=api_secret,
        testnet=testnet,
        rate_limit=rate_limit,
    )

    loader = KlineLoader(connector)
    try:
        await connector.connect()
        candles = await loader.load_klines(
            symbol=args.symbol,
            timeframe=args.timeframe,
            limit=args.limit,
        )
        _print_summary(candles)
    finally:
        await connector.close()


if __name__ == "__main__":
    asyncio.run(main())
