"""
Unit tests for DeltaHedgerBot.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from bybit_options.services.hedger.bot import DeltaHedgerBot, HedgerMode
from bybit_options.services.hedger.models import OrderResult, HedgerConfig, FractalSignal


class MockConnector:
    """Mock connector."""
    def __init__(self):
        self.get_ticker = AsyncMock()


class MockPool:
    """Mock asyncpg pool."""
    def __init__(self):
        self.acquire = MagicMock()
        self.connection = AsyncMock()
        self.acquire.return_value.__aenter__.return_value = self.connection


@pytest.fixture
def mock_connector():
    c = MockConnector()
    # Mock ticker for BTCUSDT
    c.get_ticker.return_value = {
        "symbol": "BTCUSDT",
        "bid1Price": "95000.0",
        "ask1Price": "95001.0"
    }
    return c


@pytest.fixture
def mock_db_pool():
    return MockPool()


@pytest.fixture
def bot(mock_connector, mock_db_pool):
    config = HedgerConfig(
        mode=HedgerMode.NEUTRAL,
        threshold=0.003,
        enabled=True,
        check_interval_seconds=10  # fast loop
    )
    # We pass config explicitly to avoid db load in simple tests
    bot_instance = DeltaHedgerBot(mock_connector, mock_db_pool, config=config)
    
    # Mock internal components to isolate bot logic
    bot_instance.monitor = AsyncMock()
    bot_instance.executor = AsyncMock()
    bot_instance.detector = AsyncMock()
    
    # Default detector behavior: No signal
    bot_instance.detector.detect.return_value = None
    
    # Mock db loader to avoid reading DB
    with patch("bybit_options.services.hedger.bot.HedgerConfigLoader.load_from_db", new_callable=AsyncMock) as mock_load:
        mock_load.return_value = config
        yield bot_instance


class TestDeltaHedgerBot:
    
    @pytest.mark.asyncio
    async def test_hedge_needed_long_exposure(self, bot):
        """Test hedging when delta is positive (Long exposure) -> Should SELL."""
        # 1. Setup: Delta = +0.5 BTC (Long)
        bot.monitor.get_portfolio_delta.return_value = 0.5
        
        # Mock executor result
        bot.executor.place_limit_order.return_value = OrderResult(
            status="PLACED", order_id="test_id", execution_time_ms=100
        )
        
        # 2. Execute
        await bot.check_and_hedge()
        
        # 3. Verify
        # Should place SELL order for 0.1 BTC (max_order_size cap, default is 0.1)
        # Deviation = 0.5. Max size = 0.1.
        bot.executor.place_limit_order.assert_called_once()
        call_args = bot.executor.place_limit_order.call_args[1]
        
        assert call_args["symbol"] == "BTCUSDT"
        assert call_args["side"] == "Sell"
        assert call_args["size"] == 0.1  # Capped by max_order_size
        
        # Verify DB logging
        bot.db_pool.connection.execute.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_hedge_needed_short_exposure(self, bot):
        """Test hedging when delta is negative (Short exposure) -> Should BUY."""
        # 1. Setup: Delta = -0.5 BTC (Short)
        bot.monitor.get_portfolio_delta.return_value = -0.5
        
        # Mock executor result
        bot.executor.place_limit_order.return_value = OrderResult(
            status="PLACED", order_id="test_id_buy"
        )
        
        # 2. Execute
        await bot.check_and_hedge()
        
        # 3. Verify
        bot.executor.place_limit_order.assert_called_once()
        call_args = bot.executor.place_limit_order.call_args[1]
        
        assert call_args["side"] == "Buy"
        assert call_args["size"] == 0.1
        
    @pytest.mark.asyncio
    async def test_below_threshold(self, bot):
        """Test no action when deviation is below threshold."""
        # Setup: Delta = 0.001 (Threshold 0.003)
        bot.monitor.get_portfolio_delta.return_value = 0.001
        
        # Execute
        await bot.check_and_hedge()
        
        # Verify
        bot.executor.place_limit_order.assert_not_called()
        bot.db_pool.connection.execute.assert_not_called()
        
    @pytest.mark.asyncio
    async def test_max_order_size_cap(self, bot):
        """Test that order size is capped by max_order_size."""
        # Config max size is default 0.1
        # Delta deviation = 0.05 (Valid, > threshold, < max)
        bot.monitor.get_portfolio_delta.return_value = 0.05
        
        bot.executor.place_limit_order.return_value = OrderResult(status="PLACED")
        
        await bot.check_and_hedge()
        
        call_args = bot.executor.place_limit_order.call_args[1]
        assert call_args["size"] == 0.05  # Not capped

    @pytest.mark.asyncio
    async def test_mode_switching(self, bot):
        """Test that bot calls detector and switches mode."""
        # Setup: H1 Breakout Signal
        bot.detector.detect.return_value = FractalSignal(
            timeframe="H1", 
            fractal_type="HIGH", 
            fractal_price=100.0, 
            current_price=101.0, 
            direction="LONG",
            is_breakout=True,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Initial mode NEUTRAL
        bot.config.mode = HedgerMode.NEUTRAL
        bot.monitor.get_portfolio_delta.return_value = 0.0
        
        with patch("bybit_options.services.hedger.bot.HedgerConfigLoader.save_to_db", new_callable=AsyncMock) as mock_save:
             await bot.check_and_hedge()
             
             # Verify detector called
             bot.detector.detect.assert_called_once()
             
             # Verify mode switched to DIRECTIONAL
             assert bot.config.mode == HedgerMode.DIRECTIONAL
             
             # Verify config saved
             # Verify config saved
             mock_save.assert_called_once()
             args = mock_save.call_args[0]
             saved_config = args[1]
             assert saved_config.mode == HedgerMode.DIRECTIONAL
             assert saved_config.target_delta == 0.01  # Default directional_bias_long
             assert bot.config.target_delta == 0.01
