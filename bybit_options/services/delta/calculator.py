"""
Delta Calculator Service
========================
Aggregates trade and orderbook data into Delta Metrics.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional
from decimal import Decimal
from loguru import logger
from sqlalchemy import select, func

from .database import LargeTrade, OrderbookSnapshot, DeltaMetrics

class DeltaCalculator:
    """
    Periodic service to compute Cumulative Volume Delta (CVD) and OB Imbalances.
    Reads from 'large_trades' and 'orderbook_snapshots'.
    Writes to 'delta_metrics'.
    """

    def __init__(self, session_factory):
        self.session_factory = session_factory
        self._running = False
        self.intervals = {
            '1m': 60,
            '5m': 300
        }

    async def start(self):
        """Start the background calculation loop."""
        logger.info("Starting DeltaCalculator service")
        self._running = True
        asyncio.create_task(self._calculation_loop())

    async def stop(self):
        self._running = False

    async def calculate_interval(self, symbol: str, interval: str):
        """
        Compute metrics for the last closed interval.
        """
        seconds = self.intervals.get(interval)
        if not seconds: return

        now = datetime.now(timezone.utc)
        start_time = now - timedelta(seconds=seconds)
        
        async with self.session_factory() as session:
            # 1. Aggressive Delta
            # Sum Buy Volume
            buy_stmt = select(func.sum(LargeTrade.quantity)).where(
                LargeTrade.symbol == symbol,
                LargeTrade.timestamp >= start_time,
                LargeTrade.side == 'Buy'
            )
            buy_res = await session.execute(buy_stmt)
            buy_vol = buy_res.scalar() or Decimal('0')

            # Sum Sell Volume
            sell_stmt = select(func.sum(LargeTrade.quantity)).where(
                LargeTrade.symbol == symbol,
                LargeTrade.timestamp >= start_time,
                LargeTrade.side == 'Sell'
            )
            sell_res = await session.execute(sell_stmt)
            sell_vol = sell_res.scalar() or Decimal('0')
            
            # Count
            count_stmt = select(func.count()).where(
                LargeTrade.symbol == symbol,
                LargeTrade.timestamp >= start_time
            )
            count_res = await session.execute(count_stmt)
            trade_count = count_res.scalar() or 0

            delta = buy_vol - sell_vol

            # 2. Orderbook Imbalance (Average over interval)
            ob_stmt = select(func.avg(OrderbookSnapshot.imbalance)).where(
                OrderbookSnapshot.symbol == symbol,
                OrderbookSnapshot.timestamp >= start_time
            )
            ob_res = await session.execute(ob_stmt)
            avg_imbalance = ob_res.scalar()

            # 3. Store Metrics
            metric = DeltaMetrics(
                timestamp=now,
                symbol=symbol,
                interval=interval,
                filtered_buy_volume=buy_vol,
                filtered_sell_volume=sell_vol,
                filtered_delta=delta,
                large_trades_count=trade_count,
                avg_imbalance=avg_imbalance
            )
            session.add(metric)
            await session.commit()
            
            logger.debug(f"Computed {interval} Delta for {symbol}: {delta}, Imb: {avg_imbalance}")

    async def _calculation_loop(self):
        """
        Main loop.
        Triggers calculation for all symbols every 10 seconds.
        """
        logger.info("Delta Calculation Loop Started")
        while self._running:
            # TODO: dynamic symbol list. process all known?
            # For MVP, assume ['BTCUSDT']
            symbols = ['BTCUSDT']
            
            for sym in symbols:
                await self.calculate_interval(sym, '1m')
                # 5m calculation might be redundant every 10s, but safe for MVP
                # ideally check if 5m boundary crossed

            await asyncio.sleep(10)
