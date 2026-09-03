"""
Bybit Options Risk Engine — CLI entrypoint.

This module contains the canonical CLI implementation. Script entrypoints
(`apps/cli.py`, root `main.py`) should call `run()`.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys

from dotenv import load_dotenv

from bybit_options.orchestration.analysis_orchestrator import AnalysisOrchestrator
from bybit_options.reports.display_manager import DisplayManager
from bybit_options.services.bybit_connector import BybitConnector


def _ensure_utf8_stdout() -> None:
    # Keep Windows console output readable (emoji + Cyrillic).
    if getattr(sys.stdout, "encoding", None) != "utf-8" and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")


def setup_logging(level: str = "INFO") -> None:
    """Configure logging for the application."""
    log_level = getattr(logging, level.upper(), logging.INFO)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    logging.getLogger("aiohttp").setLevel(logging.WARNING)


async def main() -> None:
    """
    Main execution flow.

    1) Initialize services
    2) Run analysis
    3) Display + save results
    """
    _ensure_utf8_stdout()

    load_dotenv()

    api_key = os.getenv("BYBIT_API_KEY")
    api_secret = os.getenv("BYBIT_API_SECRET")

    if not api_key or not api_secret:
        print("❌ ERROR: BYBIT_API_KEY and BYBIT_API_SECRET must be set in .env")
        raise SystemExit(1)

    log_level = os.getenv("LOG_LEVEL", "INFO")
    setup_logging(log_level)

    logger = logging.getLogger(__name__)
    logger.info("🚀 Starting Bybit Options Risk Analysis")

    try:
        async with BybitConnector(
            api_key=api_key,
            api_secret=api_secret,
            testnet=False,
            rate_limit=50,
        ) as connector:
            orchestrator = AnalysisOrchestrator(connector)

            logger.info("Running full analysis...")
            portfolio = await orchestrator.run_full_analysis(fetch_enhanced_metrics=True)

            logger.info("Displaying results...\n")

            display = DisplayManager()

            all_positions = []
            for coin_risk in portfolio.coin_risks.values():
                all_positions.extend(coin_risk.positions)

            display.print_positions_table(all_positions)

            report_path = display.save_report_to_markdown(all_positions, portfolio)
            logger.info("💾 Report saved to: %s", report_path)
            logger.info("   (Use 'reports/latest_analysis.md' for AI analysis)")

            logger.info("✅ Analysis complete!")

    except KeyboardInterrupt:
        logger.info("⚠️  Analysis interrupted by user")
        raise SystemExit(0)

    except Exception as exc:
        logger.error("❌ Fatal error: %s", exc, exc_info=True)
        raise SystemExit(1)


def run() -> None:
    """Synchronous wrapper for script entrypoints."""
    asyncio.run(main())

