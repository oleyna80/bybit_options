"""Base collector for delta analytics services."""

from __future__ import annotations

import asyncio
import signal
from abc import ABC, abstractmethod
from datetime import datetime, timezone

from loguru import logger


class BaseCollector(ABC):
    """Abstract base class for delta collectors."""

    def __init__(self, interval_seconds: int = 10) -> None:
        self.interval_seconds = interval_seconds
        self.running = False
        self.stats = {
            "iterations": 0,
            "items_collected": 0,
            "items_saved": 0,
            "errors": 0,
            "start_time": None,
        }

    @abstractmethod
    async def collect_once(self) -> int:
        """Execute one collection cycle. Returns number of items saved."""
        raise NotImplementedError

    async def run(self) -> None:
        """Start infinite collection loop with graceful shutdown."""
        self.running = True
        self.stats["start_time"] = datetime.now(timezone.utc)

        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                loop.add_signal_handler(sig, lambda: asyncio.create_task(self.stop()))
            except NotImplementedError:
                pass

        logger.info(f"🚀 Starting {self.__class__.__name__}")

        while self.running:
            try:
                self.stats["iterations"] += 1
                saved = await self.collect_once()
                if saved:
                    self.stats["items_saved"] += int(saved)

                if self.stats["iterations"] % 10 == 0:
                    self._log_stats()

                await asyncio.sleep(self.interval_seconds)
            except asyncio.CancelledError:
                logger.info(f"⏹️ {self.__class__.__name__} cancelled")
                break
            except Exception as exc:
                self.stats["errors"] += 1
                logger.exception(f"❌ Error in {self.__class__.__name__}: {exc}")
                await asyncio.sleep(self.interval_seconds)

        logger.info(f"🛑 {self.__class__.__name__} stopped")

    async def stop(self) -> None:
        """Stop the collector gracefully."""
        if not self.running:
            return
        logger.info(f"⏹️ Stopping {self.__class__.__name__}...")
        self.running = False

    def _log_stats(self) -> None:
        """Log collection statistics including trades/min."""
        start_time = self.stats.get("start_time")
        if not start_time:
            return

        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
        rate = (self.stats["items_saved"] / elapsed * 60) if elapsed > 0 else 0

        logger.info(
            f"📊 {self.__class__.__name__} stats: "
            f"iterations={self.stats['iterations']}, "
            f"collected={self.stats['items_collected']}, "
            f"saved={self.stats['items_saved']}, "
            f"errors={self.stats['errors']}, "
            f"rate={rate:.1f} trades/min"
        )
