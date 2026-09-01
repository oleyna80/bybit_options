#!/usr/bin/env python3
"""CLI entrypoint for trade history backfill/sync."""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys

from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_order_repository, get_trade_repository
from bybit_options.config.logging import configure_logging
from bybit_options.services.bybit_connector import BybitConnector
from bybit_options.services.trade_history_loader import TradeHistoryLoader


async def _run(args: argparse.Namespace) -> None:
    load_dotenv()

    api_key = os.getenv("BYBIT_API_KEY")
    api_secret = os.getenv("BYBIT_API_SECRET")

    if not api_key or not api_secret:
        raise ValueError("BYBIT_API_KEY and BYBIT_API_SECRET must be set")

    connector = BybitConnector(
        api_key=api_key,
        api_secret=api_secret,
        testnet=os.getenv("BYBIT_TESTNET", "true").lower() == "true",
    )

    trade_repo = get_trade_repository()
    order_repo = get_order_repository()
    loader = TradeHistoryLoader(
        connector,
        trade_repo,
        order_repo,
        window_days=args.window_days,
    )

    async with connector:
        if args.backfill:
            await loader.backfill(days=args.days, category=args.category)
        else:
            await loader.sync(category=args.category)


def main() -> None:
    parser = argparse.ArgumentParser(description="Trade history loader")
    parser.add_argument("--backfill", action="store_true", help="Run backfill")
    parser.add_argument("--days", type=int, default=180, help="Backfill days")
    parser.add_argument("--category", default="option", help="Bybit category")
    parser.add_argument(
        "--window-days",
        type=int,
        default=6,
        help="Window size in days (<=7)",
    )
    args = parser.parse_args()

    configure_logging()
    logger = logging.getLogger("sync_trades")

    try:
        asyncio.run(_run(args))
    except Exception as exc:
        logger.error("Trade history sync failed: %s", exc, exc_info=True)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
