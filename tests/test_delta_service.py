import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from bybit_options.services.delta.database import LargeTrade, OrderbookSnapshot, DeltaMetrics
from bybit_options.services.delta.calculator import DeltaCalculator
from bybit_options.services.delta.ingestor import TradeIngestor

# Helper for async DB mock
class AsyncMockSession:
    def __init__(self):
        self.added = []
        self.committed = False
        self._results = iter([
            Decimal('100.0'), # Buy Vol
            Decimal('60.0'),  # Sell Vol
            10, # Count
            Decimal('0.05')   # Avg Imbalance
        ])
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def add(self, obj):
        self.added.append(obj)
        
    async def commit(self):
        self.committed = True
        
    async def execute(self, stmt):
        mock_result = MagicMock()
        try:
            val = next(self._results)
            mock_result.scalar.return_value = val
        except StopIteration:
            mock_result.scalar.return_value = None
        return mock_result

@pytest.mark.asyncio
async def test_large_trade_model():
    """Test LargeTrade model creation."""
    trade = LargeTrade(
        timestamp=datetime.now(),
        trade_id="12345",
        symbol="BTCUSDT",
        exchange="bybit",
        price=Decimal("50000.50"),
        quantity=Decimal("10.0"),
        side="Buy",
        market_type="perp"
    )
    assert trade.symbol == "BTCUSDT"
    assert trade.quantity == Decimal("10.0")

@pytest.mark.asyncio
async def test_calculator_logic():
    """Test DeltaCalculator aggregation logic."""
    session_factory = MagicMock(return_value=AsyncMockSession())
    calculator = DeltaCalculator(session_factory)
    
    await calculator.calculate_interval("BTCUSDT", "1m")
    
    # Check if a metrics object was created and added
    session = session_factory.return_value
    assert len(session.added) == 1
    metric = session.added[0]
    
    assert isinstance(metric, DeltaMetrics)
    assert metric.symbol == "BTCUSDT"
    assert metric.interval == "1m"
    assert metric.filtered_buy_volume == Decimal('100.0')
    assert metric.filtered_sell_volume == Decimal('60.0')
    assert metric.filtered_delta == Decimal('40.0') # 100 - 60
    assert metric.avg_imbalance == Decimal('0.05')

@pytest.mark.asyncio
async def test_ingestor_threshold():
    """Test TradeIngestor threshold logic."""
    ingestor = TradeIngestor(None, ["BTCUSDT"])
    
    # Mock data
    whale_trade = {
        "topic": "publicTrade.BTCUSDT",
        "data": [
            {"v": "10.0", "p": "50000", "S": "Buy", "T": 1670000000000, "i": "id1"}, # > 5 BTC
            {"v": "0.1", "p": "50000", "S": "Sell", "T": 1670000000000, "i": "id2"}   # < 5 BTC
        ]
    }
    
    await ingestor._on_trade_message(whale_trade)
    
    # Only whale trade should be buffered
    assert len(ingestor.buffer) == 1
    assert ingestor.buffer[0].quantity == Decimal("10.0")
    assert ingestor.buffer[0].side == "Buy"

