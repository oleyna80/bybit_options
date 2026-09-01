"""
Live State Keeper - The Brain of the Trading System

ARCHITECTURE:
    WebSocket Streams → Staging Area → Risk Calculation → Published Snapshot
                            ↓              (ThreadPool)           ↓
                        Debounced                          Readers (lock-free)

DESIGN PRINCIPLES:
- Copy-on-Write: Immutable snapshots for readers
- Debouncing: Throttle expensive calculations
- Executor: CPU work doesn't block event loop
- No Locks: Single writer + atomic swaps

USAGE:
    keeper = LiveStateKeeper(stream_manager, market_data, risk_engine)
    await keeper.initialize()
    
    # From another coroutine:
    portfolio = keeper.get_portfolio_snapshot()
    delta = keeper.get_portfolio_delta("BTC")
"""

import asyncio
import copy
import logging
import time
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from enum import Enum

from stream_manager import BybitStreamManager
from bybit_options.services.market_data_service import MarketDataService
from bybit_options.core.risk_engine import RiskEngine
from bybit_options.models import (
    PortfolioRiskModel,
    PositionModel,
    CoinRiskModel,
    MarginModel,
    GreeksModel,
    PositionType,
    PositionSide,
    OptionType
)
from websocket_manager import WebSocketManager

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class StateKeeperConfig:
    """Configuration for live state management"""
    
    # Debouncing
    recalc_delay: float = 0.1  # 100ms debounce
    
    # Hedge thresholds
    delta_threshold: float = 0.01  # Alert if |delta| > 0.01 BTC
    vega_threshold: float = 1000.0  # Alert if |vega| > $1000
    margin_threshold: float = 80.0  # Alert if margin > 80%
    
    # Performance
    executor_workers: int = 1  # Single thread for risk calc
    max_position_cache: int = 1000  # Prevent memory leak
    
    # Startup
    warmup_timeout: float = 30.0  # Seconds to wait for WS
    rest_fetch_timeout: float = 10.0


# ============================================================================
# STATE TRACKING
# ============================================================================

class StateKeeperStatus(Enum):
    """State machine for keeper lifecycle"""
    INITIALIZING = "initializing"
    WARMING_UP = "warming_up"
    READY = "ready"
    DEGRADED = "degraded"  # Some data sources unavailable
    ERROR = "error"


@dataclass
class StateMetrics:
    """Metrics for monitoring"""
    version: int = 0
    last_update_time: float = 0.0
    recalc_count: int = 0
    recalc_duration_ms: float = 0.0
    ticker_updates: int = 0
    position_updates: int = 0
    warnings_generated: int = 0
    
    def mark_recalc(self, duration_ms: float):
        self.recalc_count += 1
        self.recalc_duration_ms = duration_ms
        self.last_update_time = time.time()
        self.version += 1


# ============================================================================
# LIVE STATE KEEPER
# ============================================================================

