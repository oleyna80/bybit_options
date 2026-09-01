"""
Delta Hedger Bot - Order Executor

Исполнение ордеров через Bybit API с retry логикой.
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, Optional, Protocol

from .models import OrderResult

logger = logging.getLogger(__name__)


class RateLimitError(Exception):
    """Rate limit exceeded."""
    pass


class APIError(Exception):
    """Bybit API error."""
    
    def __init__(self, message: str, code: int = 0, retryable: bool = False):
        super().__init__(message)
        self.code = code
        self.retryable = retryable


class ConnectorProtocol(Protocol):
    """Protocol for connector (for type hints)."""
    
    api_key: str
    api_secret: str
    
    def _get_base_url(self) -> str:
        ...
    
    def _generate_signature(self, timestamp: str, params_string: str) -> str:
        ...
    
    async def _get_server_time(self) -> str:
        ...
    
    @property
    def rate_limiter(self) -> Any:
        ...
    
    @property
    def _session(self) -> Any:
        ...
    
    @property
    def recv_window(self) -> str:
        ...


class OrderExecutor:
    """
    Исполнение ордеров через Bybit API.
    
    Features:
    - Limit orders only (по требованию трейдера)
    - Retry logic с exponential backoff
    - Логирование всех операций
    - Поддержка фьючерсов и опционов
    
    Usage:
        executor = OrderExecutor(connector)
        result = await executor.place_limit_order(
            symbol="BTCUSDT",
            side="BUY",
            size=0.01,
            price=95000.0
        )
        if result.is_success:
            print(f"Order placed: {result.order_id}")
    """
    
    # Bybit error codes that are retryable
    RETRYABLE_CODES = {
        10002,  # Request timeout
        10006,  # Too many requests
        10016,  # Server busy
        33004,  # Order not found (race condition)
    }
    
    def __init__(
        self,
        connector: ConnectorProtocol,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 10.0
    ):
        """
        Инициализирует OrderExecutor.
        
        Args:
            connector: Bybit connector instance
            max_retries: Максимальное количество повторов
            base_delay: Базовая задержка между повторами (секунды)
            max_delay: Максимальная задержка (секунды)
        """
        self.connector = connector
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    async def place_limit_order(
        self,
        symbol: str,
        side: str,
        size: float,
        price: float,
        category: str = "linear",
        time_in_force: str = "GTC",
        reduce_only: bool = False,
        order_link_id: Optional[str] = None
    ) -> OrderResult:
        """
        Размещает лимитный ордер с retry логикой.
        
        Args:
            symbol: Trading pair (e.g., "BTCUSDT" for futures, "BTC-100000-C" for options)
            side: "Buy" or "Sell"
            size: Order size in base currency
            price: Limit price
            category: "linear" for futures, "option" for options
            time_in_force: "GTC" (Good Till Cancel), "IOC", "FOK"
            reduce_only: If True, order can only reduce position
            order_link_id: Custom order ID for tracking
            
        Returns:
            OrderResult with order_id and status
        """
        start_time = time.time()
        
        # Normalize side
        side_normalized = side.capitalize()  # "buy" -> "Buy", "SELL" -> "Sell"
        if side_normalized not in ("Buy", "Sell"):
            return OrderResult(
                status="FAILED",
                symbol=symbol,
                side=side,
                error=f"Invalid side: {side}. Must be 'Buy' or 'Sell'"
            )
        
        # Prepare order params
        params = {
            "category": category,
            "symbol": symbol,
            "side": side_normalized,
            "orderType": "Limit",
            "qty": str(size),
            "price": str(price),
            "timeInForce": time_in_force,
        }
        
        if reduce_only:
            params["reduceOnly"] = True
        
        if order_link_id:
            params["orderLinkId"] = order_link_id
        
        # Execute with retries
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                result = await self._execute_order(params)
                
                execution_time_ms = int((time.time() - start_time) * 1000)
                
                return OrderResult(
                    order_id=result.get("orderId"),
                    status="PLACED",
                    symbol=symbol,
                    side=side_normalized,
                    price=price,
                    size=size,
                    execution_time_ms=execution_time_ms
                )
                
            except RateLimitError as e:
                delay = self._calculate_delay(attempt)
                logger.warning(
                    f"Rate limited on attempt {attempt + 1}/{self.max_retries}, "
                    f"waiting {delay:.1f}s"
                )
                await asyncio.sleep(delay)
                last_error = e
                
            except APIError as e:
                if e.retryable and attempt < self.max_retries - 1:
                    delay = self._calculate_delay(attempt)
                    logger.warning(
                        f"Retryable error on attempt {attempt + 1}/{self.max_retries}: {e}, "
                        f"waiting {delay:.1f}s"
                    )
                    await asyncio.sleep(delay)
                    last_error = e
                else:
                    # Non-retryable error
                    execution_time_ms = int((time.time() - start_time) * 1000)
                    return OrderResult(
                        status="FAILED",
                        symbol=symbol,
                        side=side_normalized,
                        error=str(e),
                        execution_time_ms=execution_time_ms
                    )
                    
            except Exception as e:
                logger.error(f"Unexpected error placing order: {e}")
                execution_time_ms = int((time.time() - start_time) * 1000)
                return OrderResult(
                    status="FAILED",
                    symbol=symbol,
                    side=side_normalized,
                    error=str(e),
                    execution_time_ms=execution_time_ms
                )
        
        # Max retries exceeded
        execution_time_ms = int((time.time() - start_time) * 1000)
        return OrderResult(
            status="FAILED",
            symbol=symbol,
            side=side_normalized,
            error=f"Max retries ({self.max_retries}) exceeded. Last error: {last_error}",
            execution_time_ms=execution_time_ms
        )
    
    async def place_option_order(
        self,
        symbol: str,
        side: str,
        size: float,
        price: Optional[float] = None,
        order_type: str = "Limit"
    ) -> OrderResult:
        """
        Размещает ордер на опцион.
        
        Args:
            symbol: Option symbol (e.g., "BTC-100000-C")
            side: "Buy" or "Sell"
            size: Number of contracts
            price: Limit price (required for Limit orders)
            order_type: "Limit" or "Market"
            
        Returns:
            OrderResult
        """
        if order_type == "Limit" and price is None:
            return OrderResult(
                status="FAILED",
                symbol=symbol,
                side=side,
                error="Price required for Limit orders"
            )
        
        if order_type == "Limit":
            return await self.place_limit_order(
                symbol=symbol,
                side=side,
                size=size,
                price=price,
                category="option"
            )
        else:
            # Market order for options
            return await self._place_market_order(
                symbol=symbol,
                side=side,
                size=size,
                category="option"
            )
    
    async def cancel_order(
        self,
        symbol: str,
        order_id: Optional[str] = None,
        order_link_id: Optional[str] = None,
        category: str = "linear"
    ) -> OrderResult:
        """
        Отменяет ордер.
        
        Args:
            symbol: Trading pair
            order_id: Bybit order ID
            order_link_id: Custom order ID
            category: "linear" or "option"
            
        Returns:
            OrderResult
        """
        if not order_id and not order_link_id:
            return OrderResult(
                status="FAILED",
                symbol=symbol,
                error="Either order_id or order_link_id required"
            )
        
        params = {
            "category": category,
            "symbol": symbol,
        }
        
        if order_id:
            params["orderId"] = order_id
        if order_link_id:
            params["orderLinkId"] = order_link_id
        
        try:
            result = await self._cancel_order_request(params)
            return OrderResult(
                order_id=result.get("orderId"),
                status="CANCELLED",
                symbol=symbol
            )
        except Exception as e:
            return OrderResult(
                status="FAILED",
                symbol=symbol,
                error=str(e)
            )
    
    async def _execute_order(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Выполняет запрос на создание ордера.
        
        Raises:
            RateLimitError: При превышении лимита запросов
            APIError: При ошибке API
        """
        # TODO: Warning fixed: Refactor this method to use a generic `connector.send_signed_request` 
        # to avoid abstraction leak (direct usage of connector attributes like _session).
        
        # Acquire rate limiter
        await self.connector.rate_limiter.acquire()
        
        # Prepare request
        timestamp = await self.connector._get_server_time()
        body_json = json.dumps(params)
        signature = self.connector._generate_signature(timestamp, body_json)
        
        headers = {
            "X-BAPI-API-KEY": self.connector.api_key,
            "X-BAPI-SIGN": signature,
            "X-BAPI-SIGN-TYPE": "2",
            "X-BAPI-TIMESTAMP": timestamp,
            "X-BAPI-RECV-WINDOW": self.connector.recv_window,
            "Content-Type": "application/json",
        }
        
        url = f"{self.connector._get_base_url()}/v5/order/create"
        
        try:
            async with self.connector._session.post(
                url, 
                headers=headers, 
                data=body_json
            ) as resp:
                data = await resp.json()
                
                ret_code = data.get("retCode", -1)
                
                if ret_code == 0:
                    return data.get("result", {})
                elif ret_code == 10006:  # Rate limit
                    raise RateLimitError(data.get("retMsg", "Rate limited"))
                elif ret_code in self.RETRYABLE_CODES:
                    raise APIError(
                        data.get("retMsg", f"Error code: {ret_code}"),
                        code=ret_code,
                        retryable=True
                    )
                else:
                    raise APIError(
                        data.get("retMsg", f"Error code: {ret_code}"),
                        code=ret_code,
                        retryable=False
                    )
                    
        except (RateLimitError, APIError):
            raise
        except Exception as e:
            logger.error(f"Order request failed: {e}")
            raise APIError(str(e), retryable=True)
    
    async def _place_market_order(
        self,
        symbol: str,
        side: str,
        size: float,
        category: str
    ) -> OrderResult:
        """Place a market order."""
        params = {
            "category": category,
            "symbol": symbol,
            "side": side.capitalize(),
            "orderType": "Market",
            "qty": str(size),
        }
        
        try:
            result = await self._execute_order(params)
            return OrderResult(
                order_id=result.get("orderId"),
                status="PLACED",
                symbol=symbol,
                side=side.capitalize(),
                size=size
            )
        except Exception as e:
            return OrderResult(
                status="FAILED",
                symbol=symbol,
                side=side,
                error=str(e)
            )
    
    async def _cancel_order_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute cancel order request."""
        await self.connector.rate_limiter.acquire()
        
        timestamp = await self.connector._get_server_time()
        body_json = json.dumps(params)
        signature = self.connector._generate_signature(timestamp, body_json)
        
        headers = {
            "X-BAPI-API-KEY": self.connector.api_key,
            "X-BAPI-SIGN": signature,
            "X-BAPI-SIGN-TYPE": "2",
            "X-BAPI-TIMESTAMP": timestamp,
            "X-BAPI-RECV-WINDOW": self.connector.recv_window,
            "Content-Type": "application/json",
        }
        
        url = f"{self.connector._get_base_url()}/v5/order/cancel"
        
        async with self.connector._session.post(
            url, 
            headers=headers, 
            data=body_json
        ) as resp:
            data = await resp.json()
            
            if data.get("retCode") != 0:
                raise APIError(data.get("retMsg", "Cancel failed"))
            
            return data.get("result", {})
    
    def _calculate_delay(self, attempt: int) -> float:
        """
        Вычисляет задержку с exponential backoff.
        
        Formula: min(base_delay * 2^attempt, max_delay)
        """
        delay = self.base_delay * (2 ** attempt)
        return min(delay, self.max_delay)
