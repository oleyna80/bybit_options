"""
Unit tests for OrderExecutor.

Tests the order placement logic with mocked connector.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch
from typing import Dict, Any

from bybit_options.services.hedger.order_executor import (
    OrderExecutor,
    RateLimitError,
    APIError,
)
from bybit_options.services.hedger.models import OrderResult


class MockResponse:
    """Mock aiohttp response."""
    
    def __init__(self, data: Dict[str, Any]):
        self._data = data
    
    async def json(self):
        return self._data
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        pass


class MockSession:
    """Mock aiohttp session."""
    
    def __init__(self):
        self.post = MagicMock()
        self._response_data = {"retCode": 0, "result": {"orderId": "test123"}}
    
    def set_response(self, data: Dict[str, Any]):
        self._response_data = data
        self.post.return_value = MockResponse(data)


class MockRateLimiter:
    """Mock rate limiter."""
    
    def __init__(self):
        self.acquire = AsyncMock()


class MockConnector:
    """Mock connector for testing."""
    
    def __init__(self):
        self.api_key = "test_api_key"
        self.api_secret = "test_api_secret"
        self.recv_window = "5000"
        self.rate_limiter = MockRateLimiter()
        self._mock_session = MockSession()
        self._get_server_time = AsyncMock(return_value="1705334400000")
    
    def _get_base_url(self) -> str:
        return "https://api-testnet.bybit.com"
    
    def _generate_signature(self, timestamp: str, params_string: str) -> str:
        return "mock_signature"
    
    @property
    def _session(self):
        return self._mock_session
    
    def set_api_response(self, data: Dict[str, Any]):
        """Set the API response for testing."""
        self._mock_session.set_response(data)


@pytest.fixture
def mock_connector():
    """Create a mock connector."""
    return MockConnector()


@pytest.fixture
def order_executor(mock_connector):
    """Create OrderExecutor with mock connector."""
    return OrderExecutor(
        mock_connector,
        max_retries=3,
        base_delay=0.01,  # Short delay for tests
        max_delay=0.1
    )


class TestOrderExecutorBasic:
    """Basic tests for OrderExecutor."""
    
    @pytest.mark.asyncio
    async def test_successful_order(self, order_executor, mock_connector):
        """Test successful order placement."""
        mock_connector.set_api_response({
            "retCode": 0,
            "retMsg": "OK",
            "result": {"orderId": "order123", "orderLinkId": ""}
        })
        
        result = await order_executor.place_limit_order(
            symbol="BTCUSDT",
            side="Buy",
            size=0.01,
            price=95000.0
        )
        
        assert result.is_success
        assert result.order_id == "order123"
        assert result.status == "PLACED"
        assert result.symbol == "BTCUSDT"
        assert result.side == "Buy"
    
    @pytest.mark.asyncio
    async def test_side_normalization(self, order_executor, mock_connector):
        """Test that side is normalized correctly."""
        mock_connector.set_api_response({
            "retCode": 0,
            "result": {"orderId": "order123"}
        })
        
        # Test lowercase
        result = await order_executor.place_limit_order(
            symbol="BTCUSDT",
            side="buy",
            size=0.01,
            price=95000.0
        )
        assert result.side == "Buy"
        
        # Test uppercase
        result = await order_executor.place_limit_order(
            symbol="BTCUSDT",
            side="SELL",
            size=0.01,
            price=95000.0
        )
        assert result.side == "Sell"
    
    @pytest.mark.asyncio
    async def test_invalid_side(self, order_executor):
        """Test invalid side returns error."""
        result = await order_executor.place_limit_order(
            symbol="BTCUSDT",
            side="invalid",
            size=0.01,
            price=95000.0
        )
        
        assert result.is_failed
        assert "Invalid side" in result.error


class TestRetryLogic:
    """Test retry logic with exponential backoff."""
    
    @pytest.mark.asyncio
    async def test_retry_on_rate_limit(self, mock_connector):
        """Test retry on rate limit error."""
        executor = OrderExecutor(
            mock_connector,
            max_retries=3,
            base_delay=0.01,
            max_delay=0.1
        )
        
        # First call: rate limit, second call: success
        responses = [
            {"retCode": 10006, "retMsg": "Rate limited"},
            {"retCode": 0, "result": {"orderId": "order123"}}
        ]
        call_count = [0]
        
        def mock_post(*args, **kwargs):
            response = responses[min(call_count[0], len(responses) - 1)]
            call_count[0] += 1
            return MockResponse(response)
        
        mock_connector._mock_session.post = mock_post
        
        result = await executor.place_limit_order(
            symbol="BTCUSDT",
            side="Buy",
            size=0.01,
            price=95000.0
        )
        
        assert result.is_success
        assert call_count[0] == 2  # First failed, second succeeded
    
    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, mock_connector):
        """Test max retries exceeded."""
        executor = OrderExecutor(
            mock_connector,
            max_retries=2,
            base_delay=0.01,
            max_delay=0.1
        )
        
        # Always return rate limit
        mock_connector.set_api_response({
            "retCode": 10006,
            "retMsg": "Rate limited"
        })
        
        result = await executor.place_limit_order(
            symbol="BTCUSDT",
            side="Buy",
            size=0.01,
            price=95000.0
        )
        
        assert result.is_failed
        assert "Max retries" in result.error
    
    @pytest.mark.asyncio
    async def test_exponential_backoff_calculation(self, order_executor):
        """Test exponential backoff delay calculation."""
        # base_delay = 0.01, max_delay = 0.1
        
        assert order_executor._calculate_delay(0) == 0.01  # 0.01 * 2^0
        assert order_executor._calculate_delay(1) == 0.02  # 0.01 * 2^1
        assert order_executor._calculate_delay(2) == 0.04  # 0.01 * 2^2
        assert order_executor._calculate_delay(3) == 0.08  # 0.01 * 2^3
        assert order_executor._calculate_delay(4) == 0.1   # capped at max_delay


class TestAPIErrors:
    """Test API error handling."""
    
    @pytest.mark.asyncio
    async def test_non_retryable_error(self, order_executor, mock_connector):
        """Test non-retryable API error."""
        mock_connector.set_api_response({
            "retCode": 10001,  # Generic error, not in RETRYABLE_CODES
            "retMsg": "Invalid parameter"
        })
        
        result = await order_executor.place_limit_order(
            symbol="BTCUSDT",
            side="Buy",
            size=0.01,
            price=95000.0
        )
        
        assert result.is_failed
        assert "Invalid parameter" in result.error
    
    @pytest.mark.asyncio
    async def test_retryable_error_codes(self, mock_connector):
        """Test retryable error codes."""
        executor = OrderExecutor(
            mock_connector,
            max_retries=2,
            base_delay=0.01,
            max_delay=0.1
        )
        
        # Test error code 10002 (timeout) - should retry
        responses = [
            {"retCode": 10002, "retMsg": "Request timeout"},
            {"retCode": 0, "result": {"orderId": "order123"}}
        ]
        call_count = [0]
        
        def mock_post(*args, **kwargs):
            response = responses[min(call_count[0], len(responses) - 1)]
            call_count[0] += 1
            return MockResponse(response)
        
        mock_connector._mock_session.post = mock_post
        
        result = await executor.place_limit_order(
            symbol="BTCUSDT",
            side="Buy",
            size=0.01,
            price=95000.0
        )
        
        assert result.is_success


class TestOptionOrders:
    """Test option order placement."""
    
    @pytest.mark.asyncio
    async def test_option_limit_order(self, order_executor, mock_connector):
        """Test option limit order."""
        mock_connector.set_api_response({
            "retCode": 0,
            "result": {"orderId": "opt123"}
        })
        
        result = await order_executor.place_option_order(
            symbol="BTC-100000-C",
            side="Buy",
            size=1.0,
            price=0.05
        )
        
        assert result.is_success
        assert result.order_id == "opt123"
    
    @pytest.mark.asyncio
    async def test_option_limit_requires_price(self, order_executor):
        """Test that limit orders require price."""
        result = await order_executor.place_option_order(
            symbol="BTC-100000-C",
            side="Buy",
            size=1.0,
            price=None,
            order_type="Limit"
        )
        
        assert result.is_failed
        assert "Price required" in result.error


class TestCancelOrder:
    """Test order cancellation."""
    
    @pytest.mark.asyncio
    async def test_cancel_order_success(self, order_executor, mock_connector):
        """Test successful order cancellation."""
        mock_connector.set_api_response({
            "retCode": 0,
            "result": {"orderId": "order123"}
        })
        
        # Need to mock session.post for cancel endpoint
        mock_connector._mock_session.post = MagicMock(return_value=MockResponse({
            "retCode": 0,
            "result": {"orderId": "order123"}
        }))
        
        result = await order_executor.cancel_order(
            symbol="BTCUSDT",
            order_id="order123"
        )
        
        assert result.status == "CANCELLED"
    
    @pytest.mark.asyncio
    async def test_cancel_requires_id(self, order_executor):
        """Test that cancel requires order ID."""
        result = await order_executor.cancel_order(
            symbol="BTCUSDT"
        )
        
        assert result.is_failed
        assert "order_id or order_link_id required" in result.error


class TestExecutionTime:
    """Test execution time tracking."""
    
    @pytest.mark.asyncio
    async def test_execution_time_recorded(self, order_executor, mock_connector):
        """Test that execution time is recorded."""
        mock_connector.set_api_response({
            "retCode": 0,
            "result": {"orderId": "order123"}
        })
        
        result = await order_executor.place_limit_order(
            symbol="BTCUSDT",
            side="Buy",
            size=0.01,
            price=95000.0
        )
        
        assert result.execution_time_ms is not None
        assert result.execution_time_ms >= 0