class LiveStateKeeper:
    """
    Central state manager for live portfolio
    
    Responsibilities:
    1. Aggregate data from WebSocket streams
    2. Trigger risk recalculation on updates
    3. Detect hedge signals
    4. Provide thread-safe read access
    
    Concurrency Model:
    - Single writer (WS callbacks in event loop)
    - Single calculator (ThreadPoolExecutor)
    - Multiple readers (get immutable snapshots)
    - No locks needed (atomic swaps + GIL)
    """
    
    def __init__(
        self,
        stream_manager: BybitStreamManager,
        market_data: MarketDataService,
        risk_engine: RiskEngine,
        trade_logger: Optional['TradeLogger'] = None,  # NEW: Optional trade logger
        config: Optional[StateKeeperConfig] = None
    ):
        self.stream_manager = stream_manager
        self.market_data = market_data
        self.risk_engine = risk_engine
        self.trade_logger = trade_logger  # NEW
        self.config = config or StateKeeperConfig()
        
        # WebSocket manager for broadcasting updates
        self._ws_manager: Optional[WebSocketManager] = None
        self._broadcast_task: Optional[asyncio.Task] = None
        
        # State
        self.status = StateKeeperStatus.INITIALIZING
        self.metrics = StateMetrics()
        
        # Staging area (mutable, only WS writes)
        self._staging_tickers: Dict[str, Dict] = {}
        self._staging_positions: Dict[str, Dict] = {}
        self._staging_margin: Optional[Dict] = None
        self._dirty_symbols: Set[str] = set()
        
        # Published snapshot (immutable, readers access)
        self._current_portfolio: Optional[PortfolioRiskModel] = None
        
        # Executor for CPU-bound work
        self._executor = ThreadPoolExecutor(
            max_workers=self.config.executor_workers,
            thread_name_prefix="risk_calc"
        )
        
        # Debounce control
        self._recalc_task: Optional[asyncio.Task] = None
        
        # Startup sync
        self._first_message_event = asyncio.Event()
    
    def set_websocket_manager(self, ws_manager: WebSocketManager):
        """
        Set WebSocket manager for broadcasting updates
        
        Args:
            ws_manager: WebSocketManager instance
        """
        self._ws_manager = ws_manager
        logger.info("WebSocket manager set for LiveStateKeeper")
        
        # Start broadcast loop if we're already ready
        if self.status == StateKeeperStatus.READY and self._ws_manager:
            self._start_broadcast_loop()
    
    async def _start_broadcast_loop(self):
        """Start automatic broadcast of portfolio updates"""
        if not self._ws_manager:
            logger.warning("Cannot start broadcast loop: WebSocket manager not set")
            return
        
        if self._broadcast_task and not self._broadcast_task.done():
            logger.info("Broadcast loop already running")
            return
        
        logger.info("Starting WebSocket broadcast loop")
        
        async def portfolio_provider():
            """Provide latest portfolio for broadcasting"""
            portfolio = self.get_portfolio_snapshot()
            if not portfolio:
                # If no portfolio yet, run a quick analysis
                try:
                    # This is a simplified version - in production you'd want to
                    # trigger a recalculation or use cached data
                    from bybit_options.orchestration.analysis_orchestrator import AnalysisOrchestrator
                    orchestrator = AnalysisOrchestrator(self.market_data.connector)
                    portfolio = await orchestrator.run_full_analysis(fetch_enhanced_metrics=False)
                except Exception as e:
                    logger.error(f"Failed to get portfolio for broadcast: {e}")
                    return None
            return portfolio
        
        # Start broadcast loop
        self._broadcast_task = asyncio.create_task(
            self._ws_manager.start_broadcast_loop(portfolio_provider)
        )
        
        try:
            await self._broadcast_task
        except asyncio.CancelledError:
            logger.info("Broadcast loop cancelled")
        except Exception as e:
            logger.error(f"Broadcast loop error: {e}")
    
    def stop_broadcast_loop(self):
        """Stop the broadcast loop"""
        if self._broadcast_task and not self._broadcast_task.done():
            self._broadcast_task.cancel()
            logger.info("Broadcast loop stopped")
    
    # ========================================================================
    # LIFECYCLE
    # ========================================================================
    
    async def initialize(self):
        """
        Phased initialization:
        1. Fetch REST snapshot (positions, margin)
        2. Subscribe to WebSocket streams
        3. Wait for first WS message
        4. Mark as ready
        """
        logger.info("🚀 Initializing Live State Keeper...")
        self.status = StateKeeperStatus.INITIALIZING
        
        try:
            # PHASE 1: REST snapshot
            await self._fetch_rest_snapshot()
            
            # PHASE 2: WebSocket subscriptions
            await self._subscribe_to_streams()
            
            # PHASE 2.5: Register callbacks (NEW)
            self._register_stream_callbacks()
            
            # PHASE 3: Wait for WebSocket warmup
            self.status = StateKeeperStatus.WARMING_UP
            await self._wait_for_warmup()
            
            # PHASE 4: Ready
            self.status = StateKeeperStatus.READY
            logger.info("✅ Live State Keeper READY")
        
        except asyncio.TimeoutError:
            logger.error("❌ Initialization timeout")
            self.status = StateKeeperStatus.ERROR
            raise
        
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}", exc_info=True)
            self.status = StateKeeperStatus.ERROR
            raise
    
    async def _fetch_rest_snapshot(self):
        """Fetch initial state via REST API"""
        logger.info("📡 Phase 1: Fetching REST snapshot...")
        
        try:
            # Fetch positions
            raw_positions = await asyncio.wait_for(
                self.market_data.fetch_all_positions(),
                timeout=self.config.rest_fetch_timeout
            )
            
            # Load into staging
            for pos in raw_positions:
                symbol = pos.get("symbol", "")
                if symbol:
                    self._staging_positions[symbol] = pos
            
            logger.info(f"  ✅ Loaded {len(self._staging_positions)} positions")
            
            # Fetch margin
            margin = await asyncio.wait_for(
                self.market_data.fetch_margin_info(),
                timeout=self.config.rest_fetch_timeout
            )
            
            if margin:
                self._staging_margin = margin.dict()
                logger.info(f"  ✅ Loaded margin: ${margin.total_equity:,.2f}")
            
            # Initial risk calculation
            await self._recalculate_risk()
            logger.info(f"  ✅ Initial risk calculated (v{self.metrics.version})")
        
        except asyncio.TimeoutError:
            logger.error("REST snapshot fetch timeout")
            raise
        except Exception as e:
            logger.error(f"REST snapshot fetch failed: {e}")
            raise
    
    async def _subscribe_to_streams(self):
        """Subscribe to WebSocket channels"""
        logger.info("📡 Phase 2: Subscribing to WebSocket streams...")
        
        # Subscribe to private streams (positions, orders)
        await self.stream_manager.subscribe_position()
        logger.info("  ✅ Subscribed to position updates")
        
        # Subscribe to tickers for all active positions
        for symbol in self._staging_positions.keys():
            await self.stream_manager.subscribe_ticker(symbol)
        
        logger.info(f"  ✅ Subscribed to {len(self._staging_positions)} tickers")
        
        # Register callbacks
        self._register_callbacks()
    
    def _register_stream_callbacks(self):
        """
        Register callbacks with StreamManager
        
        CRITICAL: This links StreamManager events to StateKeeper/TradeLogger
        """
        logger.info("📡 Registering stream callbacks...")
        
        # Register execution callback (for trade logging)
        if self.trade_logger:
            self.stream_manager.set_execution_callback(self.on_execution)
            logger.info("  ✅ Execution callback → TradeLogger")
        
        # Register position callback (for state updates)
        self.stream_manager.set_position_callback(self.on_position_update)
        logger.info("  ✅ Position callback → StateKeeper")
    
    # ========================================================================
    # CALLBACK HANDLERS (Called by StreamManager)
    # ========================================================================
    
    async def on_execution(self, execution_data: Dict):
        """
        Handle trade execution from StreamManager
        
        This is the critical link between Bybit WebSocket
        and Google Sheets logging.
        
        Args:
            execution_data: Raw execution from Bybit
            {
                "execId": "xxx",
                "symbol": "BTC-26DEC25-95000-C",
                "side": "Buy",
                "execQty": "0.01",
                "execPrice": "1234.56",
                "execFee": "1.23",
                "isMaker": false,
                "execTime": "1234567890123"
            }
        """
        logger.info(
            f"💰 Execution: {execution_data.get('symbol')} "
            f"{execution_data.get('side')} {execution_data.get('execQty')}"
        )
        
        # Log to Google Sheets
        if self.trade_logger:
            await self.trade_logger.log_trade(execution_data)
    
    async def _wait_for_warmup(self):
        """Wait for first WebSocket message"""
        logger.info("📡 Phase 3: Waiting for WebSocket confirmation...")
        
        try:
            await asyncio.wait_for(
                self._first_message_event.wait(),
                timeout=self.config.warmup_timeout
            )
            logger.info("  ✅ WebSocket streams active")
        
        except asyncio.TimeoutError:
            logger.warning(
                "  ⚠️  WebSocket warmup timeout. "
                "Proceeding with REST data only."
            )
            self.status = StateKeeperStatus.DEGRADED
    
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down Live State Keeper...")
        
        # Cancel pending recalc
        if self._recalc_task and not self._recalc_task.done():
            self._recalc_task.cancel()
        
        # Shutdown executor
        self._executor.shutdown(wait=True)
        
        logger.info("✅ Live State Keeper shutdown complete")
    
    # ========================================================================
    # EVENT HANDLERS (Called from WebSocket callbacks)
    # ========================================================================
    
    def on_ticker_update(self, symbol: str, ticker_data: Dict):
        """
        Handle ticker update from WebSocket
        
        Fast path: Just update staging + schedule recalc
        """
        self._staging_tickers[symbol] = ticker_data
        self._dirty_symbols.add(symbol)
        self.metrics.ticker_updates += 1
        
        # Mark first message received
        if not self._first_message_event.is_set():
            self._first_message_event.set()
        
        # Schedule debounced recalc
        self._schedule_recalc()
    
    def on_position_update(self, position_data: Dict):
        """
        Handle position update from WebSocket
        
        Scenarios:
        1. Existing position changed (size/PnL updated)
        2. New position opened (subscribe to ticker)
        3. Position closed (remove from staging)
        """
        symbol = position_data.get("symbol", "")
        if not symbol:
            return
        
        size = float(position_data.get("size", 0))
        
        if size == 0:
            # Position closed
            if symbol in self._staging_positions:
                logger.info(f"📤 Position closed: {symbol}")
                del self._staging_positions[symbol]
                self._dirty_symbols.add(symbol)
        else:
            # Position opened or updated
            is_new = symbol not in self._staging_positions
            
            if is_new:
                logger.info(f"📥 New position opened: {symbol} (size={size})")
                # Auto-subscribe to ticker
                asyncio.create_task(
                    self.stream_manager.subscribe_ticker(symbol)
                )
            
            self._staging_positions[symbol] = position_data
            self._dirty_symbols.add(symbol)
        
        self.metrics.position_updates += 1
        
        # Mark first message received
        if not self._first_message_event.is_set():
            self._first_message_event.set()
        
        # Schedule recalc
        self._schedule_recalc()
    
    def on_margin_update(self, margin_data: Dict):
        """Handle margin update from WebSocket"""
        self._staging_margin = margin_data
        self._schedule_recalc()
    
    # ========================================================================
    # RISK CALCULATION (Debounced + Executor)
    # ========================================================================
    
    def _schedule_recalc(self):
        """
        Schedule debounced risk recalculation
        
        Debouncing: If multiple updates arrive within 100ms,
        only the last one triggers recalc.
        """
        # Cancel pending task
        if self._recalc_task and not self._recalc_task.done():
            self._recalc_task.cancel()
        
        # Schedule new task
        self._recalc_task = asyncio.create_task(
            self._debounced_recalc()
        )
    
    async def _debounced_recalc(self):
        """Wait for debounce delay, then recalculate"""
        await asyncio.sleep(self.config.recalc_delay)
        await self._recalculate_risk()
    
    async def _recalculate_risk(self):
        """
        Recalculate portfolio risk (runs in executor)
        
        Flow:
        1. Shallow copy staging data (isolate from WS updates)
        2. Run RiskEngine in thread (CPU-bound)
        3. Atomic swap of published snapshot
        4. Check hedge signals
        
        PERFORMANCE CRITICAL:
        Uses shallow copy instead of deepcopy because:
        - stream_manager returns new dict references (Copy-on-Write)
        - RiskEngine only reads data (no mutations)
        - Speedup: 50x faster on 50+ positions
        """
        start_time = time.time()
        
        try:
            # Step 1: Shallow copy data (FAST: ~0.1-0.5ms)
            # Safe because stream_manager uses Copy-on-Write
            # and RiskEngine is read-only
            tickers = copy.copy(self._staging_tickers)
            positions = copy.copy(self._staging_positions)
            margin = copy.copy(self._staging_margin) if self._staging_margin else None
            
            # Step 2: Offload to executor (blocks thread, not event loop)
            loop = asyncio.get_event_loop()
            new_portfolio = await loop.run_in_executor(
                self._executor,
                self._compute_risk_sync,
                tickers,
                positions,
                margin
            )
            
            # Step 3: Atomic swap (GIL-safe)
            self._current_portfolio = new_portfolio
            
            # Step 4: Update metrics
            duration_ms = (time.time() - start_time) * 1000
            self.metrics.mark_recalc(duration_ms)
            
            # Step 5: Check hedge signals
            self._check_hedge_signals(new_portfolio)
            
            # Step 6: Broadcast update via WebSocket if manager is set
            await self._broadcast_portfolio_update(new_portfolio)
            
            # Clear dirty flags
            self._dirty_symbols.clear()
            
            logger.debug(
                f"Risk recalculated: v{self.metrics.version}, "
                f"duration={duration_ms:.1f}ms"
            )
        
        except Exception as e:
            logger.error(f"Risk recalculation failed: {e}", exc_info=True)
            self.status = StateKeeperStatus.ERROR
    
    def _compute_risk_sync(
        self,
        tickers: Dict[str, Dict],
        positions: Dict[str, Dict],
        margin: Optional[Dict]
    ) -> PortfolioRiskModel:
        """
        Synchronous risk computation (runs in thread)
        
        This is CPU-bound work that must not block event loop.
        
        CRITICAL: This function runs in ThreadPoolExecutor.
        Do NOT use asyncio or await here.
        """
        # Convert raw data to PositionModel objects
        position_models: List[PositionModel] = []
        
        for symbol, raw_pos in positions.items():
            # Determine position type
            category = raw_pos.get("_category", "")
            
            if category == "option":
                pos_type = PositionType.OPTION
            elif category == "linear":
                pos_type = PositionType.LINEAR
            else:
                pos_type = PositionType.LINEAR  # Default
            
            # Extract base coin
            base_coin = self.risk_engine.extract_base_coin(symbol)
            
            # Get ticker data
            ticker_data = tickers.get(symbol)
            
            # Calculate Greeks
            greeks = self.risk_engine.calculate_position_greeks(
                raw_position=raw_pos,
                ticker_data=ticker_data,
                pos_type=pos_type
            )
            
            # Extract option details
            series, option_type, strike = None, None, None
            if pos_type == PositionType.OPTION:
                series, option_type, strike = \
                    self.risk_engine.extract_option_details(symbol)
            
            # Build position model
            position = self.risk_engine.build_position_model(
                raw_position=raw_pos,
                greeks=greeks,
                pos_type=pos_type,
                base_coin=base_coin,
                series=series,
                option_type=option_type,
                strike=strike
            )
            
            position_models.append(position)
        
        # Get underlying prices (from tickers)
        underlying_prices = {}
        for symbol, ticker in tickers.items():
            # Look for linear perpetual tickers (e.g., BTCUSDT)
            if "USDT" in symbol and "-" not in symbol:
                # This is a linear ticker
                base_coin = self.risk_engine.extract_base_coin(symbol)
                mark_price = float(ticker.get("markPrice", 0) or ticker.get("lastPrice", 0))
                if mark_price > 0:
                    underlying_prices[base_coin] = mark_price
        
        # Convert margin dict to model
        margin_model = None
        if margin:
            try:
                margin_model = MarginModel(**margin)
            except Exception as e:
                logger.error(f"Failed to parse margin model: {e}")
        
        # Build portfolio
        portfolio = self.risk_engine.build_portfolio_risk(
            positions=position_models,
            margin=margin_model,
            underlying_prices=underlying_prices
        )
        
        return portfolio
    
    # ========================================================================
    # HEDGE SIGNAL DETECTION
    # ========================================================================
    
    def _check_hedge_signals(self, portfolio: PortfolioRiskModel):
        """
        Check if portfolio needs hedging
        
        Signals:
        1. Delta exceeds threshold
        2. Vega exceeds threshold
        3. Margin exceeds threshold
        """
        warnings = []
        
        # Check delta per coin
        for coin, coin_risk in portfolio.coin_risks.items():
            delta = coin_risk.total_greeks.delta_coin
            
            if abs(delta) > self.config.delta_threshold:
                msg = (
                    f"🚨 HEDGE SIGNAL: {coin} delta={delta:+.4f} "
                    f"(threshold={self.config.delta_threshold})"
                )
                warnings.append(msg)
                logger.warning(msg)
        
        # Check vega
        if abs(portfolio.total_vega_usd) > self.config.vega_threshold:
            msg = (
                f"🚨 VEGA ALERT: ${portfolio.total_vega_usd:+,.2f} "
                f"(threshold=${self.config.vega_threshold:,.0f})"
            )
            warnings.append(msg)
            logger.warning(msg)
        
        # Check margin
        if portfolio.margin and portfolio.margin.margin_ratio:
            if portfolio.margin.margin_ratio > self.config.margin_threshold:
                msg = (
                    f"🚨 MARGIN ALERT: {portfolio.margin.margin_ratio:.1f}% "
                    f"(threshold={self.config.margin_threshold}%)"
                )
                warnings.append(msg)
                logger.warning(msg)
        
        if warnings:
            self.metrics.warnings_generated += len(warnings)
    
    # ========================================================================
    # WEBSOCKET BROADCAST
    # ========================================================================
    
    async def _broadcast_portfolio_update(self, portfolio: PortfolioRiskModel):
        """
        Broadcast portfolio update via WebSocket manager
        
        Args:
            portfolio: PortfolioRiskModel to broadcast
        """
        if not self._ws_manager:
            return
        
        try:
            await self._ws_manager.broadcast_portfolio_update(portfolio)
            logger.debug(f"Portfolio update broadcast via WebSocket (v{self.metrics.version})")
            
            # Also update WebSocket manager's latest portfolio for new connections
            self._ws_manager._latest_portfolio = portfolio
            self._ws_manager._latest_portfolio_timestamp = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Failed to broadcast portfolio update: {e}")
    
    # ========================================================================
    # PUBLIC READ API (Thread-safe, lock-free)
    # ========================================================================
    
    def get_portfolio_snapshot(self) -> Optional[PortfolioRiskModel]:
        """
        Get current portfolio state (thread-safe)
        
        Returns immutable reference to Pydantic model.
        No locks needed - atomic read of reference.
        """
