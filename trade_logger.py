"""
Trade Logger - SQL Integration (PostgreSQL)

ARCHITECTURE:
- Async queue for non-blocking writes
- Deduplication via execution ID tracking
- Batch inserts for efficiency
- Enrichment with market data (IV, underlying price)

SCHEMA:
trades table:
- id: UUID
- exec_id: VARCHAR (UNIQUE, for deduplication)
- timestamp: TIMESTAMP
- symbol: VARCHAR
- side: VARCHAR (Buy/Sell)
- size: DECIMAL
- exec_price: DECIMAL
- fee: DECIMAL
- role: VARCHAR (Maker/Taker)
- iv: DECIMAL
- underlying_price: DECIMAL
- strategy_tag: VARCHAR

USAGE:
    logger = TradeLogger(
        database_url="postgresql+asyncpg://user:password@localhost/trades_db",
    )

    await logger.initialize()
    await logger.log_trade(execution_data)
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Set, Any
from datetime import datetime, timezone
from dataclasses import dataclass
from collections import OrderedDict

from sqlalchemy import (
    Column,
    String,
    Numeric,
    DateTime,
    Boolean,
    Integer,
    Text,
    BigInteger,
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import select, insert
from sqlalchemy.dialects.postgresql import insert as pg_insert

from stream_manager import BybitStreamManager
from bybit_options.services.market_data_service import MarketDataService

logger = logging.getLogger(__name__)

# SQLAlchemy ORM setup
Base = declarative_base()


# ============================================================================
# DATABASE MODELS
# ============================================================================


class Trade(Base):
    """Trade execution record"""

    __tablename__ = "trades"

    exec_id = Column(String(100), primary_key=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    symbol = Column(String(50), nullable=False, index=True)
    side = Column(String(10), nullable=False)  # Buy/Sell
    size = Column(Numeric(18, 8), nullable=False)
    exec_price = Column(Numeric(18, 8), nullable=False)
    fee = Column(Numeric(18, 8), nullable=False)
    role = Column(String(10), nullable=False)  # Maker/Taker
    iv = Column(Numeric(10, 6), nullable=True)
    underlying_price = Column(Numeric(18, 8), nullable=True)
    strategy_tag = Column(String(100), nullable=True)
    # NEW: Order tracking (added 2025-12-30)
    order_id = Column(String(100), nullable=True)
    order_link_id = Column(String(100), nullable=True)
    order_type = Column(String(50), nullable=True)
    stop_order_type = Column(String(50), nullable=True)

    # NEW: Pricing
    mark_price = Column(Numeric(18, 8), nullable=True)
    mark_iv = Column(Numeric(10, 6), nullable=True)
    index_price = Column(Numeric(18, 8), nullable=True)
    trade_iv = Column(Numeric(10, 6), nullable=True)

    # NEW: Execution details
    exec_value = Column(Numeric(18, 8), nullable=True)
    closed_size = Column(Numeric(18, 8), nullable=True)
    order_qty = Column(Numeric(18, 8), nullable=True)
    order_price = Column(Numeric(18, 8), nullable=True)
    leaves_qty = Column(Numeric(18, 8), nullable=True)

    # NEW: Fees
    fee_rate = Column(Numeric(10, 6), nullable=True)
    fee_currency = Column(String(10), nullable=True)
    exec_fee_v2 = Column(Numeric(18, 8), nullable=True)
    extra_fees = Column(Text, nullable=True)

    # NEW: Other
    block_trade_id = Column(String(100), nullable=True)
    seq = Column(BigInteger, nullable=True)
    market_unit = Column(String(50), nullable=True)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class PositionEntry(Base):
    """Position entry tracking with IV (supports LONG and SHORT)"""

    __tablename__ = "position_entries"

    symbol = Column(String(50), primary_key=True)
    entry_price = Column(Numeric(18, 8), nullable=False)
    entry_iv = Column(Numeric(10, 6), nullable=True)  # Stored as fraction (0.52 = 52%)
    net_qty = Column(Numeric(18, 8), nullable=False)  # Can be negative (short)
    abs_qty = Column(Numeric(18, 8), nullable=False)  # For weighted averaging
    entry_time = Column(DateTime(timezone=True), nullable=False)
    last_update = Column(DateTime(timezone=True), nullable=False)
    fill_count = Column(Integer, default=1)
    position_side = Column(String(10), nullable=False)  # 'LONG' or 'SHORT'
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


# ============================================================================
# CONFIGURATION
# ============================================================================


@dataclass
class TradeLoggerConfig:
    """Configuration for trade logging"""

    # Database
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/trades"

    # Performance
    batch_size: int = 10  # Batch writes for efficiency
    flush_interval: float = 5.0  # Flush every 5 seconds
    max_queue_size: int = 1000

    # Deduplication
    dedup_cache_size: int = 10000  # Keep last 10k execution IDs


# ============================================================================
# TRADE LOGGER
# ============================================================================


class TradeLogger:
    """
    Async trade logger with SQL integration

    Features:
    - Non-blocking async queue
    - Batch writes for efficiency
    - Deduplication via execution ID
    - Market data enrichment (IV, underlying)
    - PostgreSQL storage
    """

    def __init__(
        self,
        market_data: Optional[MarketDataService] = None,
        stream_manager: Optional[BybitStreamManager] = None,
        config: Optional[TradeLoggerConfig] = None,
    ):
        self.market_data = market_data
        self.stream_manager = stream_manager
        self.config = config or TradeLoggerConfig()

        # Database
        self.engine = None
        self.async_session_maker = None

        # Async queue
        self.trade_queue: asyncio.Queue = asyncio.Queue(
            maxsize=self.config.max_queue_size
        )

        # Deduplication
        self.logged_execution_ids: OrderedDict[str, None] = OrderedDict()
        self._dedup_lock = asyncio.Lock()

        # Worker task
        self._worker_task: Optional[asyncio.Task] = None
        self._running = False

    # ========================================================================
    # INITIALIZATION
    # ========================================================================

    async def initialize(self):
        """
        Initialize database connection and create tables

        Steps:
        1. Create async engine
        2. Create all tables
        3. Start worker task
        """
        logger.info("🔌 Initializing Trade Logger...")

        try:
            # Create async engine
            self.engine = create_async_engine(
                self.config.database_url, echo=False, pool_pre_ping=True
            )

            self.async_session_maker = async_sessionmaker(
                self.engine, class_=AsyncSession, expire_on_commit=False
            )

            # Create tables
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            logger.info("✅ Database initialized")

            # Start worker
            self._running = True
            self._worker_task = asyncio.create_task(self._worker_loop())

            logger.info("✅ Trade Logger initialized")

        except Exception as e:
            logger.error(f"❌ Trade Logger initialization failed: {e}", exc_info=True)
            raise

    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down Trade Logger...")

        self._running = False

        # Wait for queue to drain
        logger.info(f"Waiting for {self.trade_queue.qsize()} trades to flush...")
        await self.trade_queue.join()

        # Cancel worker
        if self._worker_task and not self._worker_task.done():
            self._worker_task.cancel()
            await asyncio.gather(self._worker_task, return_exceptions=True)

        # Close database connection
        if self.engine:
            await self.engine.dispose()

        logger.info("✅ Trade Logger shutdown complete")

    # ========================================================================
    # LOGGING API
    # ========================================================================

    async def log_trade(self, execution_data: Dict[str, Any]):
        """
        Queue a trade for logging

        Args:
            execution_data: Raw execution data from Bybit WebSocket

        Format:
        {
            "execId": "xxx",
            "symbol": "BTC-26DEC25-95000-C",
            "side": "Buy",
            "execQty": "0.01",
            "execPrice": "1234.56",
            "execFee": "1.23",
            "execTime": "1234567890123"
        }
        """
        exec_id = execution_data.get("execId", "")

        # Deduplication
        async with self._dedup_lock:
            if exec_id in self.logged_execution_ids:
                self.logged_execution_ids.move_to_end(exec_id)
                logger.debug(f"Skipping duplicate execution: {exec_id}")
                return
            self.logged_execution_ids[exec_id] = None
            if len(self.logged_execution_ids) > self.config.dedup_cache_size:
                self.logged_execution_ids.popitem(last=False)

        try:
            # Add to queue (non-blocking)
            await asyncio.wait_for(self.trade_queue.put(execution_data), timeout=1.0)

        except asyncio.TimeoutError:
            async with self._dedup_lock:
                self.logged_execution_ids.pop(exec_id, None)
            logger.error(f"Queue full, dropping trade: {exec_id}")

        except Exception as e:
            async with self._dedup_lock:
                self.logged_execution_ids.pop(exec_id, None)
            logger.error(f"Failed to queue trade: {e}")

    # ========================================================================
    # WORKER LOOP
    # ========================================================================

    async def _worker_loop(self):
        """
        Background worker that processes trade queue

        Strategy:
        1. Collect trades for batch_size or flush_interval
        2. Enrich with market data
        3. Write batch to Google Sheets
        4. Retry on failures
        """
        logger.info("🔄 Trade logger worker started")

        batch: List[Dict] = []
        last_flush = time.time()

        while self._running:
            try:
                # Wait for trade with timeout
                try:
                    trade = await asyncio.wait_for(self.trade_queue.get(), timeout=1.0)
                    batch.append(trade)
                    self.trade_queue.task_done()

                except asyncio.TimeoutError:
                    pass  # Check flush interval

                # Flush conditions
                should_flush = len(batch) >= self.config.batch_size or (
                    batch and time.time() - last_flush >= self.config.flush_interval
                )

                if should_flush:
                    await self._flush_batch(batch)
                    batch = []
                    last_flush = time.time()

            except Exception as e:
                logger.error(f"Worker loop error: {e}", exc_info=True)
                await asyncio.sleep(1)

        # Final flush
        if batch:
            await self._flush_batch(batch)

        logger.info("Trade logger worker stopped")

    async def _flush_batch(self, batch: List[Dict]):
        """
        Write batch to database + update position entries

        Steps:
        1. Enrich trades with market data
        2. Create Trade objects
        3. Update position entries with entry IV
        """
        if not batch:
            return

        logger.info(f"📝 Flushing {len(batch)} trades to database")

        try:
            # Enrich trades
            enriched = await self._enrich_trades(batch)

            # Insert to database
            async with self.async_session_maker() as session:
                for trade_data in enriched:
                    # Create Trade object
                    trade = Trade(
                        exec_id=trade_data["execId"],
                        timestamp=(
                            datetime.fromtimestamp(
                                int(trade_data.get("execTime", 0)) / 1000,
                                tz=timezone.utc,
                            )
                            if trade_data.get("execTime")
                            else datetime.now(timezone.utc)
                        ),
                        symbol=trade_data.get("symbol", ""),
                        side=trade_data.get("side", ""),
                        size=float(trade_data.get("execQty", 0)),
                        exec_price=float(trade_data.get("execPrice", 0)),
                        fee=float(trade_data.get("execFee", 0)),
                        role="Maker" if trade_data.get("isMaker") else "Taker",
                        iv=(
                            float(trade_data.get("_iv", 0))
                            if trade_data.get("_iv")
                            else None
                        ),
                        underlying_price=(
                            float(trade_data.get("_underlying_price", 0))
                            if trade_data.get("_underlying_price")
                            else None
                        ),
                        strategy_tag=trade_data.get("strategy_tag", ""),
                    )
                    session.add(trade)

                # Update position entries
                await self._update_position_entries(session, enriched)

                # Commit batch
                await session.commit()

            logger.info(f"✅ Flushed {len(batch)} trades + updated position entries")

        except Exception as e:
            logger.error(f"❌ Failed to flush batch: {e}", exc_info=True)
            # Continue even if flush fails

    async def _update_position_entries(self, session: AsyncSession, trades: List[Dict]):
        """
        Update position entries with weighted average IV

        SUPPORTS BOTH LONG AND SHORT POSITIONS:
        - LONG position: opened by Buy, net_qty > 0
        - SHORT position: opened by Sell, net_qty < 0

        Logic:
        - signed_qty: Buy = +qty, Sell = -qty
        - net_qty = cumulative signed_qty
        - If position flips sign (long→short or short→long): close old entry, open new
        - Weighted average IV calculated only for fills in same direction

        IV Storage Convention:
        - Store as fraction (0.52 = 52%)
        - Display as percentage (52.0%)

        Entry IV Behavior:
        - Partial close: entry_iv unchanged (represents IV at initial entry)
        - Partial add: entry_iv recalculated as weighted average
        - Position flip: old entry deleted, new entry created with new IV
        """
        for trade in trades:
            try:
                symbol = trade.get("symbol", "")
                side = trade.get("side", "")  # Buy or Sell
                qty = float(trade.get("execQty", 0))
                price = float(trade.get("execPrice", 0))
                iv = float(trade.get("_iv", 0)) if trade.get("_iv") else None
                exec_time = (
                    datetime.fromtimestamp(
                        int(trade.get("execTime", 0)) / 1000, tz=timezone.utc
                    )
                    if trade.get("execTime")
                    else datetime.now(timezone.utc)
                )

                # Skip if no IV available
                if iv is None or iv == 0:
                    logger.warning(f"Skipping position entry for {symbol}: No IV data")
                    continue

                # Convert IV to fraction if needed
                if iv > 1.0:
                    iv = iv / 100.0

                # Calculate signed quantity
                signed_qty = qty if side == "Buy" else -qty

                # Query existing position
                result = await session.execute(
                    select(PositionEntry).where(PositionEntry.symbol == symbol)
                )
                existing = result.scalar_one_or_none()

                if existing:
                    old_net_qty = float(existing.net_qty)
                    new_net_qty = old_net_qty + signed_qty

                    # Case 1: Position flip (crosses zero)
                    if (old_net_qty > 0 and new_net_qty < 0) or (
                        old_net_qty < 0 and new_net_qty > 0
                    ):
                        await session.delete(existing)

                        if abs(new_net_qty) > 1e-8:  # Not exactly zero
                            new_side = "LONG" if new_net_qty > 0 else "SHORT"
                            new_entry = PositionEntry(
                                symbol=symbol,
                                entry_price=price,
                                entry_iv=iv,
                                net_qty=new_net_qty,
                                abs_qty=abs(new_net_qty),
                                entry_time=exec_time,
                                last_update=exec_time,
                                fill_count=1,
                                position_side=new_side,
                            )
                            session.add(new_entry)
                            logger.info(
                                f"Position flip {symbol}: {old_net_qty:.4f}→{new_net_qty:.4f} "
                                f"(closed old, opened {new_side} @ IV {iv*100:.2f}%)"
                            )
                        else:
                            logger.info(f"Position closed exactly {symbol}")

                    # Case 2: Position closed
                    elif abs(new_net_qty) < 1e-8:
                        await session.delete(existing)
                        logger.info(f"Closed position {symbol}, removed entry")

                    # Case 3: Position reduced (same direction)
                    elif abs(new_net_qty) < abs(old_net_qty):
                        existing.net_qty = new_net_qty
                        existing.abs_qty = abs(new_net_qty)
                        existing.last_update = exec_time
                        logger.debug(
                            f"Reduced {symbol}: qty {old_net_qty:.4f}→{new_net_qty:.4f}"
                        )

                    # Case 4: Position increased (same direction)
                    else:
                        old_abs_qty = float(existing.abs_qty)
                        old_iv = float(existing.entry_iv) if existing.entry_iv else 0
                        old_price = float(existing.entry_price)

                        new_abs_qty = abs(new_net_qty)
                        new_avg_iv = (old_abs_qty * old_iv + qty * iv) / new_abs_qty
                        new_avg_price = (
                            old_abs_qty * old_price + qty * price
                        ) / new_abs_qty

                        existing.net_qty = new_net_qty
                        existing.abs_qty = new_abs_qty
                        existing.entry_iv = new_avg_iv
                        existing.entry_price = new_avg_price
                        existing.last_update = exec_time
                        existing.fill_count += 1

                        logger.debug(
                            f"Increased {symbol}: qty {old_net_qty:.4f}→{new_net_qty:.4f}, "
                            f"IV {old_iv*100:.2f}%→{new_avg_iv*100:.2f}%"
                        )

                else:
                    if abs(signed_qty) > 1e-8:
                        position_side = "LONG" if signed_qty > 0 else "SHORT"
                        new_entry = PositionEntry(
                            symbol=symbol,
                            entry_price=price,
                            entry_iv=iv,
                            net_qty=signed_qty,
                            abs_qty=abs(signed_qty),
                            entry_time=exec_time,
                            last_update=exec_time,
                            fill_count=1,
                            position_side=position_side,
                        )
                        session.add(new_entry)
                        logger.info(
                            f"New position entry: {symbol} {position_side} qty={signed_qty:.4f} "
                            f"IV={iv*100:.2f}%"
                        )

            except Exception as e:
                logger.error(
                    f"Failed to update position entry for {trade.get('symbol')}: {e}"
                )

    async def _enrich_trades(self, trades: List[Dict]) -> List[Dict]:
        """
        Enrich trades with market data (IV, underlying price)

        Returns:
            List of enriched trade dicts
        """
        enriched = []

        for trade in trades:
            try:
                symbol = trade.get("symbol", "")

                # Get ticker data for IV
                iv = None
                underlying_price = None

                if self.stream_manager:
                    ticker = self.stream_manager.get_ticker(symbol)
                    if ticker:
                        iv = float(ticker.get("markIv", 0)) or None

                # Get underlying price
                if symbol:
                    base_coin = symbol.split("-")[0] if "-" in symbol else symbol[:3]

                    if self.stream_manager:
                        # Try to get from perpetual ticker
                        perp_symbol = f"{base_coin}USDT"
                        perp_ticker = self.stream_manager.get_ticker(perp_symbol)
                        if perp_ticker:
                            underlying_price = (
                                float(
                                    perp_ticker.get("lastPrice")
                                    or perp_ticker.get("markPrice")
                                    or 0
                                )
                                or None
                            )

                # Add enrichment
                enriched_trade = trade.copy()
                enriched_trade["_iv"] = iv
                enriched_trade["_underlying_price"] = underlying_price

                enriched.append(enriched_trade)

            except Exception as e:
                logger.error(f"Failed to enrich trade: {e}")
                enriched.append(trade)  # Add without enrichment

        return enriched

    def _format_row(self, trade: Dict) -> List[Any]:
        """
        Format trade dict (deprecated - kept for reference)

        Now trades are inserted directly via ORM
        """
        pass

    async def _write_rows_with_retry(self, rows: List[List[Any]]):
        """
        Deprecated - SQL handles writes directly without retry logic
        """
        pass

    # ========================================================================
    # UTILITIES
    # ========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """Get logging statistics"""
        return {
            "queue_size": self.trade_queue.qsize(),
            "logged_count": len(self.logged_execution_ids),
            "running": self._running,
        }


# ============================================================================
# INTEGRATION EXAMPLE
# ============================================================================


async def main():
    """Example: Integrate TradeLogger with LiveStateKeeper"""
    import os
    from dotenv import load_dotenv
    from bybit_options.services.bybit_connector import BybitConnector

    load_dotenv()

    api_key = os.getenv("BYBIT_API_KEY")
    api_secret = os.getenv("BYBIT_API_SECRET")
    db_url = os.getenv(
        "DATABASE_URL", "postgresql+asyncpg://postgres:password@localhost:5432/trades"
    )

    # Initialize services
    connector = BybitConnector(api_key, api_secret)
    await connector._init_session()

    stream_manager = BybitStreamManager(api_key, api_secret)
    market_data = MarketDataService(connector)

    # Create trade logger
    trade_logger = TradeLogger(
        market_data=market_data,
        stream_manager=stream_manager,
        config=TradeLoggerConfig(database_url=db_url),
    )

    try:
        # Initialize trade logger
        try:
            await trade_logger.initialize()
            logger.info("✅ Trade logging ENABLED")
        except Exception as e:
            logger.error(
                f"⚠️  Trade logger init failed: {e}. Continuing without logging."
            )
            trade_logger = None

        # Start stream manager
        await stream_manager.start()

        # Subscribe to execution reports
        # Note: Bybit requires explicit subscription to "execution" topic
        await stream_manager.private_client.send(
            {"op": "subscribe", "args": ["execution"]}
        )
        logger.info("✅ Subscribed to execution reports")

        # Simulate trade logging
        mock_execution = {
            "execId": f"test_{int(time.time() * 1000)}",
            "symbol": "BTC-26DEC25-95000-C",
            "side": "Buy",
            "execQty": "0.01",
            "execPrice": "1234.56",
            "execFee": "1.23",
            "isMaker": False,
            "execTime": str(int(time.time() * 1000)),
        }

        if trade_logger:
            await trade_logger.log_trade(mock_execution)
            logger.info("📝 Test trade logged")

        # Wait for flush
        await asyncio.sleep(6)

        # Check stats
        if trade_logger:
            stats = trade_logger.get_stats()
            print(f"Logger stats: {stats}")

    except KeyboardInterrupt:
        print("\n⚠️  Shutting down...")

    finally:
        if trade_logger:
            await trade_logger.shutdown()
        await stream_manager.stop()
        await connector.close()

        print("✅ Shutdown complete")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    asyncio.run(main())
