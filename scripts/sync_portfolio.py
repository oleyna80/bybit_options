#!/usr/bin/env python3
"""CLI entrypoint for portfolio snapshots (hourly)."""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from datetime import timedelta

from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_portfolio_snapshot_repository
from bybit_options.config.logging import configure_logging
from bybit_options.orchestration.analysis_orchestrator import AnalysisOrchestrator
from bybit_options.services.bybit_connector import BybitConnector
from bybit_options.services.portfolio_syncer import PortfolioSyncer


async def _run_once(syncer: PortfolioSyncer, logger: logging.Logger) -> None:
    result = await syncer.take_snapshot()
    logger.info(
        "Snapshot stored: time=%s inserted=%s",
        result.snapshot_time.isoformat(),
        result.inserted,
    )


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

    snapshot_repo = get_portfolio_snapshot_repository()
    orchestrator = AnalysisOrchestrator(connector)
    syncer = PortfolioSyncer(orchestrator, snapshot_repo)

    logger = logging.getLogger("sync_portfolio")

    async with connector:
        if args.once:
            await _run_once(syncer, logger)
            return

        interval = timedelta(minutes=args.interval_minutes)
        logger.info(
            "Starting hourly snapshot loop: interval=%s minutes",
            args.interval_minutes,
        )
        while True:
            try:
                await _run_once(syncer, logger)
            except Exception as exc:
                logger.error("Snapshot failed: %s", exc, exc_info=True)
            await asyncio.sleep(interval.total_seconds())


def main() -> None:
    parser = argparse.ArgumentParser(description="Portfolio snapshot syncer")
    parser.add_argument("--once", action="store_true", help="Run a single snapshot")
    parser.add_argument(
        "--interval-minutes",
        type=int,
        default=60,
        help="Interval for snapshots in minutes (default 60)",
    )
    args = parser.parse_args()

    configure_logging()
    logger = logging.getLogger("sync_portfolio")

    try:
        asyncio.run(_run(args))
    except Exception as exc:
        logger.error("Portfolio snapshot sync failed: %s", exc, exc_info=True)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
