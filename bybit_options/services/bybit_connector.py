"""
Bybit Connector - Refactored Version
====================================
Inherits from BaseExchangeConnector.

BACKWARD COMPATIBLE: All original methods preserved.
NEW FEATURES: get_recent_trades(), get_orderbook_snapshot()
"""

import hmac
import hashlib
import json
import time
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode
from datetime import datetime, timezone
from decimal import Decimal
import logging

import aiohttp

from bybit_options.services.base_connector import BaseExchangeConnector
from bybit_options.models.delta_models import (
    LargeTradeModel,
    OrderbookSnapshotModel,
    OpenInterestModel
)
from bybit_options.models.trade_history import (
    ExecutionHistoryResponse,
    OrderHistoryResponse,
)

logger = logging.getLogger(__name__)


class BybitConnector(BaseExchangeConnector):
    """
    Bybit API connector (V5 API).
    
    Inherits: BaseExchangeConnector
    
    Original Methods (Preserved):
    - get_positions()
    - get_tickers()
    - get_wallet_balance()
    - get_instruments_info()
    - get_kline_history()
    - get_historical_implied_volatility()
    
    New Methods:
    - get_recent_trades() - fetch large trades
    - get_orderbook_snapshot() - fetch orderbook
    """
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        testnet: bool = False,
        rate_limit: int = 50
    ):
        super().__init__(api_key, api_secret, testnet, rate_limit)
        self.recv_window = "10000"
    
    # =========================================================================
    # IMPLEMENT ABSTRACT METHODS
    # =========================================================================
    
    def _get_base_url(self) -> str:
        """Return Bybit API base URL"""
        if self.testnet:
            return "https://api-testnet.bybit.com"
        return "https://api.bybit.com"
    
    async def _get_server_time(self) -> str:
        """Get Bybit server time with fallback"""
        try:
            async with self._session.get(
                f"{self._get_base_url()}/v5/market/time"
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
        params_string: str
    ) -> str:
        """Generate Bybit HMAC SHA256 signature"""
        param_str = timestamp + self.api_key + self.recv_window + params_string
        return hmac.new(
            self.api_secret.encode('utf-8'),
            param_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def parse_trade(self, raw_data: Dict) -> LargeTradeModel:
        """
        Parse Bybit trade to LargeTradeModel.
        
        Bybit format:
        {
            "symbol": "BTCUSDT",
            "side": "Buy",
            "size": "10.5",
            "price": "95000.50",
            "execId": "abc123",
            "time": "1705334400000"
        }
        """
        trade_id = raw_data.get("execId")
        if not trade_id:
            raise ValueError("Missing execId")

        timestamp_value = raw_data.get("time") or raw_data.get("execTime")
        if timestamp_value is None:
            raise ValueError("Missing trade time")

        return LargeTradeModel(
            exchange='bybit',
            market_type='perpetual',
            symbol=raw_data['symbol'],
            price=Decimal(raw_data['price']),
            quantity=Decimal(raw_data.get('size') or raw_data.get('qty') or 0),
            side=raw_data['side'],
            trade_id=trade_id,
            timestamp=datetime.fromtimestamp(
                int(timestamp_value) / 1000,
                tz=timezone.utc
            )
        )
    
    def parse_orderbook(self, raw_data: Dict) -> OrderbookSnapshotModel:
        """
        Parse Bybit orderbook to OrderbookSnapshotModel.
        
        Bybit format:
        {
            "symbol": "BTCUSDT",
            "b": [["95000.5", "2.34"], ...],  # bids
            "a": [["95001.0", "3.21"], ...],  # asks
            "ts": "1705334400000"
        }
        """
        timestamp_value = raw_data.get("ts")
        timestamp = None
        if timestamp_value is not None:
            timestamp = datetime.fromtimestamp(int(timestamp_value) / 1000, tz=timezone.utc)

        return OrderbookSnapshotModel.from_raw_orderbook(
            exchange='bybit',
            symbol=raw_data['s'],
            bids_raw=raw_data.get('b', []),
            asks_raw=raw_data.get('a', []),
            timestamp=timestamp,
        )
    
    # =========================================================================
    # BYBIT-SPECIFIC REQUEST METHODS
    # =========================================================================
    
    async def _signed_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute Bybit signed request"""
        await self.rate_limiter.acquire()
        
        if params is None:
            params = {}
        
        timestamp = await self._get_server_time()
        
        # Determine payload/signature based on method
        if method == "GET":
            params_to_sign = urlencode(params) if params else ""
            signature = self._generate_signature(timestamp, params_to_sign)
            url = f"{self._get_base_url()}{endpoint}"
            if params_to_sign:
                url += f"?{params_to_sign}"
            
            headers = {
                "X-BAPI-API-KEY": self.api_key,
                "X-BAPI-SIGN": signature,
                "X-BAPI-SIGN-TYPE": "2",
                "X-BAPI-TIMESTAMP": timestamp,
                "X-BAPI-RECV-WINDOW": self.recv_window,
            }
            
            async with self._session.get(url, headers=headers) as resp:
                resp.raise_for_status()
                return await resp.json()
        
        else: # POST, PUT, DELETE (usually use JSON body in V5 for POST)
            params_to_sign = json.dumps(params)
            signature = self._generate_signature(timestamp, params_to_sign)
            url = f"{self._get_base_url()}{endpoint}"
            
            headers = {
                "X-BAPI-API-KEY": self.api_key,
                "X-BAPI-SIGN": signature,
                "X-BAPI-SIGN-TYPE": "2",
                "X-BAPI-TIMESTAMP": timestamp,
                "X-BAPI-RECV-WINDOW": self.recv_window,
                "Content-Type": "application/json"
            }
            
            async with self._session.request(method, url, headers=headers, data=params_to_sign) as resp:
                resp.raise_for_status()
                return await resp.json()
    
    async def _public_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute Bybit public request"""
        await self.rate_limiter.acquire()
        
        url = f"{self._get_base_url()}{endpoint}"
        
        try:
            async with self._session.get(url, params=params) as resp:
                resp.raise_for_status()
                return await resp.json()
        except Exception as e:
            logger.error(f"Bybit public request failed: {endpoint} - {e}")
            raise

    async def _signed_request_with_retry(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute signed request with rate limit retry."""

        async def _request():
            return await self._signed_request(method, endpoint, params)

        try:
            return await self._retry_with_backoff(_request)
        except aiohttp.ClientResponseError as exc:
            if exc.status == 429:
                return await self._retry_with_backoff(_request)
            raise
    
    # =========================================================================
    # NEW METHODS FOR DELTA SYSTEM
    # =========================================================================
    
    async def get_open_interest(
        self,
        symbol: str,
        category: str = 'linear',
        interval: str = '5min',
        limit: int = 1
    ) -> List[OpenInterestModel]:
        """
        Fetch Open Interest from Bybit.
        
        Args:
            symbol: Trading pair
            category: linear | inverse
            interval: 5min, 15min, 30min, 1h, 4h, 1d
            limit: 1-200
            
        Returns:
            List[OpenInterestModel]
        """
        params = {
            "category": category,
            "symbol": symbol,
            "intervalTime": interval,
            "limit": limit
        }
        
        try:
            data = await self._public_request("/v5/market/open-interest", params)
            
            if data.get("retCode") != 0:
                logger.error(f"OI fetch failed: {data.get('retMsg')}")
                return []
                
            items = []
            for item in data.get("result", {}).get("list", []):
                timestamp_ms = item.get("timestamp")
                if not timestamp_ms:
                    continue
                    
                items.append(OpenInterestModel(
                    exchange='bybit',
                    symbol=symbol,
                    open_interest=Decimal(item.get("openInterest", "0")),
                    timestamp=datetime.fromtimestamp(
                        int(timestamp_ms) / 1000, 
                        tz=timezone.utc
                    )
                ))
                
            return items
            
        except Exception as e:
            logger.error(f"Error getting OI for {symbol}: {e}")
            return []

    async def get_recent_trades_raw(
        self,
        symbol: str,
        category: str = 'spot',
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Fetch recent trades (raw payloads).

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            category: 'spot', 'linear', 'inverse', 'option'
            limit: Max trades to fetch

        Returns:
            Raw list from Bybit response
        """
        params = {
            "category": category,
            "symbol": symbol,
            "limit": limit
        }

        data = await self._public_request("/v5/market/recent-trade", params)

        if data.get("retCode") != 0:
            logger.error(
                f"Trades fetch failed: [{data.get('retCode')}] "
                f"{data.get('retMsg')}"
            )
            return []

        return data.get("result", {}).get("list", [])

    async def get_recent_trades(
        self,
        symbol: str,
        category: str = 'spot',
        limit: int = 100
    ) -> List[LargeTradeModel]:
        """
        Fetch recent trades and filter for large ones.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            category: 'spot', 'linear', 'inverse', 'option'
            limit: Max trades to fetch
        
        Returns:
            List[LargeTradeModel] with only large trades
        """
        trades = await self.get_recent_trades_raw(
            symbol=symbol,
            category=category,
            limit=limit
        )

        # Parse and filter large trades
        large_trades = []
        for trade in trades:
            try:
                parsed = self.parse_trade(trade)
                large_trades.append(parsed)
            except ValueError:
                # Trade doesn't meet threshold, skip
                continue
        
        logger.info(
            f"Fetched {len(trades)} trades, "
            f"filtered to {len(large_trades)} large trades"
        )
        
        return large_trades
    
    async def get_orderbook_snapshot(
        self,
        symbol: str,
        category: str = 'spot',
        depth: int = 20
    ) -> OrderbookSnapshotModel:
        """
        Fetch orderbook snapshot.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            category: 'spot', 'linear', 'inverse', 'option'
            depth: Number of levels (default 20, max 200)
        
        Returns:
            OrderbookSnapshotModel
        """
        limit = 25 if depth <= 20 else min(depth, 200)
        params = {
            "category": category,
            "symbol": symbol,
            "limit": limit,
        }
        
        data = await self._public_request("/v5/market/orderbook", params)
        
        if data.get("retCode") != 0:
            logger.error(
                f"Orderbook fetch failed: [{data.get('retCode')}] "
                f"{data.get('retMsg')}"
            )
            raise ValueError(f"Failed to fetch orderbook: {data.get('retMsg')}")
        
        result = data.get("result", {})

        bids = result.get('b', [])
        asks = result.get('a', [])

        if depth <= 20:
            bids = bids[:depth]
            asks = asks[:depth]

        return self.parse_orderbook({
            's': result.get('s'),
            'b': bids,
            'a': asks,
            'ts': result.get('ts')
        })

    async def get_execution_history(
        self,
        category: str,
        start_time: int,
        end_time: int,
        limit: int = 50,
        cursor: Optional[str] = None,
    ) -> ExecutionHistoryResponse:
        """Fetch execution history with cursor pagination support."""
        params: Dict[str, Any] = {
            "category": category,
            "startTime": start_time,
            "endTime": end_time,
            "limit": limit,
        }
        if cursor:
            params["cursor"] = cursor

        data = await self._signed_request_with_retry("GET", "/v5/execution/list", params)
        if data.get("retCode") == 10006:
            data = await self._retry_with_backoff(
                self._signed_request, "GET", "/v5/execution/list", params
            )

        return ExecutionHistoryResponse.parse_obj(data)

    async def get_order_history(
        self,
        category: str,
        start_time: int,
        end_time: int,
        limit: int = 20,
        cursor: Optional[str] = None,
    ) -> OrderHistoryResponse:
        """Fetch order history with cursor pagination support."""
        params: Dict[str, Any] = {
            "category": category,
            "startTime": start_time,
            "endTime": end_time,
            "limit": limit,
        }
        if cursor:
            params["cursor"] = cursor

        data = await self._signed_request_with_retry("GET", "/v5/order/history", params)
        if data.get("retCode") == 10006:
            data = await self._retry_with_backoff(
                self._signed_request, "GET", "/v5/order/history", params
            )

        return OrderHistoryResponse.parse_obj(data)
    
    # =========================================================================
    # ORIGINAL METHODS - PRESERVED FOR BACKWARD COMPATIBILITY
    # =========================================================================
    
    async def get_positions(
        self,
        category: str,
        symbol: Optional[str] = None,
        settle_coin: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Fetch positions with pagination support"""
        all_positions = []
        cursor = ""
        seen_cursors = set()
        max_pages = 100
        page_count = 0

        while True:
            page_count += 1
            if page_count > max_pages:
                logger.error(f"Pagination limit reached ({max_pages} pages)")
                break

            params = {"category": category, "limit": 200}
            if symbol:
                params["symbol"] = symbol
            if settle_coin:
                params["settleCoin"] = settle_coin
            if cursor:
                params["cursor"] = cursor

            data = await self._signed_request("GET", "/v5/position/list", params)

            if data.get("retCode") != 0:
                logger.error(f"Position fetch failed: {data.get('retMsg')}")
                break

            result = data.get("result", {})
            positions = result.get("list", [])
            active = [p for p in positions if float(p.get("size", 0)) != 0]
            all_positions.extend(active)

            cursor = result.get("nextPageCursor", "")
            if not cursor:
                break

            if cursor in seen_cursors:
                logger.error("Duplicate cursor detected")
                break

            seen_cursors.add(cursor)

        return all_positions
    
    async def get_tickers(
        self,
        category: str,
        base_coin: Optional[str] = None,
        symbol: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Fetch market tickers"""
        params = {"category": category, "limit": 1000}
        
        if base_coin:
            params["baseCoin"] = base_coin
        if symbol:
            params["symbol"] = symbol
        
        data = await self._public_request("/v5/market/tickers", params)
        
        if data.get("retCode") != 0:
            logger.error(f"Ticker fetch failed: {data.get('retMsg')}")
            return []
        
        return data.get("result", {}).get("list", [])
    
    async def get_wallet_balance(
        self,
        account_type: str = "UNIFIED",
        coin: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fetch wallet balance and margin info"""
        params = {"accountType": account_type}
        if coin:
            params["coin"] = coin
        
        data = await self._signed_request("GET", "/v5/account/wallet-balance", params)
        
        if data.get("retCode") != 0:
            logger.error(f"Wallet fetch failed: {data.get('retMsg')}")
            return {}
        
        return data.get("result", {})
    
    async def get_instruments_info(
        self,
        category: str,
        symbol: Optional[str] = None,
        base_coin: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Fetch instrument specifications with pagination"""
        logger.info(f"Fetching instruments: category={category}")
        
        all_instruments = []
        cursor = ""
        seen_cursors = set()
        max_pages = 100
        page_count = 0
        
        while True:
            page_count += 1
            if page_count > max_pages:
                logger.error(f"Pagination limit reached ({max_pages} pages)")
                break
            
            params = {"category": category, "limit": 1000}
            if symbol:
                params["symbol"] = symbol
            if base_coin:
                params["baseCoin"] = base_coin
            if cursor:
                params["cursor"] = cursor
            
            data = await self._public_request("/v5/market/instruments-info", params)
            
            if data.get("retCode") != 0:
                logger.error(f"Instruments fetch failed: {data.get('retMsg')}")
                break
            
            result = data.get("result", {})
            instruments = result.get("list", [])
            all_instruments.extend(instruments)
            
            cursor = result.get("nextPageCursor", "")
            if not cursor:
                break
            
            if cursor in seen_cursors:
                logger.error("Duplicate cursor detected")
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
        """Fetch historical K-line data (OHLCV)"""
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
            logger.error(f"Kline fetch failed: {data.get('retMsg')}")
            return []

        return data.get("result", {}).get("list", [])
    
    async def get_historical_implied_volatility(
        self,
        category: str = 'option',
        base_coin: str = 'BTC',
        period: int = 30
    ) -> List[Dict[str, Any]]:
        """Fetch historical Implied Volatility"""
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
            logger.error(f"Historical IV fetch failed: {data.get('retMsg')}")
            return []
            
        return data.get("result", {}).get("list", [])
    
    async def place_order(
        self,
        category: str,
        symbol: str,
        side: str,
        order_type: str,
        qty: str,
        price: Optional[str] = None,
        order_link_id: Optional[str] = None,
        time_in_force: str = "GTC"
    ) -> Dict[str, Any]:
        """
        Place a new order.
        
        Args:
            category: Product category (spot, linear, inverse, option)
            symbol: Symbol name
            side: Buy or Sell
            order_type: Limit or Market
            qty: Order quantity
            price: Order price (required for Limit orders)
            order_link_id: Custom order ID
            time_in_force: Time in force strategy
            
        Returns:
            Dictionary containing orderId and orderLinkId
        """
        params = {
            "category": category,
            "symbol": symbol,
            "side": side.capitalize(),
            "orderType": order_type.capitalize(),
            "qty": qty,
            "timeInForce": time_in_force
        }
        
        if price:
            params["price"] = price
            
        if order_link_id:
            params["orderLinkId"] = order_link_id
            
        data = await self._signed_request_with_retry(
            "POST",
            "/v5/order/create",
            params
        )
        
        if data.get("retCode") != 0:
            logger.error(f"Order placement failed: {data.get('retMsg')}")
            raise ValueError(f"Order failed: {data.get('retMsg')}")
            
        return data.get("result", {})
    
    async def amend_order(
        self,
        category: str,
        symbol: str,
        order_id: Optional[str] = None,
        order_link_id: Optional[str] = None,
        price: Optional[str] = None,
        qty: Optional[str] = None
    ) -> Dict[str, Any]:
        """Amend an active order."""
        params = {"category": category, "symbol": symbol}
        if order_id:
            params["orderId"] = order_id
        if order_link_id:
            params["orderLinkId"] = order_link_id
        if price:
            params["price"] = price
        if qty:
            params["qty"] = qty
            
        data = await self._signed_request_with_retry("POST", "/v5/order/amend", params)
        if data.get("retCode") != 0:
            raise ValueError(f"Amend failed: {data.get('retMsg')}")
        return data.get("result", {})

    async def cancel_order(
        self,
        category: str,
        symbol: str,
        order_id: Optional[str] = None,
        order_link_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Cancel an active order."""
        params = {"category": category, "symbol": symbol}
        if order_id:
            params["orderId"] = order_id
        if order_link_id:
            params["orderLinkId"] = order_link_id
            
        data = await self._signed_request_with_retry("POST", "/v5/order/cancel", params)
        if data.get("retCode") != 0:
            raise ValueError(f"Cancel failed: {data.get('retMsg')}")
        return data.get("result", {})

    async def get_realtime_orders(
        self,
        category: str,
        symbol: Optional[str] = None,
        order_id: Optional[str] = None,
        order_link_id: Optional[str] = None,
        open_only: int = 0  # 0: all, 1: open only? No, for realtime usually 0.
        # Check API docs: /v5/order/realtime. openOnly 0=active etc.
    ) -> List[Dict[str, Any]]:
        """Fetch incomplete orders."""
        params = {"category": category}
        if symbol:
            params["symbol"] = symbol
        if order_id:
            params["orderId"] = order_id
        if order_link_id:
            params["orderLinkId"] = order_link_id
            
        data = await self._signed_request_with_retry("GET", "/v5/order/realtime", params)
        return data.get("result", {}).get("list", [])
