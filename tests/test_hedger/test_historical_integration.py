"""
Integration tests for Hedger Bot with "Historical" data scenarios.

Tests the interaction between SignalDetector, Bot logic, and Mocked DB.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from bybit_options.services.hedger.bot import DeltaHedgerBot, HedgerMode
from bybit_options.services.hedger.models import HedgerConfig

class MockConnector:
    def __init__(self):
        self.get_ticker = AsyncMock()

class MockPool:
    """Mock asyncpg Pool with direct fetch methods."""
    def __init__(self):
        self.acquire = MagicMock()
        self.connection = AsyncMock()
        self.acquire.return_value.__aenter__.return_value = self.connection
        
        # Methods used by SignalDetector
        self.fetch = AsyncMock()
        self.fetchval = AsyncMock()

@pytest.fixture
def mock_db_pool():
    return MockPool()

@pytest.fixture
def bot(mock_db_pool):
    connector = MockConnector()
    connector.get_ticker.return_value = {"bid1Price": "100000", "ask1Price": "100001"}
    
    config = HedgerConfig(
        mode=HedgerMode.NEUTRAL, 
        enabled=True, 
        check_interval_seconds=10,
        directional_bias_long=0.01,
        directional_bias_short=-0.01
    )
    
    # Initialize bot with mocked connector and pool
    # Note: SignalDetector is initialized inside __init__ using this pool
    bot_instance = DeltaHedgerBot(connector, mock_db_pool, config=config)
    
    # Mock other components we don't care about detecting logic wise
    bot_instance.monitor = AsyncMock()
    bot_instance.executor = AsyncMock()
    
    # We DO NOT mock bot_instance.detector, we want to test its logic!
    
    with patch("bybit_options.services.hedger.bot.HedgerConfigLoader.load_from_db", new_callable=AsyncMock) as mock_load:
        mock_load.return_value = config
        
        with patch("bybit_options.services.hedger.bot.HedgerConfigLoader.save_to_db", new_callable=AsyncMock):
            yield bot_instance

@pytest.mark.asyncio
async def test_bullish_breakout_scenario(bot):
    """
    Scenario:
    1. Ranges Established (H1 High = 100k, H4 High = 105k)
    2. Price = 95k (Neutral)
    3. Price = 101k (Breakout H1) -> Switch to DIRECTIONAL, target=+0.01
    4. Price = 99k (Retrace) -> Switch to NEUTRAL, target=0.0
    """
    
    # Helper to set db state for SignalDetector
    def set_db_state(current_price, h1_fractals, h4_fractals):
        bot.db_pool.fetchval.return_value = current_price # For get_current_price
        
        # Side effect for fetch() to return different fractals based on timeframe arg
        async def fetch_side_effect(query, *args):
            # args[0] is timeframe because query takes $1
            timeframe = args[0]
            if timeframe == "H4": return h4_fractals
            if timeframe == "H1": return h1_fractals
            return []
            
        bot.db_pool.fetch.side_effect = fetch_side_effect
    
    fractals_h1 = [{"price": 100000.0, "type": "HIGH"}, {"price": 90000.0, "type": "LOW"}]
    fractals_h4 = [{"price": 105000.0, "type": "HIGH"}, {"price": 85000.0, "type": "LOW"}]
    
    # --- Step 1: Neutral ---
    set_db_state(95000.0, fractals_h1, fractals_h4)
    bot.monitor.get_portfolio_delta.return_value = 0.0
    
    await bot.check_and_hedge()
    
    assert bot.config.mode == HedgerMode.NEUTRAL
    assert bot.config.target_delta == 0.0
    
    # --- Step 2: Breakout H1 ---
    # Price 101k > H1 High (100k)
    set_db_state(101000.0, fractals_h1, fractals_h4)
    
    await bot.check_and_hedge()
    
    assert bot.config.mode == HedgerMode.DIRECTIONAL
    assert bot.config.target_delta == 0.01 # Long bias
    
    # --- Step 3: Retrace ---
    # Price 99k (Inside range)
    set_db_state(99000.0, fractals_h1, fractals_h4)
    
    await bot.check_and_hedge()
    
    assert bot.config.mode == HedgerMode.NEUTRAL
    assert bot.config.target_delta == 0.0

@pytest.mark.asyncio
async def test_bearish_breakout_scenario(bot):
    """
    Scenario:
    1. Ranges (H1 Low = 90k)
    2. Price = 89k (Breakout H1 Low) -> DIRECTIONAL SHORT
    """
    fractals_h1 = [{"price": 100000.0, "type": "HIGH"}, {"price": 90000.0, "type": "LOW"}]
    # H4 wide enough
    fractals_h4 = [{"price": 110000.0, "type": "HIGH"}, {"price": 80000.0, "type": "LOW"}]

    def set_db_state(current_price):
        bot.db_pool.fetchval.return_value = current_price
        async def fetch_side_effect(query, *args):
            timeframe = args[0]
            if timeframe == "H4": return fractals_h4
            if timeframe == "H1": return fractals_h1
            return []
        bot.db_pool.fetch.side_effect = fetch_side_effect

    # Price Drops to 89k
    set_db_state(89000.0)
    bot.monitor.get_portfolio_delta.return_value = 0.0
    
    await bot.check_and_hedge()
    
    assert bot.config.mode == HedgerMode.DIRECTIONAL
    assert bot.config.target_delta == -0.01 # Short bias
