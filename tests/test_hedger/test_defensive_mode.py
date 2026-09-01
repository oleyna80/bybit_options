import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from bybit_options.services.hedger.bot import DeltaHedgerBot, HedgerMode
from bybit_options.services.hedger.models import FractalSignal, OrderResult

class TestDefensiveMode(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.connector = AsyncMock()
        self.db_pool = MagicMock()
        # Mock acquire context manager for db_pool
        self.db_pool.acquire.return_value.__aenter__.return_value = AsyncMock()
        
        self.bot = DeltaHedgerBot(self.connector, self.db_pool)
        
        # Mock components
        self.bot.detector = AsyncMock()
        self.bot.monitor = AsyncMock()
        self.bot.monitor.get_portfolio_delta.return_value = 0.0
        self.bot.executor = AsyncMock()
        
        # Mock connector methods for options
        self.bot.connector.get_instruments_info.return_value = [
            {
                "symbol": "BTC-29DEC23-40000-C", 
                "priceFilter": {"tickSize": "0.5"}
            },
            {
                "symbol": "BTC-5JAN24-40000-C",
                "priceFilter": {"tickSize": "0.5"}
            },
            {
                "symbol": "BTC-5JAN24-39000-P",
                "priceFilter": {"tickSize": "0.5"}
            }
        ]
        self.bot.connector.get_tickers.return_value = [
            {"ask1Price": "150.0", "bid1Price": "140.0"}
        ]
        
        # Mock executor
        self.bot.executor.place_option_order.return_value = OrderResult(
            order_id="opt_123", status="PLACED", symbol="BTC-5JAN24-40000-C", side="Buy", execution_time_ms=100
        )
        self.bot.executor.place_limit_order.return_value = OrderResult(
            order_id="fut_123", status="PLACED", symbol="BTCUSDT", side="Sell"
        )
        
        # Mock get_ticker for futures (in case check_and_hedge proceeds to hedge delta)
        self.bot.connector.get_ticker.return_value = {"ask1Price": "40000", "bid1Price": "40000"}

    @patch("bybit_options.services.hedger.bot.OptionSolver")
    async def test_h4_long_breakout_buys_call(self, mock_solver):
        # Configure Mock Solver
        mock_solver.get_target_expiry.return_value = "5JAN24"
        mock_solver.get_atm_strike.return_value = 40000
        mock_solver.format_symbol.return_value = "BTC-5JAN24-40000-C"
        
        # 1. Setup H4 Long Breakout Signal
        signal = FractalSignal(
            timeframe="H4",
            is_breakout=True,
            direction="LONG",
            fractal_type="HIGH",
            current_price=40100.0,
            fractal_price=40000.0,
            timestamp=datetime.now(timezone.utc)
        )
        self.bot.detector.detect.return_value = signal
        # Ensure we are currently NOT in Defensive mode
        self.bot.config.mode = HedgerMode.NEUTRAL
        
        # 2. Run
        await self.bot.check_and_hedge()
        
        # 3. Assertions
        # Mode switch
        self.assertEqual(self.bot.config.mode, HedgerMode.DEFENSIVE)
        
        # Option Order Placed
        self.bot.connector.get_instruments_info.assert_called_once()
        mock_solver.get_atm_strike.assert_called_with(40100.0, base_coin="BTC")
        # Ensure it formatted a CALL
        mock_solver.format_symbol.assert_called_with("BTC", "5JAN24", 40000, "C")
        
        self.bot.executor.place_option_order.assert_called_once()
        kwargs = self.bot.executor.place_option_order.call_args[1]
        self.assertEqual(kwargs["symbol"], "BTC-5JAN24-40000-C")
        self.assertEqual(kwargs["side"], "Buy")
        # Size should come from config (default 0.1)
        self.assertEqual(kwargs["size"], 0.1)
        
    @patch("bybit_options.services.hedger.bot.OptionSolver")
    async def test_h4_short_breakout_buys_put(self, mock_solver):
        mock_solver.get_target_expiry.return_value = "5JAN24"
        mock_solver.get_atm_strike.return_value = 39000
        mock_solver.format_symbol.return_value = "BTC-5JAN24-39000-P"
        
        signal = FractalSignal(
            timeframe="H4",
            is_breakout=True,
            direction="SHORT",
            fractal_type="LOW",
            current_price=38900.0,
            fractal_price=39000.0,
            timestamp=datetime.now(timezone.utc)
        )
        self.bot.detector.detect.return_value = signal
        self.bot.config.mode = HedgerMode.NEUTRAL
        
        await self.bot.check_and_hedge()
        
        self.assertEqual(self.bot.config.mode, HedgerMode.DEFENSIVE)
        mock_solver.format_symbol.assert_called_with("BTC", "5JAN24", 39000, "P")
        
        kwargs = self.bot.executor.place_option_order.call_args[1]
        self.assertEqual(kwargs["symbol"], "BTC-5JAN24-39000-P")
        self.assertEqual(kwargs["side"], "Buy")

    async def test_existing_defensive_mode_does_not_rebuy(self):
        # If we are ALREADY in DEFENSIVE mode, we should NOT buy options again 
        # unless mode changed (which it didn't).
        
        signal = FractalSignal(
            timeframe="H4",
            is_breakout=True,
            direction="LONG",
            fractal_type="HIGH",
            current_price=40100.0,
            fractal_price=40000.0,
            timestamp=datetime.now(timezone.utc)
        )
        self.bot.detector.detect.return_value = signal
        self.bot.config.mode = HedgerMode.DEFENSIVE # Already Defensive
        
        await self.bot.check_and_hedge()
        
        # Should persist (refresh config etc) but check_and_hedge logic filters mode_changed
        # wait, bot updates mode if logic matches. 
        # If signal is H4 breakout, _determine_mode returns DEFENSIVE.
        # old mode was DEFENSIVE.
        # mode_changed = False.
        # So _buy_protection_options should NOT be called.
        
        self.bot.executor.place_option_order.assert_not_called()

    async def test_exit_defensive_mode_closes_options(self):
        """Test that switching from DEFENSIVE to NEUTRAL (no signal) closes options."""
        # 1. Start in DEFENSIVE mode
        self.bot.config.mode = HedgerMode.DEFENSIVE
        
        # 2. Detector returns NO signal (False Breakout / Return to Range)
        self.bot.detector.detect.return_value = None
        
        # 3. Mock existing protection options
        self.bot.connector.get_positions.return_value = [
            # Active Long Call
            {"symbol": "BTC-5JAN24-40000-C", "size": "0.1", "side": "Buy"},
            # Inactive position (size 0)
            {"symbol": "BTC-5JAN24-41000-C", "size": "0", "side": "Buy"},
            # Short position (should ignored if we only close Longs? Or maybe we panic close all?)
            # Logic says "Close all Long option positions found (assuming they were protective)."
            {"symbol": "BTC-5JAN24-50000-C", "size": "0.1", "side": "Sell"}
        ]
        
        # 4. Run
        await self.bot.check_and_hedge()
        
        # 5. Assertions
        # Mode switch to NEUTRAL
        self.assertEqual(self.bot.config.mode, HedgerMode.NEUTRAL)
        
        # Check get_positions called
        self.bot.connector.get_positions.assert_called_with(category="option", base_coin="BTC")
        
        # Check Sell order placed for the Long Call
        # We expect 1 call to place_option_order
        self.assertEqual(self.bot.executor.place_option_order.call_count, 1)
        
        kwargs = self.bot.executor.place_option_order.call_args[1]
        self.assertEqual(kwargs["symbol"], "BTC-5JAN24-40000-C")
        self.assertEqual(kwargs["side"], "Sell")
        self.assertEqual(kwargs["size"], 0.1)
        # Price should be bid * 0.9 = 140 * 0.9 = 126
        # And rounded to 0.5 -> 126.0
        self.assertEqual(kwargs["price"], 126.0)

if __name__ == "__main__":
    unittest.main()
