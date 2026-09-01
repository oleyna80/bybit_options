#!/usr/bin/env python3
"""
Entry point for Fractal Collector loop (FRAC-004).

Usage:
    python scripts/run_fractal_loop.py --symbol BTCUSDT --h1 --h4
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import signal
import sys
from typing import Iterable

import asyncpg
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bybit_options.services.bybit_connector import BybitConnector
from bybit_options.services.telegram_alerter import TelegramAlerter
from strategy.data.fractal_collector import CollectorLoop
from strategy.data.kline_loader import KlineLoader
from strategy.storage.fractal_storage import FractalStorage


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fractal Collector Loop")
    parser.add_argument("--symbol", default="BTCUSDT", help="Symbol (default: BTCUSDT)")
    parser.add_argument("--h1", action="store_true", help="Enable H1 collection")
    parser.add_argument("--h4", action="store_true", help="Enable H4 collection")
    parser.add_argument("--once", action="store_true", help="Run one cycle and exit")
    parser.add_argument("--log-level", default=None, help="Logging level (default: LOG_LEVEL env or INFO)")
    return parser.parse_args()


def _resolve_timeframes(args: argparse.Namespace) -> list[str]:
    timeframes: list[str] = []
    if args.h1:
        timeframes.append("H1")
    if args.h4:
        timeframes.append("H4")
    if not timeframes:
        timeframes = ["H1", "H4"]
    return timeframes


async def _run_loop(timeframes: Iterable[str], args: argparse.Namespace) -> None:
    load_dotenv()

    api_key = os.getenv("BYBIT_API_KEY")
    api_secret = os.getenv("BYBIT_API_SECRET")
    db_dsn = os.getenv("DATABASE_URL")
    testnet = os.getenv("BYBIT_TESTNET", "false").lower() == "true"
    rate_limit = int(os.getenv("BYBIT_RATE_LIMIT", "50"))

    if not api_key or not api_secret:
        raise ValueError("BYBIT_API_KEY and BYBIT_API_SECRET must be set")
    if not db_dsn:
        raise ValueError("DATABASE_URL must be set")

    log_level = args.log_level or os.getenv("LOG_LEVEL", "INFO")
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    connector = BybitConnector(
        api_key=api_key,
        api_secret=api_secret,
        testnet=testnet,
        rate_limit=rate_limit,
    )
    db_pool = await asyncpg.create_pool(db_dsn)

    storage = FractalStorage(db_pool)
    loader = KlineLoader(connector)
    telegram = TelegramAlerter()
    collector = CollectorLoop(
        symbol=args.symbol,
        kline_loader=loader,
        storage=storage,
        telegram_alerter=telegram,
    )

    stop_event = asyncio.Event()

    def _handle_signal() -> None:
        logging.getLogger("run_fractal_loop").info("Received stop signal")
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _handle_signal)
        except NotImplementedError:
            pass

    try:
        await connector.connect()
        if args.once:
            await collector.run_once(timeframes)
            return

        runner_task = asyncio.create_task(collector.start(timeframes))
        await stop_event.wait()
        await collector.stop()
        await runner_task
    finally:
        await telegram.stop()
        await connector.close()
        await db_pool.close()


async def main() -> None:
    args = _parse_args()
    timeframes = _resolve_timeframes(args)
    await _run_loop(timeframes, args)


if __name__ == "__main__":
    asyncio.run(main())
