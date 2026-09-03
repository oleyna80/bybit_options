"""
Unit tests for PositionMonitor.

Tests the delta calculation logic with mocked connector.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import List, Dict, Any

from bybit_options.services.hedger.position_monitor import PositionMonitor, PositionFetchError


class MockConnector:
    """Mock connector for testing."""
    
    def __init__(self):
        self.get_positions = AsyncMock()


@pytest.fixture
def mock_connector():
    """Create a mock connector."""
    return MockConnector()


@pytest.fixture
def position_monitor(mock_connector):
    """Create PositionMonitor with mock connector."""
    return PositionMonitor(mock_connector, base_coin="BTC")


class TestPositionMonitorBasic:
    """Basic tests for PositionMonitor."""
    
    @pytest.mark.asyncio
    async def test_empty_positions(self, position_monitor, mock_connector):
        """Test with no positions."""
        mock_connector.get_positions.return_value = []
        
        delta = await position_monitor.get_portfolio_delta()
        
        assert delta == 0.0
        assert position_monitor.last_delta == 0.0
    
    @pytest.mark.asyncio
    async def test_neutral_delta(self, position_monitor, mock_connector):
        """Test with balanced positions (delta neutral)."""
        # Options: +0.5 delta
        # Futures: -0.5 delta
        mock_connector.get_positions.side_effect = [
            # Options call
            [{"symbol": "BTC-100000-C", "size": "1.0", "delta": "0.5", "side": "Buy"}],
            # Futures call  
            [{"symbol": "BTCUSDT", "size": "0.5", "side": "Sell"}],
        ]
        
        delta = await position_monitor.get_portfolio_delta()
        
        assert delta == 0.0
        assert position_monitor.last_options_delta == 0.5
        assert position_monitor.last_futures_delta == -0.5


class TestOptionsPositions:
    """Test options delta calculation."""
    
    @pytest.mark.asyncio
    async def test_long_call_position(self, position_monitor, mock_connector):
        """Test LONG CALL (positive delta)."""
        mock_connector.get_positions.side_effect = [
            # Options
            [{"symbol": "BTC-100000-C", "size": "1.0", "delta": "0.6", "side": "Buy"}],
            # Futures
            [],
        ]
        
        delta = await position_monitor.get_portfolio_delta()
        
        # LONG CALL: size(1.0) * delta(0.6) = 0.6
        assert delta == 0.6
    
    @pytest.mark.asyncio
    async def test_long_put_position(self, position_monitor, mock_connector):
        """Test LONG PUT (negative delta)."""
        mock_connector.get_positions.side_effect = [
            # Options
            [{"symbol": "BTC-90000-P", "size": "1.0", "delta": "-0.4", "side": "Buy"}],
            # Futures
            [],
        ]
        
        delta = await position_monitor.get_portfolio_delta()
        
        # LONG PUT: size(1.0) * delta(-0.4) = -0.4
        assert delta == -0.4
    
    @pytest.mark.asyncio
    async def test_short_call_position(self, position_monitor, mock_connector):
        """Test SHORT CALL (negative delta, inverted)."""
        mock_connector.get_positions.side_effect = [
            # Options - SHORT (size negative)
            [{"symbol": "BTC-110000-C", "size": "-1.0", "delta": "0.3", "side": "Sell"}],
            # Futures
            [],
        ]
        
        delta = await position_monitor.get_portfolio_delta()
        
        # SHORT CALL: size(-1.0) * delta(0.3) = -0.3
        assert delta == -0.3
    
    @pytest.mark.asyncio
    async def test_short_put_position(self, position_monitor, mock_connector):
        """Test SHORT PUT (positive delta, inverted)."""
        mock_connector.get_positions.side_effect = [
            # Options - SHORT (size negative)
            [{"symbol": "BTC-85000-P", "size": "-1.0", "delta": "-0.35", "side": "Sell"}],
            # Futures
            [],
        ]
        
        delta = await position_monitor.get_portfolio_delta()
        
        # SHORT PUT: size(-1.0) * delta(-0.35) = 0.35
        assert delta == 0.35
    
    @pytest.mark.asyncio
    async def test_iron_condor_position(self, position_monitor, mock_connector):
        """Test Iron Condor (4 legs, near delta neutral)."""
        mock_connector.get_positions.side_effect = [
            # Options - Iron Condor
            [
                # Long Put (OTM)
                {"symbol": "BTC-85000-P", "size": "1.0", "delta": "-0.15"},
                # Short Put (nearer ATM)
                {"symbol": "BTC-90000-P", "size": "-1.0", "delta": "-0.30"},
                # Short Call (nearer ATM)
                {"symbol": "BTC-110000-C", "size": "-1.0", "delta": "0.25"},
                # Long Call (OTM)
                {"symbol": "BTC-115000-C", "size": "1.0", "delta": "0.10"},
            ],
            # Futures
            [],
        ]
        
        delta = await position_monitor.get_portfolio_delta()
        
        # Expected:
        # Long Put: 1.0 * -0.15 = -0.15
        # Short Put: -1.0 * -0.30 = +0.30
        # Short Call: -1.0 * 0.25 = -0.25
        # Long Call: 1.0 * 0.10 = +0.10
        # Total: -0.15 + 0.30 - 0.25 + 0.10 = 0.0
        assert abs(delta) < 0.001  # Near zero


class TestFuturesPositions:
    """Test futures delta calculation."""
    
    @pytest.mark.asyncio
    async def test_long_futures(self, position_monitor, mock_connector):
        """Test LONG futures position."""
        mock_connector.get_positions.side_effect = [
            # Options
            [],
            # Futures
            [{"symbol": "BTCUSDT", "size": "0.5", "side": "Buy"}],
        ]
        
        delta = await position_monitor.get_portfolio_delta()
        
        assert delta == 0.5
    
    @pytest.mark.asyncio
    async def test_short_futures(self, position_monitor, mock_connector):
        """Test SHORT futures position."""
        mock_connector.get_positions.side_effect = [
            # Options
            [],
            # Futures
            [{"symbol": "BTCUSDT", "size": "0.3", "side": "Sell"}],
        ]
        
        delta = await position_monitor.get_portfolio_delta()
        
        assert delta == -0.3


class TestCombinedPositions:
    """Test combined options + futures."""
    
    @pytest.mark.asyncio
    async def test_hedged_position(self, position_monitor, mock_connector):
        """Test options hedged with futures."""
        mock_connector.get_positions.side_effect = [
            # Options: Delta +0.7
            [
                {"symbol": "BTC-95000-C", "size": "2.0", "delta": "0.5"},  # +1.0
                {"symbol": "BTC-90000-P", "size": "-1.0", "delta": "-0.3"},  # +0.3
            ],
            # Futures: Short 1.0 = -1.0 delta
            [{"symbol": "BTCUSDT", "size": "1.0", "side": "Sell"}],
        ]
        
        delta = await position_monitor.get_portfolio_delta()
        
        # Options: 2.0*0.5 + (-1.0)*(-0.3) = 1.0 + 0.3 = 1.3
        # Futures: -1.0
        # Total: 0.3
        assert abs(delta - 0.3) < 0.001
    
    @pytest.mark.asyncio
    async def test_detailed_delta(self, position_monitor, mock_connector):
        """Test get_detailed_delta method."""
        mock_connector.get_positions.side_effect = [
            # Options
            [{"symbol": "BTC-100000-C", "size": "1.0", "delta": "0.5"}],
            # Futures
            [{"symbol": "BTCUSDT", "size": "0.2", "side": "Buy"}],
        ]
        
        details = await position_monitor.get_detailed_delta()
        
        assert details["options_delta"] == 0.5
        assert details["futures_delta"] == 0.2
        assert details["total_delta"] == 0.7
        assert details["base_coin"] == "BTC"
        assert details["is_net_long"] is True
        assert details["is_net_short"] is False
        assert details["is_neutral"] is False


class TestErrorHandling:
    """Test error handling."""
    
    @pytest.mark.asyncio
    async def test_connector_error_options(self, position_monitor, mock_connector):
        """Test error handling when options fetch fails."""
        mock_connector.get_positions.side_effect = [
            Exception("API Error"),  # Options fail
            [{"symbol": "BTCUSDT", "size": "0.1", "side": "Buy"}],  # Futures OK
        ]
        
        # Should raise PositionFetchError instead of returning partial result
        with pytest.raises(PositionFetchError, match="Options fetch failed"):
            await position_monitor.get_portfolio_delta()

    @pytest.mark.asyncio
    async def test_connector_error_futures(self, position_monitor, mock_connector):
        """Test error handling when futures fetch fails."""
        mock_connector.get_positions.side_effect = [
            [],  # Options OK
            Exception("API Error"),  # Futures fail
        ]
        
        # Should raise PositionFetchError
        with pytest.raises(PositionFetchError, match="Futures fetch failed"):
            await position_monitor.get_portfolio_delta()
    
    @pytest.mark.asyncio
    async def test_invalid_position_data(self, position_monitor, mock_connector):
        """Test handling of invalid position data."""
        mock_connector.get_positions.side_effect = [
            # Options with invalid data
            [
                {"symbol": "BTC-100000-C", "size": "invalid", "delta": "0.5"},
                {"symbol": "BTC-95000-C", "size": "1.0", "delta": "0.4"},  # Valid
            ],
            # Futures
            [],
        ]
        
        delta = await position_monitor.get_portfolio_delta()
        
        # Only valid position should count
        assert delta == 0.4
    
    @pytest.mark.asyncio
    async def test_zero_size_position(self, position_monitor, mock_connector):
        """Test that zero-size positions are ignored."""
        mock_connector.get_positions.side_effect = [
            # Options with zero size
            [
                {"symbol": "BTC-100000-C", "size": "0", "delta": "0.5"},
                {"symbol": "BTC-95000-C", "size": "1.0", "delta": "0.4"},
            ],
            # Futures
            [],
        ]
        
        delta = await position_monitor.get_portfolio_delta()
        
        # Only non-zero position
        assert delta == 0.4


class TestEdgeCases:
    """Edge case tests."""
    
    @pytest.mark.asyncio
    async def test_very_small_delta(self, position_monitor, mock_connector):
        """Test very small delta is not rounded to zero."""
        mock_connector.get_positions.side_effect = [
            [{"symbol": "BTC-100000-C", "size": "0.001", "delta": "0.001"}],
            [],
        ]
        
        delta = await position_monitor.get_portfolio_delta()
        
        assert delta == 0.000001
    
    @pytest.mark.asyncio
    async def test_large_position(self, position_monitor, mock_connector):
        """Test large position size."""
        mock_connector.get_positions.side_effect = [
            [{"symbol": "BTC-100000-C", "size": "100", "delta": "0.5"}],
            [{"symbol": "BTCUSDT", "size": "50", "side": "Sell"}],
        ]
        
        delta = await position_monitor.get_portfolio_delta()
        
        # Options: 100 * 0.5 = 50
        # Futures: -50
        # Total: 0
        assert delta == 0.0
