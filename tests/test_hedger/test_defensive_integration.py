"""
Integration tests for Defensive Mode Lifecycle.
Simulates: H4 Breakout -> Buy Option -> Return to Range -> Close Option.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from bybit_options.services.hedger.bot import DeltaHedgerBot, HedgerMode
from bybit_options.services.hedger.models import HedgerConfig, OrderResult

class MockPool:
    def __init__(self):
        self.acquire = MagicMock()
        self.connection = AsyncMock()
        # Ensure acquire context manager returns the connection
        self.acquire.return_value.__aenter__.return_value = self.connection
        
        # Methods for reading data (SignalDetector uses these directly or via pool)
        # However, bot.db_pool is passed to SignalDetector.
        # SignalDetector uses self.db.fetch and self.db.fetchrow (via fetchval helper usually or fetchrow)
        # Actually SignalDetector uses fetch and fetchrow.
        self.fetch = AsyncMock()
        self.fetchval = AsyncMock()
        self.fetchrow = AsyncMock()
        
        # execute is called on connection context manager usually in logs
        # but configured as pool.acquire() in bot._log_action
        
    def reset_mocks(self):
        self.fetch.reset_mock()
        self.fetchval.reset_mock()
        self.fetchrow.reset_mock()
        self.connection.execute.reset_mock()

@pytest.fixture
def mock_db_pool():
    return MockPool()

@pytest.fixture
def bot(mock_db_pool):
    connector = AsyncMock()
    
    # 1. Setup Connector Mocks for Options
    # Instruments
    connector.get_instruments_info.return_value = [
        {"symbol": "BTC-5JAN24-40000-C", "priceFilter": {"tickSize": "0.5"}},
        {"symbol": "BTC-5JAN24-30000-P", "priceFilter": {"tickSize": "0.5"}}
    ]
    # Tickers (for Option Price)
    # Return a list with one ticker having ask1Price (for buying) and bid1Price (for selling)
    connector.get_tickers.return_value = [
        {"ask1Price": "200.0", "bid1Price": "180.0"}
    ]
    # Ticker for Futures (BTCUSDT)
    connector.get_ticker.return_value = {"ask1Price": "40000.0", "bid1Price": "40000.0"}
    
    # Order Executor Returns
    connector.place_order.return_value = {"orderId": "opt_123", "execId": "ex_1"} # Raw return
    
    config = HedgerConfig(
        mode=HedgerMode.NEUTRAL, 
        enabled=True, 
        hedge_base_coin="BTC",
        option_price_markup_pct=5.0
    )
    
    bot_instance = DeltaHedgerBot(connector, mock_db_pool, config=config)
    
    # Mock specialized components slightly but keep logic integral
    # We WANT to test OptionSolver and Logic interaction, so we don't mock OptionSolver entirely
    # But we mock external calls (done via connector)
    
    # Mock Monitor (we don't test Delta calculation here strictly, just 0.0)
    bot_instance.monitor = AsyncMock()
    bot_instance.monitor.get_portfolio_delta.return_value = 0.0
    
    # We keep Executor real? Or mock?
    # Executor calls connector.place_order. If we keep Executor, we verify connector calls.
    # But Executor has delays/retries. For unit/integration test, mocked executor is often easier 
    # if we only care about "it tried to place order".
    # However, to test "Full Cycle", we want to see OrderResult propagated.
    # Let's mock executor methods to return successes immediately.
    bot_instance.executor = AsyncMock()
    bot_instance.executor.place_option_order.return_value = OrderResult(
        order_id="opt_123", status="PLACED", symbol="BTC-5JAN24-40000-C", side="Buy", execution_time_ms=50
    )
    
    # Need to handle Config Loader
    with patch("bybit_options.services.hedger.bot.HedgerConfigLoader.load_from_db", new_callable=AsyncMock) as mock_load:
        mock_load.return_value = config
        with patch("bybit_options.services.hedger.bot.HedgerConfigLoader.save_to_db", new_callable=AsyncMock):
            yield bot_instance

@pytest.mark.asyncio
async def test_full_defensive_cycle(bot):
    """
    Step 1: Neutral State
    Step 2: H4 Breakout -> Switch to Defensive -> Buy Option
    Step 3: Stabilization -> Switch to Neutral -> Sell Option
    """
    
    # helper for db state
    def set_market_state(price: float, h4_high: float):
        # 1. Helper for get_current_price (from perpetual_ohlcv)
        # SignalDetector.get_current_price calls fetchval
        bot.db_pool.fetchval.return_value = price

        # 2. Helper for _check_fractal_breakout (from fractals_cache)
        # SignalDetector calls fetch
        # H4 High fractal
        fractals_h4 = [{"price": h4_high, "type": "HIGH"}]
        # H1 dummy
        fractals_h1 = [{"price": h4_high*1.1, "type": "HIGH"}] # Far away
        
        async def fetch_side_effect(query, *args):
            if not args: return []
            timeframe = args[0]
            if timeframe == "H4": 
                return fractals_h4
            if timeframe == "H1": return fractals_h1
            return []
            
        bot.db_pool.fetch.side_effect = fetch_side_effect

    # ==========================================
    # PHASE 1: NEUTRAL
    # ==========================================
    # Price 39k, H4 High 40k. No breakout.
    set_market_state(price=39000.0, h4_high=40000.0)
    
    await bot.check_and_hedge()
    
    assert bot.config.mode == HedgerMode.NEUTRAL
    bot.executor.place_option_order.assert_not_called()
    
    # ==========================================
    # PHASE 2: DEFENSIVE (Breakout)
    # ==========================================
    # Price 40100 > 40000. Breakout!
    set_market_state(price=40100.0, h4_high=40000.0)
    
    # Mock OptionSolver to give deterministic results if needed, 
    # but we can rely on real logic if imports work and connector data is good.
    # Connector returns "BTC-5JAN24-40000-C" which matches likely ATM for 40100.
    
    # Patch OptionSolver to ensure it picks the symbol we mocked in connector
    with patch("bybit_options.services.hedger.bot.OptionSolver") as mock_solver:
        mock_solver.get_target_expiry.return_value = "5JAN24"
        mock_solver.get_atm_strike.return_value = 40000
        mock_solver.format_symbol.return_value = "BTC-5JAN24-40000-C"
        
        await bot.check_and_hedge()
        
    assert bot.config.mode == HedgerMode.DEFENSIVE
    
    # Verify Option Order Placed
    bot.executor.place_option_order.assert_called_once()
    call_args = bot.executor.place_option_order.call_args[1]
    assert call_args["side"] == "Buy"
    assert call_args["symbol"] == "BTC-5JAN24-40000-C"
    
    # Verify DB Log for OPTIONS_BUY
    # execute is called on connection
    calls = bot.db_pool.connection.execute.call_args_list
    # We look for valid insert
    buy_log_found = False
    for call in calls:
        query = call[0][0]
        if "INSERT INTO hedge_actions" in query:
            # Check args
            args = call[0][1:]
            # args[4] is action_type (index 4 because 0 is query, then params start)
            # Actually call arguments are (query, $1, $2, ...)
            # So call[0] is (query, arg1, arg2...)
            if call.args[5] == "OPTIONS_BUY": # $5 is action_type? 
                # Query: VALUES ($1, $2, $3, $4, $5...)
                # $1: mode, $2: trigger, $3: delta_before, $4: target, $5: action_type
                # Let's count args carefully or just check if "OPTIONS_BUY" is in args
                if "OPTIONS_BUY" in call.args:
                    buy_log_found = True
                    break
    
    assert buy_log_found, "OPTIONS_BUY not logged to DB"
    
    # Reset mocks for next phase
    bot.executor.place_option_order.reset_mock()
    bot.db_pool.connection.execute.reset_mock()

    # ==========================================
    # PHASE 3: STABILIZATION (Return to Range)
    # ==========================================
    # Price 39500 < 40000. No Signal.
    set_market_state(price=39500.0, h4_high=40000.0)
    
    # Important: We must mock that we HOLD the option now
    bot.connector.get_positions.return_value = [
        {"symbol": "BTC-5JAN24-40000-C", "size": "0.1", "side": "Buy"}
    ]
    
    # Mock executor output for SELL
    bot.executor.place_option_order.return_value = OrderResult(
        order_id="opt_close_1", status="PLACED", symbol="BTC-5JAN24-40000-C", side="Sell"
    )

    await bot.check_and_hedge()
    
    assert bot.config.mode == HedgerMode.NEUTRAL
    
    # Verify Option Close Order
    bot.executor.place_option_order.assert_called_once()
    call_args = bot.executor.place_option_order.call_args[1]
    assert call_args["side"] == "Sell"
    assert call_args["symbol"] == "BTC-5JAN24-40000-C"
    
    # Verify DB Log for OPTIONS_CLOSE
    close_log_found = False
    possible_actions = ["OPTIONS_CLOSE"] 
    # Note: Logic in bot.py uses "OPTIONS_CLOSE" string?
    # Let's check bot.py source from previous turn... 
    # Yes: action_type="OPTIONS_CLOSE"
    
    for call in bot.db_pool.connection.execute.call_args_list:
        if "OPTIONS_CLOSE" in call.args:
            close_log_found = True
            break
            
    assert close_log_found, "OPTIONS_CLOSE not logged to DB"

