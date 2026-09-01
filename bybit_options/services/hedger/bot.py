"""
Delta Hedger Bot - Main Logic
"""

import asyncio
import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional

from .option_solver import OptionSolver
from .config import HedgerConfig, HedgerConfigLoader
from .models import HedgeAction, HedgerMode, OrderResult, FractalSignal
from .order_executor import OrderExecutor
from .position_monitor import PositionMonitor, PositionFetchError
from .signal_detector import SignalDetector
from ..telegram_alerter import TelegramAlerter

logger = logging.getLogger(__name__)


class DeltaHedgerBot:
    """
    Main class for Delta Hedger Bot.
    
    Orchestrates monitoring and hedging activities.
    """
    
    def __init__(
        self,
        connector,  # BybitConnector
        db_pool,    # asyncpg.Pool
        config: Optional[HedgerConfig] = None
    ):
        self.connector = connector
        self.db_pool = db_pool
        
        # Load config or use default (will be refreshed from DB in start)
        self.config = config or HedgerConfig()
        
        # Components
        self.monitor = PositionMonitor(connector, base_coin="BTC")
        self.executor = OrderExecutor(connector)
        self.detector = SignalDetector(db_pool)
        self.alerter = TelegramAlerter()
        
        # State
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Start the hedger bot loop."""
        if self._running:
            logger.warning("Hedger bot already running")
            return
            
        logger.info("Starting Delta Hedger Bot...")
        self._running = True
        
        # Initial config load
        await self.refresh_config()
        
        self._task = asyncio.create_task(self._main_loop())
        await self._send_alert(f"🚀 **Bot Started**\nMode: `{self.config.mode.value}`")
        logger.info("Delta Hedger Bot started")
        
    async def stop(self):
        """Stop the hedger bot."""
        if not self._running:
            return
            
        logger.info("Stopping Delta Hedger Bot...")
        self._running = False
        
        if self._task:
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
            
        await self._send_alert("🛑 **Bot Stopped**")
        await self.alerter.stop()
        logger.info("Delta Hedger Bot stopped")
        
    async def refresh_config(self):
        """Reload configuration from DB."""
        try:
            self.config = await HedgerConfigLoader.load_from_db(
                self.db_pool, 
                override_env=True
            )
            logger.info(f"Config reloaded: mode={self.config.mode}, enabled={self.config.enabled}")
        except Exception as e:
            logger.error(f"Failed to reload config: {e}")
            
    async def _main_loop(self):
        """Main execution loop."""
        while self._running:
            try:
                # 1. Refresh config
                await self.refresh_config()
                
                if not self.config.enabled:
                    logger.info("Hedger disabled in config, sleeping...")
                    await self._sleep_cancellable(self.config.check_interval_seconds)
                    continue
                
                # 2. Check and hedge
                await self.check_and_hedge()
                
                # 3. Sleep
                await self._sleep_cancellable(self.config.check_interval_seconds)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                await asyncio.sleep(5)  # Error backoff
                
    async def _sleep_cancellable(self, seconds: int):
        """Sleep that can be cancelled properly."""
        for _ in range(seconds):
            if not self._running:
                break
            await asyncio.sleep(1)

    def _determine_mode(self, signal: Optional[FractalSignal]) -> HedgerMode:
        """
        Determine HedgerMode based on detected signal.
        
        Logic:
        - No signal -> NEUTRAL
        - H4 breakout -> DEFENSIVE
        - H1 breakout -> DIRECTIONAL
        """
        if not signal:
            return HedgerMode.NEUTRAL
            
        if signal.timeframe == "H4" and signal.is_breakout:
            return HedgerMode.DEFENSIVE
            
        if signal.timeframe == "H1" and signal.is_breakout:
            return HedgerMode.DIRECTIONAL
            
        return HedgerMode.NEUTRAL

    async def check_and_hedge(self):
        """
        Execute one hedging cycle.
        
        1. Get current delta
        2. Calculate deviation from target
        3. If deviation > threshold, place hedge order
        """
        try:
            # 0. Detect Signals and Adjust Mode (HEDGER-009)
            signal = await self.detector.detect()
            new_mode = self._determine_mode(signal)
            
            # Determine new target delta
            new_target = self.config.target_delta
            if new_mode == HedgerMode.NEUTRAL:
                new_target = 0.0
            elif new_mode == HedgerMode.DIRECTIONAL and signal:
                if signal.direction == "LONG":
                    new_target = self.config.directional_bias_long
                elif signal.direction == "SHORT":
                    new_target = self.config.directional_bias_short
            
            mode_changed = new_mode != self.config.mode
            target_changed = new_target != self.config.target_delta
            
            if mode_changed or target_changed:
                previous_mode = self.config.mode
                
                logger.info(
                    f"State update: Mode {self.config.mode}->{new_mode}, "
                    f"Target {self.config.target_delta}->{new_target} (Signal: {signal})"
                )
                
                await self._send_alert(
                    f"🔄 **Mode Change**\n"
                    f"From: `{self.config.mode.value}`\n"
                    f"To: `{new_mode.value}`\n"
                    f"Target Delta: `{new_target}`\n"
                    f"Signal: `{signal}`"
                )

                self.config.mode = new_mode
                self.config.target_delta = new_target
                # Persist new state to DB
                await HedgerConfigLoader.save_to_db(self.db_pool, self.config)
                
                # If entering DEFENSIVE mode, buy protection
                if new_mode == HedgerMode.DEFENSIVE and mode_changed and signal:
                    await self._buy_protection_options(signal)
                
                # If leaving DEFENSIVE mode, close protection
                if previous_mode == HedgerMode.DEFENSIVE and mode_changed and new_mode != HedgerMode.DEFENSIVE:
                    await self._close_protection_options()
            
            # 1. Get Portfolio Delta
            current_delta = await self.monitor.get_portfolio_delta()
            
            # 2. Determine Target Delta
            # For HEDGER-006 (Phase 1), we only support NEUTRAL mode logic here effectively
            # Full logic for DIRECTIONAL/DEFENSIVE will be added later, 
            # but we use config.target_delta which should be 0.0 for NEUTRAL.
            target = 0.0
            if self.config.mode == HedgerMode.NEUTRAL:
                target = 0.0
            else:
                # Placeholder for other modes
                target = self.config.target_delta
                
            deviation = current_delta - target
            abs_deviation = abs(deviation)
            
            logger.info(
                f"Delta check: current={current_delta:.4f} target={target:.4f} "
                f"deviation={deviation:.4f} threshold={self.config.threshold}"
            )
            
            # 3. Check Threshold
            if abs_deviation < self.config.threshold:
                logger.debug("Deviation within threshold, skipping hedge")
                return
            
            # 4. Calculate Hedge Action
            # If deviation is positive (Long exposure), we need to SELL (Short)
            # If deviation is negative (Short exposure), we need to BUY (Long)
            hedge_side = "Sell" if deviation > 0 else "Buy"
            hedge_size = min(abs_deviation, self.config.max_order_size)
            
            # Formally calculate required change
            # e.g. deviation = +0.5 (Too long). Hedge = Sell 0.5.
            # New delta ~= +0.5 - 0.5 = 0.
            
            logger.info(f"Hedging needed: {hedge_side} {hedge_size:.4f} BTC")
            
            # 5. Execute Order (Futures)
            # We assume hedging is done via BTCUSDT futures
            # For Limit Order, we need current price properly. 
            # OrderExecutor places limit, but we need a price.
            # Ideally we should get ticker price.
            # For MVP, let's assume we can fetch ticker or use 'last_price' if available?
            # Or use OrderExecutor to get ticker?
            # Since OrderExecutor is low level, we'll fetch ticker here via connector
            
            ticker = await self.connector.get_ticker("BTCUSDT", category="linear")
            best_bid = float(ticker.get("bid1Price", 0))
            best_ask = float(ticker.get("ask1Price", 0))
            
            if best_bid == 0 or best_ask == 0:
                logger.error("Failed to get valid orderbook prices")
                return

            # Determine limit price based on side and offset
            # If BUY, we want to be slightly aggressive or passive? 
            # 'limit_price_offset_bps' suggests aggressive (pay more to fill) or passive?
            # Usually for hedging we want to fill. 
            # Let's assume offset adds to price for BUY (higher limit) and subtracts for SELL (lower limit) 
            # to ensure fill (marketable limit), OR it places passive maker order.
            # Given AC3 mentions 'retry logic', it implies we might want to be maker or aggressive taker.
            # Let's implementation: standard 'taker' style limit order (crossing spread)
            # or 'maker' style. Let's aim for MAKER first (inside spread) or Best Bid/Ask?
            # MVP: Place at Best Ask (Buy) or Best Bid (Sell) aka Marketable Limit
            
            price = best_ask if hedge_side == "Buy" else best_bid
            
            # Apply offset to ensure fill if configured (marketable limit)
            # offset_ratio = self.config.limit_price_offset_bps / 10000.0
            # if hedge_side == "Buy":
            #     price *= (1 + offset_ratio)
            # else:
            #     price *= (1 - offset_ratio)
                
            # Round price (BTCUSDT usually 1 or 0.1 precision, check instrument info? Assuming 0.1 for now)
            # Ideally should use instrument info. Passing raw float might be risky if not rounded.
            # Let's simple round to 1 decimal place for BTC
            price = round(price, 1)
            
            result = await self.executor.place_limit_order(
                symbol="BTCUSDT",
                side=hedge_side,
                size=hedge_size,
                price=price,
                category="linear",
                time_in_force="GTC"
            )
            
            # 6. Log Action
            await self._log_action(
                action_type="FUTURES_HEDGE",
                side=hedge_side,
                size=hedge_size,
                price=price,
                result=result,
                delta_before=current_delta,
                target_delta=target
            )
            
        except PositionFetchError as e:
            logger.error(f"Position fetch failed, skipping cycle: {e}")
            # Log failure?
        except Exception as e:
            logger.error(f"Unexpected error in check_and_hedge: {e}", exc_info=True)
    
    async def _buy_protection_options(self, signal: FractalSignal):
        """
        Buy protection options when entering DEFENSIVE mode.
        """
        try:
            logger.info(f"Initiating defensive option buy for signal: {signal}")
            
            base_coin = self.config.hedge_base_coin
            
            # 1. Fetch available expiries & instrument info
            instruments = await self.connector.get_instruments_info(category="option", base_coin=base_coin)
            expiries = set()
            symbol_map = {}
            
            for inst in instruments:
                sym = inst.get("symbol", "")
                symbol_map[sym] = inst
                parts = sym.split("-")
                if len(parts) >= 3:
                     expiries.add(parts[1])
            
            # 2. Select Expiry
            target_expiry = OptionSolver.get_target_expiry(list(expiries), min_days=2)
            if not target_expiry:
                logger.error("No suitable expiry found for protection")
                return
                
            # 3. Select Strike (ATM)
            atm_strike = OptionSolver.get_atm_strike(signal.current_price, base_coin=base_coin)
            
            # 4. Determine Type
            # Breakout LONG (UP) -> Buy Call (Gamma Long)
            # Breakout SHORT (DOWN) -> Buy Put (Gamma Long)
            option_type = "C" if signal.direction == "LONG" else "P"
            
            # 5. Construct Symbol
            symbol = OptionSolver.format_symbol(base_coin, target_expiry, atm_strike, option_type)
            
            # Validate symbol availability
            inst_info = symbol_map.get(symbol)
            if not inst_info:
                logger.error(f"Constructed symbol {symbol} not found in available instruments")
                return

            # Get tick size for rounding
            tick_size = float(inst_info.get("priceFilter", {}).get("tickSize", "0.5"))

            # 6. Execute Order
            size = self.config.max_order_size
            
            logger.info(f"Placing defensive option order: {symbol} {size} contracts")
            
            ticker_list = await self.connector.get_tickers(category="option", symbol=symbol)
            if not ticker_list:
                logger.error(f"Ticker not found for {symbol}")
                return
                
            ticker = ticker_list[0]
            best_ask = float(ticker.get("ask1Price", 0))
            if best_ask == 0:
                 logger.warning(f"No ask price for {symbol}, cannot place limit buy")
                 return
            
            # Calculate Limit Price with Configurable Markup
            markup = 1 + (self.config.option_price_markup_pct / 100)
            raw_price = best_ask * markup
            
            # Round to tick size
            limit_price = round(raw_price / tick_size) * tick_size
            
            result = await self.executor.place_option_order(
                symbol=symbol,
                side="Buy",
                size=size,
                price=limit_price,
                order_type="Limit"
            )
            
            if result.status == "PLACED" or result.status == "FILLED":
                logger.info(
                    f"Option order success: symbol={symbol} price={limit_price:.2f} "
                    f"size={size} order_id={result.order_id} exec_time_ms={result.execution_time_ms}"
                )
            else:
                logger.error(f"Option order failed: {result.error}")
            
            await self._log_action(
                action_type="OPTIONS_BUY",
                side="BUY",
                size=size,
                price=limit_price,
                result=result,
                delta_before=0.0,
                target_delta=0.0,
                instrument=symbol,
                trigger_source=f"{signal.timeframe}_FRACTAL"
            )

        except Exception as e:
            logger.error(f"Failed to buy protection options: {e}", exc_info=True)
            
    async def _log_action(
        self,
        action_type: str,
        side: str,
        size: float,
        price: float,
        result: OrderResult,
        delta_before: float,
        target_delta: float,
        instrument: str = "BTCUSDT",
        trigger_source: str = "THRESHOLD"
    ):
        """Log hedging action to DB."""
        
        # Send Alert
        icon = "✅" if result.status == "Filled" else "⚠️"
        if result.status != "Filled": 
            icon = "❌" if result.error else "⏳"
        
        msg = (
            f"{icon} **Order Executed**\n"
            f"Type: `{action_type}`\n"
            f"Side: `{side}` {size} {instrument}\n"
            f"Price: {price}\n"
            f"Status: `{result.status}`"
        )
        if result.error:
            msg += f"\nError: `{result.error}`"
        
        await self._send_alert(msg)

        try:
            action = HedgeAction(
                mode=self.config.mode,
                trigger_source=trigger_source,
                delta_before=delta_before,
                target_delta=target_delta,
                action_type=action_type,
                instrument=instrument,
                side=side.upper(),
                size=size,
                order_type="LIMIT",
                limit_price=price,
                order_id=result.order_id,
                status=result.status,
                error_message=result.error,
                delta_after=None, # TBD: could calculate projected
                execution_time_ms=result.execution_time_ms
            )
            
            query = """
                INSERT INTO hedge_actions (
                    mode, trigger_source, delta_before, target_delta,
                    action_type, instrument, side, size, order_type, limit_price,
                    order_id, status, error_message, execution_time_ms, timestamp
                )
                VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15
                )
            """
            
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    query,
                    action.mode.value,
                    action.trigger_source,
                    action.delta_before,
                    action.target_delta,
                    action.action_type,
                    action.instrument,
                    action.side,
                    action.size,
                    action.order_type,
                    action.limit_price,
                    action.order_id,
                    action.status,
                    action.error_message,
                    action.execution_time_ms,
                    action.timestamp
                )
                
        except Exception as e:
            logger.error(f"Failed to log hedge action: {e}")

    async def _close_protection_options(self):
        """
        Close all Long option positions found (assuming they were protective).
        Called when leaving DEFENSIVE mode.
        """
        try:
            logger.info("Closing protective options...")
            
            # 1. Fetch current option positions
            positions = await self.connector.get_positions(category="option", base_coin=self.config.hedge_base_coin)
            
            # 2. Filter for Long positions (size > 0 and side usually matches)
            # In Bybit V5:
            # size: Position size
            # side: "Buy" or "Sell". For Options, "Buy" means we are Long the option.
            
            long_positions = [
                p for p in positions 
                if float(p.get("size", 0)) > 0 and p.get("side") == "Buy"
            ]
            
            if not long_positions:
                logger.info("No protective options to close.")
                return

            for pos in long_positions:
                symbol = pos.get("symbol")
                size = float(pos.get("size", 0))
                
                logger.info(f"Closing protective position: {symbol} size={size}")
                
                # Fetch ticker for Price
                ticker_list = await self.connector.get_tickers(category="option", symbol=symbol)
                best_bid = 0.0
                tick_size = 0.5 # default
                
                if ticker_list:
                     best_bid = float(ticker_list[0].get("bid1Price", 0))
                
                # We need to SELL to close a Long position.
                # If best_bid > 0, we can place a limit order.
                # If 0, we might be stuck.
                
                # Strategy: Limit at Best Bid * 0.9 (Marketable Limit for fast exit)
                # or just generic Limit if we want to be maker? Code Review says panic exit?
                # "Leaving Defensive Mode" -> "False Breakout" -> We just want to dump it.
                
                price = best_bid * 0.9 if best_bid > 0 else 0
                
                # Adjust to tick size
                # Need to fetch instrument info or hardcode for now (OptionSolver helper?)
                # We can try to use the price filter from position info if available? No.
                # Let's simple round for now or use generic 0.5 for BTC options
                # (TODO: Use instrument info cache)
                
                if price > 0:
                     price = round(price * 2) / 2 # Round to nearest 0.5
                else:
                    # If Bid is 0, option is worthless. Maybe don't close?
                    # Or try place at min tick 0.1?
                    logger.warning(f"No Bid for {symbol}, cannot close immediately.")
                    continue

                result = await self.executor.place_option_order(
                    symbol=symbol,
                    side="Sell", # Opposite to "Buy" position
                    size=size,
                    price=price,
                    order_type="Limit"
                )
                
                await self._log_action(
                    action_type="OPTIONS_CLOSE",
                    side="SELL",
                    size=size,
                    price=price,
                    result=result,
                    delta_before=0.0,
                    target_delta=0.0,
                    instrument=symbol,
                    trigger_source="MODE_SWITCH"
                )

        except Exception as e:
            logger.error(f"Failed to close protection options: {e}", exc_info=True)
    async def _send_alert(self, msg: str):
        """Helper to send telegram alerts."""
        try:
            logger.debug("Sending telegram alert: %s", msg)
            await self.alerter.send_message(f"🤖 *DeltaHedgerBot*\n{msg}")
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
