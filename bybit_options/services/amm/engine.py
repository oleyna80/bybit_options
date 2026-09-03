import asyncio
import os
from datetime import datetime
from decimal import Decimal
from typing import List, Dict

from dotenv import load_dotenv
from loguru import logger

from bybit_options.services.delta.database_config import db
from bybit_options.services.bybit_connector import BybitConnector
from .repository import AmmRepository
from .models import AmmStrategy, AmmOrder, AmmLeg

from .market_data import MarketDataActor
from .pricing import OptionPricing
from .greeks_aggregator import GreeksAggregator, PortfolioGreeks
from .risk_director import RiskDirector, RiskLimits

class AmmEngine:
    """
    The Dream Machine Engine.
    Orchestrates Pricing, Execution, and Risk.
    """
    
    def __init__(self):
        self.repo = AmmRepository()
        self.strategies: List[AmmStrategy] = []
        self.connector: BybitConnector = None
        self.market_data: MarketDataActor = None
        self.greeks_aggregator = GreeksAggregator()
        self.risk_director: RiskDirector = None  # Initialized after repo
        self.is_running = False
        
    async def initialize(self):
        """Bootup sequence."""
        load_dotenv()
        logger.info("[AMM] Initializing Engine...")
        
        # 1. Connect DB
        await db.connect()
        logger.info("[AMM] Database Connected.")
        
        # 2. Connect Exchange
        api_key = os.getenv("BYBIT_API_KEY")
        api_secret = os.getenv("BYBIT_API_SECRET")
        testnet = os.getenv("BYBIT_TESTNET", "false").lower() == "true"
        
        self.connector = BybitConnector(api_key, api_secret, testnet=testnet)
        logger.info("[AMM] Bybit Connector Ready.")
        
        # 3. Start Market Data
        self.market_data = MarketDataActor(testnet=testnet)
        await self.market_data.start()
        
        # 4. Load Strategies
        self.strategies = await self.repo.get_active_strategies()
        logger.info(f"[AMM] Loaded {len(self.strategies)} active strategies.")
        
        # Subscribe to Tickers
        symbols = set()
        base_coins = set()  # NEW: Track unique base coins
        
        for s in self.strategies:
            for leg in s.legs:
                symbols.add(leg.symbol)
                # Extract base coin for underlying subscription
                try:
                    from bybit_options.core.risk_engine import RiskEngine
                    parsed = RiskEngine.parse_symbol(leg.symbol)
                    base = parsed.get("base")
                    if base:
                        base_coins.add(base)
                except Exception as e:
                    logger.warning(f"[AMM] Failed to parse base from {leg.symbol}: {e}")
        
        # Subscribe to option tickers
        if symbols:
            self.market_data.subscribe(symbols)
        
        # Subscribe to underlying tickers (spot prices)
        if base_coins:
            self.market_data.subscribe_underlying(base_coins)
            logger.info(f"[AMM] Subscribed to {len(base_coins)} underlying tickers")
        
        # 5. Initialize Gatekeeper (Risk Director)
        self.risk_director = RiskDirector(
            repo=self.repo,
            limits=RiskLimits(
                max_portfolio_delta=1.0,
                max_portfolio_gamma=0.05,
                max_portfolio_vega=5000.0,
                max_leg_delta=0.3,
                max_leg_gamma=0.01
            )
        )
        logger.info("[AMM] Gatekeeper initialized")
        
        # 6. Reconcile State
        await self.reconcile_state()
        
    async def reconcile_state(self):
        """
        Sync AMM memory state with Bybit exchange.
        Source of Truth: Exchange orders.
        
        This prevents:
        - Duplicate orders after restart
        - Orphaned orders in DB
        - Missed fills tracking
        """
        logger.info("[AMM] Starting Reconciliation...")
        
        try:
            # 1. Get all active orders from exchange
            response = await self.connector.get_orders(
                category="option",
                orderStatus="New,PartiallyFilled",
                limit=200  # Should cover all AMM orders
            )
            
            # Extract order list (Bybit V5 response format)
            open_orders = response.get("list", []) if isinstance(response, dict) else []
            
            # Build lookup by orderLinkId
            exchange_orders = {
                o.get("orderLinkId"): o 
                for o in open_orders
                if o.get("orderLinkId")
            }
            
            logger.info(f"[AMM] Found {len(exchange_orders)} active orders on exchange")
            
            # 2. Check each leg's active_order against exchange
            synced = 0
            cancelled = 0
            filled = 0
            
            for strategy in self.strategies:
                for leg in strategy.legs:
                    if not leg.active_order:
                        continue
                    
                    link_id = leg.active_order.bybit_order_link_id
                    
                    if link_id in exchange_orders:
                        # Order exists on exchange — check status
                        exch_order = exchange_orders[link_id]
                        exch_status = exch_order.get("orderStatus")
                        
                        if exch_status == "Filled":
                            logger.info(f"[AMM] Order {link_id} filled, updating")
                            leg.active_order.status = "FILLED"
                            await self.repo.update_order_status(link_id, "FILLED")
                            leg.active_order = None  # Clear for new order
                            filled += 1
                            
                        elif exch_status == "Cancelled":
                            logger.info(f"[AMM] Order {link_id} cancelled on exchange")
                            leg.active_order.status = "CANCELLED"
                            await self.repo.update_order_status(link_id, "CANCELLED")
                            leg.active_order = None
                            cancelled += 1
                            
                        else:
                            # Order is active (New/PartiallyFilled)
                            synced += 1
                            
                    else:
                        # Order missing from exchange — mark cancelled
                        logger.warning(f"[AMM] Order {link_id} not on exchange, marking cancelled")
                        await self.repo.update_order_status(link_id, "CANCELLED")
                        leg.active_order = None
                        cancelled += 1
            
            logger.info(
                f"[AMM] Reconciliation complete: {synced} synced, "
                f"{filled} filled, {cancelled} cancelled"
            )
            
        except Exception as e:
            logger.error(f"[AMM] Reconciliation failed: {e}")
            # Don't crash, continue with existing state
            logger.warning("[AMM] Continuing with existing state after reconciliation error")

    async def run_loop(self):
        """Main Gardener Loop."""
        self.is_running = True
        logger.info("[AMM] Engine Started. Entering Main Loop.")
        
        while self.is_running:
            try:
                await self.run_gardener_cycle()
            except Exception as e:
                logger.error(f"[AMM] Gardener Cycle Error: {e}")
            
            await asyncio.sleep(1) # 1Hz for Safety in MVP
            
    async def run_gardener_cycle(self):
        """
        Core Pricing Logic with Portfolio Greeks Risk Management.
        """
        if not self.strategies:
            return
        
        # === 1. Build caches for Greeks aggregation ===
        spot_prices = {}
        market_ivs = {}
        time_to_expiries = {}
        
        from .time_calculator import calculate_time_to_expiry
        from bybit_options.core.risk_engine import RiskEngine
        
        for strategy in self.strategies:
            if strategy.is_paused or not strategy.is_active:
                continue
            
            for leg in strategy.legs:
                if not leg.is_active:
                    continue
                
                symbol = leg.symbol
                
                # Cache spot price
                try:
                    parsed = RiskEngine.parse_symbol(symbol)
                    base = parsed.get("base")
                    if base and base not in spot_prices:
                        spot_price = self.market_data.get_underlying_price(base)
                        if spot_price:
                            spot_prices[base] = spot_price
                except:
                    pass
                
                # Cache market IV
                iv = self.market_data.get_market_iv(symbol)
                if iv:
                    market_ivs[symbol] = iv
                
                # Cache time to expiry
                try:
                    T = calculate_time_to_expiry(symbol)
                    time_to_expiries[symbol] = T
                except:
                    pass
        
        # === 2. Calculate Portfolio Greeks ===
        portfolio = self.greeks_aggregator.calculate(
            self.strategies,
            spot_prices,
            market_ivs,
            time_to_expiries
        )
        
        # Log portfolio risk
        logger.info(
            f"[AMM] Portfolio Greeks: Δ={portfolio.total_delta:.4f} Γ={portfolio.total_gamma:.6f} "
            f"ν={portfolio.total_vega:.2f} θ={portfolio.total_theta:.2f}"
        )
        
        # === 3. Portfolio-Level Risk Gating (Gatekeeper) ===
        portfolio_decision = self.risk_director.evaluate_portfolio(portfolio)
        await self.risk_director.log_decision(
            decision_type="PORTFOLIO",
            decision=portfolio_decision,
            portfolio_greeks=portfolio
        )
        
        if portfolio_decision.decision == "BLOCK":
            logger.warning(f"[AMM] ⛔ Gardener cycle BLOCKED: {portfolio_decision.reason}")
            return  # Skip this cycle entirely
        
        logger.info("[AMM] ✅ Portfolio risk check PASSED")
        
        # === 4. Process each leg with per-leg risk gating ===

        for strategy in self.strategies:
            if strategy.is_paused or not strategy.is_active:
                continue
                
            for leg in strategy.legs:
                if not leg.is_active:
                    continue
                    
                # 1. Get Market Data
                mark_iv = self.market_data.get_market_iv(leg.symbol)
                mark_price = self.market_data.get_mark_price(leg.symbol)
                
                if not mark_iv or not mark_price:
                    # Waiting for websocket...
                    continue
                
                # 2. Parse symbol and calculate time to expiry
                try:
                    from .time_calculator import calculate_time_to_expiry
                    from bybit_options.core.risk_engine import RiskEngine
                    
                    # Calculate T dynamically from expiry
                    T = calculate_time_to_expiry(leg.symbol)
                    
                    # Parse symbol for strike and option type
                    parsed = RiskEngine.parse_symbol(leg.symbol)
                    strike = float(parsed.get("strike", 0))
                    option_type = parsed.get("type", "C") 
                    
                except ValueError as e:
                    logger.warning(f"[AMM] Failed to parse symbol {leg.symbol}: {e}")
                    continue
                except Exception as e:
                    logger.error(f"[AMM] Unexpected error parsing {leg.symbol}: {e}")
                    continue
                
                # 3. Calculate Fair Price
                # Safety Anchor: FairIV vs MarkIV
                # Logic: We define FairIV in Strategy.
                # If we are BUYING, we want Price(FairIV). But if MarkIV is way lower, we buy cheaper.
                # If we are SELLING (Market Making), we ask Price(FairIV).
                # To prevent "Panic Dump" selling below market:
                # MyAsk =  Max(Price(FairIV), Price(MarkIV - Buffer))
                
                target_iv = float(strategy.target_iv)
                
                # NEW: Get real-time spot price from underlying cache
                from bybit_options.core.risk_engine import RiskEngine
                parsed = RiskEngine.parse_symbol(leg.symbol)
                base_coin = parsed.get("base")
                
                spot_price = self.market_data.get_underlying_price(base_coin)
                if not spot_price:
                    logger.warning(f"[AMM] No spot price for {base_coin}, skipping leg {leg.symbol}")
                    continue
                
                # Calculate base Greeks first (to get delta for skew adjustment)
                base_greeks = OptionPricing.calculate_greeks(
                    spot=spot_price,
                    strike=strike,
                    time_to_expiry=T,
                    risk_free_rate=0.0,
                    iv=target_iv,
                    option_type=option_type
                )
                leg_delta = base_greeks["delta"]
                
                # === DYNAMIC SKEW ADJUSTMENT ===
                # Formula: adjusted_iv = target_iv + (skew_factor * delta)
                # - Skew > 0: OTM puts (delta < 0) get lower IV, OTM calls (delta > 0) get higher IV
                # - This is opposite to typical equity skew, can be inverted if needed
                skew_adjustment = float(strategy.skew_factor) * leg_delta
                adjusted_iv = target_iv + skew_adjustment
                
                # Clamp IV to configured min/max bounds
                min_iv = float(strategy.min_iv) if hasattr(strategy, 'min_iv') else 0.10
                max_iv = float(strategy.max_iv) if hasattr(strategy, 'max_iv') else 2.00
                adjusted_iv = max(min_iv, min(max_iv, adjusted_iv))
                
                if abs(skew_adjustment) > 0.001:
                    logger.debug(f"[AMM] {leg.symbol}: base_iv={target_iv:.3f}, skew_adj={skew_adjustment:.4f}, final_iv={adjusted_iv:.3f}")
                
                # Calculate fair price with adjusted IV
                fair_price = OptionPricing.calculate_price(
                    spot=spot_price,
                    strike=strike,
                    time_to_expiry=T,
                    risk_free_rate=0.0,
                    iv=adjusted_iv,  # Now using adjusted IV
                    option_type=option_type
                )
                
                # === APPLY BID-ASK SPREAD ===
                # spread_bps = 50 means 0.5% total spread (0.25% per side)
                spread_bps = getattr(strategy, 'spread_bps', 50)
                spread_pct = spread_bps / 10000  # 50 bps = 0.005
                
                if leg.side == "SELL":
                    # We're selling (asking) - add half spread to fair price
                    final_price = fair_price * (1 + spread_pct / 2)
                else:
                    # We're buying (bidding) - subtract half spread from fair price
                    final_price = fair_price * (1 - spread_pct / 2)
                
                # Override fair_price for downstream logic
                fair_price = final_price
                
                # Calculate Greeks for this leg
                greeks = OptionPricing.calculate_greeks(
                    spot=spot_price,
                    strike=strike,
                    time_to_expiry=T,
                    risk_free_rate=0.0,
                    iv=target_iv,
                    option_type=option_type
                )
                
                leg_delta = greeks["delta"]
                leg_gamma = greeks["gamma"]
                
                # === Per-Leg Risk Gating (Gatekeeper) ===
                leg_decision = self.risk_director.evaluate_leg_order(
                    leg=leg,
                    leg_delta=leg_delta,
                    leg_gamma=leg_gamma,
                    portfolio_greeks=portfolio
                )
                
                await self.risk_director.log_decision(
                    decision_type="LEG",
                    decision=leg_decision,
                    portfolio_greeks=portfolio,
                    strategy_id=strategy.id,
                    leg_id=leg.id
                )
                
                if leg_decision.decision == "BLOCK":
                    logger.info(f"[AMM] ⛔ Leg {leg.symbol} skipped: {leg_decision.reason}")
                    continue  # Skip this leg, move to next
                
                # 4. Execute / Update Order
                # Check active order for this leg
                # If none -> Create
                # 4. Execute / Update Order
                await self.execute_leg_update(strategy, leg, fair_price, target_iv)

    async def execute_leg_update(self, strategy: AmmStrategy, leg: AmmLeg, fair_price: float, iv: float):
        """
        Decide whether to Place, Amend, or Ignore.
        """
        # Quantize Price (Bybit requires specific tick size, e.g. 0.05 or 0.1)
        # TODO: Get tick_size from InstrumentInfo. Assuming 0.1 for now.
        tick_size = 0.1
        price = round(fair_price / tick_size) * tick_size
        price_str = f"{price:.1f}"
        
        # 1. New Order
        if not leg.active_order:
            logger.info(f"[AMM] Placing NEW Order for {leg.symbol} @ {price_str}")
            try:
                # Generate unique link ID
                link_id = f"amm-{strategy.id}-{leg.id}-{int(asyncio.get_event_loop().time()*1000)}"
                
                # Execute API
                # Bybit Option qty is contracts. target_size is user def.
                # Assuming ratio is per strategy unit.
                # For MVP, assume fixed size 0.1 just to test.
                qty_str = "0.1" 
                
                # Side from Leg (BUY/SELL)
                side = leg.side.upper()
                
                # Call Connector
                res = await self.connector.place_order(
                    category="option",
                    symbol=leg.symbol,
                    side=side,
                    order_type="Limit",
                    qty=qty_str,
                    price=price_str,
                    order_link_id=link_id,
                    time_in_force="PostOnly" # Maker only!
                )
                
                bybit_id = res.get("orderId")
                
                # Save to DB
                new_order = AmmOrder(
                    leg_id=leg.id,
                    bybit_order_id=bybit_id,
                    bybit_order_link_id=link_id,
                    price=Decimal(price_str),
                    iv_at_creation=Decimal(str(iv)),
                    status="ACTIVE"
                )
                
                oid = await self.repo.save_order(new_order)
                new_order.id = oid
                
                # Update Runtime State
                leg.active_order = new_order
                
            except Exception as e:
                logger.error(f"[AMM] Place Order Failed: {e}")
                return

        # 2. Amend Order
        else:
            current_order = leg.active_order
            current_price = float(current_order.price)
            
            # Threshold Check (avoid spamming API for < 1% moves or < 2 ticks)
            # e.g. if price changed by > 0.5%
            pct_change = abs(price - current_price) / current_price if current_price else 0
            if pct_change < 0.005: # 0.5% buffer
                return
            
            logger.info(f"[AMM] Amending Order {leg.symbol}: {current_price} -> {price_str}")
            try:
                await self.connector.amend_order(
                    category="option",
                    symbol=leg.symbol,
                    order_link_id=current_order.bybit_order_link_id,
                    price=price_str
                )
                
                # Update DB
                # Note: We don't change 'id', just price/status could be updated if we tracked history
                # Ideally, insert a new 'OrderHistory' record or update the current one.
                # For MVP, we update the runtime object and maybe a 'last_updated' field in DB.
                # (Repository update logic needed here if we want persistence of price changes)
                
                current_order.price = Decimal(price_str)
                current_order.last_updated = datetime.now()
                # await self.repo.update_order_price(...) 
                
            except Exception as e:
                logger.error(f"[AMM] Amend Failed: {e}")
                # If error is "Order not found", we should mark it CANCELLED and clear active_order
                if "not found" in str(e).lower() or "170213" in str(e): # 170213: Order does not exist
                     logger.warning("[AMM] Order missing on exchange. Resetting.")
                     # Mark DB Cancelled
                     await self.repo.update_order_status(current_order.bybit_order_link_id, "CANCELLED")
                     leg.active_order = None

    async def stop(self):
        self.is_running = False
        if self.market_data:
            await self.market_data.stop()
        await db.close()
        logger.info("[AMM] Engine Stopped.")
