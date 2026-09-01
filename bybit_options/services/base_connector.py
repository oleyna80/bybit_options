"""
Base Exchange Connector
=======================
Abstract base class for all exchange API connectors.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
import aiohttp
import time
import logging

from bybit_options.models.delta_models import (
    LargeTradeModel,
    OrderbookSnapshotModel
)

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter"""
    def __init__(self, max_requests: int = 50, time_window: float = 1.0):
        self.max_requests = max_requests
        self.time_window = time_window
        self._tokens = float(max_requests)
        self._last_update = time.time()
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire permission to make request"""
        async with self._lock:
            now = time.time()
            elapsed = now - self._last_update
            
            self._tokens = min(
                self.max_requests,
                self._tokens + elapsed * (self.max_requests / self.time_window)
            )
            self._last_update = now
            
            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return
            
            deficit = 1.0 - self._tokens
            wait_time = deficit * (self.time_window / self.max_requests)
        
        await asyncio.sleep(wait_time)


class BaseExchangeConnector(ABC):
    """
    Abstract base class for exchange connectors.
    
    Subclasses must implement:
    - _get_base_url()
    - _generate_signature()
    - _get_server_time()
    - parse_trade()
    - parse_orderbook()
    """
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        testnet: bool = False,
        rate_limit: int = 50
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        
        self._session: Optional[aiohttp.ClientSession] = None
        self._lock = asyncio.Lock()
        self.rate_limiter = RateLimiter(max_requests=rate_limit)
        
        self.exchange_name = self.__class__.__name__.replace('Connector', '').lower()
        
        logger.info(
            f"Initialized {self.exchange_name} connector "
            f"(testnet={testnet}, rate_limit={rate_limit}/sec)"
        )
    
    # Abstract methods
    @abstractmethod
    def _get_base_url(self) -> str:
        """Return base URL for API"""
        pass
    
    @abstractmethod
    def _generate_signature(self, timestamp: str, params_string: str) -> str:
        """Generate authentication signature"""
        pass
    
    @abstractmethod
    async def _get_server_time(self) -> str:
        """Get server timestamp"""
        pass
    
    @abstractmethod
    def parse_trade(self, raw_data: Dict) -> LargeTradeModel:
        """Parse raw trade data to LargeTradeModel"""
        pass
    
    @abstractmethod
    def parse_orderbook(self, raw_data: Dict) -> OrderbookSnapshotModel:
        """Parse raw orderbook data to OrderbookSnapshotModel"""
        pass
    
    # Session management
    async def connect(self):
        """Create HTTP session"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=30,
                ttl_dns_cache=300
            )
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers={'Content-Type': 'application/json'}
            )
            logger.info(f"{self.exchange_name}: HTTP session created")
    
    async def close(self):
        """Close HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
            logger.info(f"{self.exchange_name}: HTTP session closed")
    
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    # Request helpers
    async def _make_public_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute public GET request"""
        if not self._session or self._session.closed:
            await self.connect()
        
        await self.rate_limiter.acquire()
        
        url = f"{self._get_base_url()}{endpoint}"
        
        try:
            async with self._session.get(url, params=params) as resp:
                resp.raise_for_status()
                return await resp.json()
        except aiohttp.ClientError as e:
            logger.error(f"{self.exchange_name} request failed: {endpoint} - {e}")
            raise
    
    async def _retry_with_backoff(
        self,
        func,
        *args,
        max_retries: int = 3,
        **kwargs
    ) -> Any:
        """Retry with exponential backoff"""
        for attempt in range(max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"{self.exchange_name}: All retries failed")
                    raise
                
                wait_time = 2 ** attempt
                logger.warning(
                    f"{self.exchange_name}: Retry {attempt + 1}/{max_retries} "
                    f"in {wait_time}s..."
                )
                await asyncio.sleep(wait_time)
