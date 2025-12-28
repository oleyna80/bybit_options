"""
Bybit Async Connector - Production-ready API client
Handles authentication, rate limiting, and async requests
"""
import hmac
import hashlib
import time
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode
import aiohttp
import asyncio
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class RateLimiter:
    """Simple token bucket rate limiter"""
    max_requests: int = 50
    time_window: float = 1.0
    _tokens: float = 50.0
    _last_update: float = 0.0
    
    async def acquire(self):
        """Wait until a request token is available"""
        while True:
            now = time.time()
            elapsed = now - self._last_update
            
            # Refill tokens
            self._tokens = min(
                self.max_requests,
                self._tokens + elapsed * (self.max_requests / self.time_window)
            )
            self._last_update = now
            
            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return
            
            await asyncio.sleep(0.1)


class BybitConnector:
    """
    Async Bybit API connector with rate limiting and connection pooling
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
        self.base_url = (
            "https://api-testnet.bybit.com"
            if testnet
            else "https://api.bybit.com"
        )
        self.recv_window = "10000"
        self.rate_limiter = RateLimiter(max_requests=rate_limit)
        self._session: Optional[aiohttp.ClientSession] = None
        self._lock = asyncio.Lock()
    
    async def __aenter__(self):
        await self._init_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def _init_session(self):
        """Initialize aiohttp session with connection pooling"""
        if self._session is None:
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
    
    async def close(self):
        """Close the aiohttp session"""
        if self._session:
            await self._session.close()
            self._session = None
    
    async def _get_server_time(self) -> str:
        """Get Bybit server time with fallback to local time"""
        try:
            async with self._session.get(
                f"{self.base_url}/v5/market/time"
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return str(data.get("time", int(time.time() * 1000)))
        except Exception as e:
            logger.warning(f"Failed to get server time: {e}, using local")
        
        return str(int(time.time() * 1000))
    
    def _generate_signature(
        self,
        timestamp: str,
        query_string: str
    ) -> str:
        """Generate HMAC SHA256 signature"""
        param_str = timestamp + self.api_key + self.recv_window + query_string
        return hmac.new(
            self.api_secret.encode('utf-8'),
            param_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    async def _signed_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a signed request with rate limiting
        """
        await self.rate_limiter.acquire()
        
        if params is None:
            params = {}
        
        # Generate signature
        timestamp = await self._get_server_time()
        query_string = urlencode(params) if params else ""
        signature = self._generate_signature(timestamp, query_string)
        
        headers = {
            "X-BAPI-API-KEY": self.api_key,
            "X-BAPI-SIGN": signature,
            "X-BAPI-SIGN-TYPE": "2",
            "X-BAPI-TIMESTAMP": timestamp,
            "X-BAPI-RECV-WINDOW": self.recv_window,
        }
        
        url = f"{self.base_url}{endpoint}"
        if query_string:
            url += f"?{query_string}"
        
        try:
            async with self._session.request(
                method,
                url,
                headers=headers
            ) as resp:
                resp.raise_for_status()
                return await resp.json()
        
        except aiohttp.ClientError as e:
            logger.error(f"Request failed: {method} {endpoint} - {e}")
            raise
    
    async def _public_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a public (unsigned) request"""
        await self.rate_limiter.acquire()
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with self._session.get(url, params=params) as resp:
                resp.raise_for_status()
                return await resp.json()
        
        except aiohttp.ClientError as e:
            logger.error(f"Public request failed: {endpoint} - {e}")
            raise
    
    async def get_positions(
        self,
        category: str,
        symbol: Optional[str] = None,
        settle_coin: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch positions with pagination support

        Args:
            category: 'linear', 'inverse', 'option'
            symbol: Optional symbol filter
            settle_coin: Optional settlement coin filter
        """
        all_positions = []
        cursor = ""
        seen_cursors = set()  # Track seen cursors to prevent infinite loops
        max_pages = 100  # Safety limit to prevent infinite pagination
        page_count = 0

        while True:
            # Safety check: prevent infinite loops
            page_count += 1
            if page_count > max_pages:
                logger.error(
                    f"Pagination limit reached ({max_pages} pages). "
                    f"Possible infinite loop or API issue."
                )
                break

            params = {
                "category": category,
                "limit": 200
            }

            if symbol:
                params["symbol"] = symbol
            if settle_coin:
                params["settleCoin"] = settle_coin
            if cursor:
                params["cursor"] = cursor

            data = await self._signed_request("GET", "/v5/position/list", params)

            if data.get("retCode") != 0:
                logger.error(
                    f"Position fetch failed: [{data.get('retCode')}] "
                    f"{data.get('retMsg')}"
                )
                break

            result = data.get("result", {})
            positions = result.get("list", [])

            # Filter out zero-size positions
            active = [p for p in positions if float(p.get("size", 0)) != 0]
            all_positions.extend(active)

            cursor = result.get("nextPageCursor", "")
            if not cursor:
                break

            # Check for duplicate cursor (API bug)
            if cursor in seen_cursors:
                logger.error(
                    f"Duplicate cursor detected: {cursor}. "
                    f"Stopping pagination to prevent infinite loop."
                )
                break

            seen_cursors.add(cursor)

        return all_positions
    
    async def get_tickers(
        self,
        category: str,
        base_coin: Optional[str] = None,
        symbol: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch market tickers
        
        Args:
            category: 'spot', 'linear', 'inverse', 'option'
            base_coin: Base currency (for options)
            symbol: Specific symbol
        """
        params = {
            "category": category,
            "limit": 1000
        }
        
        if base_coin:
            params["baseCoin"] = base_coin
        if symbol:
            params["symbol"] = symbol
        
        data = await self._public_request("/v5/market/tickers", params)
        
        if data.get("retCode") != 0:
            logger.error(
                f"Ticker fetch failed: [{data.get('retCode')}] "
                f"{data.get('retMsg')}"
            )
            return []
        
        return data.get("result", {}).get("list", [])
    
    async def get_wallet_balance(
        self,
        account_type: str = "UNIFIED",
        coin: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fetch wallet balance and margin info
        
        Args:
            account_type: 'UNIFIED', 'CONTRACT'
            coin: Optional coin filter
        """
        params = {"accountType": account_type}
        if coin:
            params["coin"] = coin
        
        data = await self._signed_request(
            "GET",
            "/v5/account/wallet-balance",
            params
        )
        
        if data.get("retCode") != 0:
            logger.error(
                f"Wallet fetch failed: [{data.get('retCode')}] "
                f"{data.get('retMsg')}"
            )
            return {}
        
        return data.get("result", {})
    
    async def get_instruments_info(
        self,
        category: str,
        symbol: Optional[str] = None,
        base_coin: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch instrument specifications with pagination support
        
        Args:
            category: 'spot', 'linear', 'inverse', 'option'
            symbol: Optional symbol filter
            base_coin: Optional base coin filter
        """
        logger.info(f"Starting to fetch instruments: category={category}, symbol={symbol}, base_coin={base_coin}")
        
        all_instruments = []
        cursor = ""
        seen_cursors = set()  # Track seen cursors to prevent infinite loops
        max_pages = 100  # Safety limit to prevent infinite pagination
        page_count = 0
        limit = 1000  # Maximum per page
        
        while True:
            # Safety check: prevent infinite loops
            page_count += 1
            if page_count > max_pages:
                logger.error(
                    f"Pagination limit reached ({max_pages} pages). "
                    f"Possible infinite loop or API issue."
                )
                break
            
            params = {
                "category": category,
                "limit": limit
            }
            
            if symbol:
                params["symbol"] = symbol
            if base_coin:
                params["baseCoin"] = base_coin
            if cursor:
                params["cursor"] = cursor
            
            data = await self._public_request("/v5/market/instruments-info", params)
            
            if data.get("retCode") != 0:
                logger.error(
                    f"Instruments fetch failed: [{data.get('retCode')}] "
                    f"{data.get('retMsg')}"
                )
                break
            
            result = data.get("result", {})
            instruments = result.get("list", [])
            all_instruments.extend(instruments)
            
            cursor = result.get("nextPageCursor", "")
            if not cursor:
                break
            
            # Check for duplicate cursor (API bug)
            if cursor in seen_cursors:
                logger.error(
                    f"Duplicate cursor detected: {cursor}. "
                    f"Stopping pagination to prevent infinite loop."
                )
                break
            
            seen_cursors.add(cursor)
        
        logger.info(f"Fetched {len(all_instruments)} total instruments")
        return all_instruments
    
    async def get_kline_history(
        self,
        category: str,
        symbol: str,
        interval: str,
        start_time_ms: Optional[int] = None,
        end_time_ms: Optional[int] = None,
        limit: int = 1000
    ) -> List[List[str]]:
        """
        Fetch historical K-line data (OHLCV).
        
        Note: Bybit API returns up to 1000 bars per request. Pagination logic
        for filling 5 years of daily data (1825 bars) needs to be handled
        by the caller or a dedicated service, not here.
        """
        params = {
            "category": category,
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }
        
        if start_time_ms is not None:
            params["start"] = start_time_ms
        if end_time_ms is not None:
            params["end"] = end_time_ms
            
        data = await self._public_request("/v5/market/kline", params)
        
        if data.get("retCode") != 0:
            logger.error(
                f"Kline fetch failed: [{data.get('retCode')}] "
                f"{data.get('retMsg')}"
            )
            return []

        # Result list contains [timestamp, open, high, low, close, volume, turnover]
        return data.get("result", {}).get("list", [])
    
    async def get_historical_implied_volatility(
        self,
        category: str = 'option',
        base_coin: str = 'BTC',
        period: int = 30 # 30 days TTM
    ) -> List[Dict[str, Any]]:
        """
        Fetch historical Implied Volatility for a specific base coin and period.
        
        Note: Bybit provides historical IV for 7/14/21/30/60/90/120/180/270/365 days TTM.
        We request 30 days period as per requirements.
        """
        params = {
            "category": category,
            "baseCoin": base_coin,
            "period": period
        }
        
        data = await self._public_request(
            "/v5/market/historical-implied-volatility",
            params
        )
        
        if data.get("retCode") != 0:
            logger.error(
                f"Historical IV fetch failed: [{data.get('retCode')}] "
                f"{data.get('retMsg')}"
            )
            return []
            
        # Result list contains [{"period": 30, "value": "0.65", "time": "1672336800000"}, ...]
        return data.get("result", {}).get("list", [])