#!/usr/bin/env python3
"""
Delta Collector CLI.

Usage:
    python scripts/run_delta_collector.py --trades
    python scripts/run_delta_collector.py --trades --symbols BTCUSDT,ETHUSDT
    python scripts/run_delta_collector.py --trades --interval 15
"""

import argparse
import asyncio
import os
import sys
from typing import List

# IMPORTANT: Load dotenv BEFORE importing modules that use env vars
from dotenv import load_dotenv
load_dotenv()

from loguru import logger

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bybit_options.services.bybit_connector import BybitConnector
from bybit_options.services.delta.collectors import (
    LargeTradeCollector,
    OrderbookCollector,
    OpenInterestCollector,
)
from bybit_options.services.delta.database_config import db
from bybit_options.services.delta.storage_service import StorageService


async def run_trade_collector(symbols: List[str], interval: int) -> None:
    """Run LargeTradeCollector loop."""
    api_key = os.getenv("BYBIT_API_KEY")
    api_secret = os.getenv("BYBIT_API_SECRET")

    if not api_key or not api_secret:
        raise ValueError("BYBIT_API_KEY and BYBIT_API_SECRET must be set")

    testnet = os.getenv("BYBIT_TESTNET", "false").lower() == "true"

    connector = None
    try:
        await db.connect()

        connector = BybitConnector(
            api_key=api_key,
            api_secret=api_secret,
            testnet=testnet,
        )
        await connector.connect()

        storage = StorageService()
        collector = LargeTradeCollector(
            connector=connector,
            storage=storage,
            symbols=symbols,
            interval_seconds=interval,
        )

        await collector.load_thresholds_from_db()
        await collector.run()
    finally:
        if connector is not None:
            await connector.close()
        await db.close()


async def run_orderbook_collector(symbols: List[str], interval: int) -> None:
    """Run OrderbookCollector loop."""
    api_key = os.getenv("BYBIT_API_KEY")
    api_secret = os.getenv("BYBIT_API_SECRET")

    if not api_key or not api_secret:
        raise ValueError("BYBIT_API_KEY and BYBIT_API_SECRET must be set")

    testnet = os.getenv("BYBIT_TESTNET", "false").lower() == "true"

    connector = None
    try:
        await db.connect()

        connector = BybitConnector(
            api_key=api_key,
            api_secret=api_secret,
            testnet=testnet,
        )
        await connector.connect()

        storage = StorageService()
        collector = OrderbookCollector(
            connector=connector,
            storage=storage,
            symbols=symbols,
            interval_seconds=interval,
        )

        await collector.run()
    finally:
        if connector is not None:
            await connector.close()
        await db.close()


async def run_oi_collector(symbols: List[str], interval: int) -> None:
    """Run OpenInterestCollector loop."""
    api_key = os.getenv("BYBIT_API_KEY")
    api_secret = os.getenv("BYBIT_API_SECRET")

    if not api_key or not api_secret:
        raise ValueError("BYBIT_API_KEY and BYBIT_API_SECRET must be set")

    testnet = os.getenv("BYBIT_TESTNET", "false").lower() == "true"

    connector = None
    try:
        await db.connect()

        connector = BybitConnector(
            api_key=api_key,
            api_secret=api_secret,
            testnet=testnet,
        )
        await connector.connect()

        storage = StorageService()
        collector = OpenInterestCollector(
            connector=connector,
            storage=storage,
            symbols=symbols,
            interval_seconds=interval,
        )

        await collector.run()
    finally:
        if connector is not None:
            await connector.close()
        await db.close()


def main() -> None:

    parser = argparse.ArgumentParser(description="Delta Collector CLI")
    parser.add_argument("--trades", action="store_true", help="Run LargeTradeCollector")
    parser.add_argument("--orderbook", action="store_true", help="Run OrderbookCollector")
    parser.add_argument("--oi", action="store_true", help="Run OpenInterestCollector")
    parser.add_argument(
        "--symbols",
        type=str,
        default="BTCUSDT,ETHUSDT",
        help="Comma-separated symbols",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=10,
        help="Polling interval in seconds",
    )

    args = parser.parse_args()

    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]

    if args.trades and args.orderbook:
        logger.info(
            f"🚀 Starting LargeTradeCollector + OrderbookCollector for {symbols}"
        )

        async def run_both() -> None:
            await asyncio.gather(
                run_trade_collector(symbols, args.interval),
                run_orderbook_collector(symbols, args.interval),
            )

        asyncio.run(run_both())
    elif args.trades:
        logger.info(f"🚀 Starting LargeTradeCollector for {symbols}")
        asyncio.run(run_trade_collector(symbols, args.interval))
    elif args.orderbook:
        logger.info(f"📊 Starting OrderbookCollector for {symbols}")
        asyncio.run(run_orderbook_collector(symbols, args.interval))
    elif args.oi:
        logger.info(f"📈 Starting OpenInterestCollector for {symbols}")
        asyncio.run(run_oi_collector(symbols, args.interval))
    else:
        parser.print_help()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        logger.error(f"Collector failed: {exc}")
        sys.exit(1)
