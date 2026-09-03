"""
Market Data Service - Async data fetching and caching layer
"""
import asyncio
from typing import Dict, List, Optional, Set, Tuple
import logging
from collections import defaultdict

from bybit_options.services.bybit_connector import BybitConnector
from bybit_options.models import (
    PositionModel, PositionSide, PositionType, OptionType,
    MarginModel, SlippageMetrics, CoinHolding
)

logger = logging.getLogger(__name__)


class MarketDataService:
    """
    Service for fetching and caching market data
    Separates data fetching from business logic
    """
    
    def __init__(self, connector: BybitConnector):
        self.connector = connector
        self._ticker_cache: Dict[str, Dict] = {}
        self._instrument_cache: Dict[str, Dict] = {}
    
    async def fetch_all_positions(self) -> List[Dict]:
        """
        Fetch all active positions across all categories
        Returns raw position data from API
        """
        logger.info("Fetching positions...")
        
        # Fetch in parallel
        linear_task = self.connector.get_positions(
            category="linear",
            settle_coin="USDT"
        )
        option_task = self.connector.get_positions(category="option")
        
        linear_positions, option_positions = await asyncio.gather(
            linear_task,
            option_task,
            return_exceptions=True
        )
        
        # Handle exceptions
        if isinstance(linear_positions, Exception):
            logger.error(f"Linear positions fetch failed: {linear_positions}")
            linear_positions = []
        
        if isinstance(option_positions, Exception):
            logger.error(f"Option positions fetch failed: {option_positions}")
            option_positions = []
        
        # Tag with category
        for pos in linear_positions:
            pos["_category"] = "linear"
        for pos in option_positions:
            pos["_category"] = "option"
        
        all_positions = linear_positions + option_positions
        
        logger.info(
            f"Fetched {len(all_positions)} positions: "
            f"{len(linear_positions)} linear, {len(option_positions)} option"
        )
        
        return all_positions
    
    async def fetch_margin_info(self) -> Optional[MarginModel]:
        """
        Fetch wallet balance and margin metrics including coin holdings
        """
        logger.info("Fetching wallet balance...")
        
        try:
            wallet_data = await self.connector.get_wallet_balance(
                account_type="UNIFIED"
            )
            
            if not wallet_data:
                logger.warning("No wallet data returned")
                return None
            
            # Extract the first account (usually there's only one)
            accounts = wallet_data.get("list", [])
            if not accounts:
                logger.warning("No accounts in wallet data")
                return None
            
            account = accounts[0]
            
            # Parse coin holdings
            holdings = []
            coins_data = account.get("coin", [])
            for coin_data in coins_data:
                # Only include coins with non-zero balance
                wallet_balance = float(coin_data.get("walletBalance", 0))
                if wallet_balance > 0:
                    holding = CoinHolding(
                        coin=coin_data.get("coin", ""),
                        wallet_balance=wallet_balance,
                        usd_value=float(coin_data.get("usdValue", 0)),
                        equity=float(coin_data.get("equity", 0)),
                        unrealized_pnl=float(coin_data.get("unrealisedPnl", 0))
                    )
                    holdings.append(holding)
            
            # Parse margin metrics
            margin = MarginModel(
                account_type=account.get("accountType", "UNIFIED"),
                total_equity=float(account.get("totalEquity", 0)),
                available_balance=float(account.get("totalAvailableBalance", 0)),
                used_margin=float(account.get("totalInitialMargin", 0)),
                initial_margin=float(account.get("totalInitialMargin", 0)),
                maintenance_margin=float(account.get("totalMaintenanceMargin", 0)),
                unrealized_pnl=float(account.get("totalPerpUPL", 0)),
                realized_pnl=0.0,  # Not directly available in this endpoint
                holdings=holdings
            )
            
            # Calculate margin ratio
            if margin.total_equity > 0:
                margin.margin_ratio = (
                    margin.used_margin / margin.total_equity * 100
                )
            
            logger.info(
                f"Margin: Equity=${margin.total_equity:.2f}, "
                f"Used=${margin.used_margin:.2f}, "
                f"Ratio={margin.margin_ratio:.2f}%"
            )
            
            return margin
        
        except Exception as e:
            logger.error(f"Failed to fetch margin info: {e}")
            return None
    
    async def fetch_option_greeks(
        self,
        base_coins: Set[str]
    ) -> Dict[str, Dict]:
        """
        Fetch option tickers (Greeks) for multiple base coins in parallel
        Returns a dictionary mapping symbol -> ticker data
        """
        if not base_coins:
            return {}
        
        logger.info(f"Fetching option tickers for: {base_coins}")
        
        tasks = [
            self.connector.get_tickers(category="option", base_coin=coin)
            for coin in base_coins
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Build unified ticker map
        ticker_map = {}
        
        for coin, result in zip(base_coins, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to fetch tickers for {coin}: {result}")
                continue
            
            for ticker in result:
                symbol = ticker.get("symbol", "")
                ticker_map[symbol] = ticker
                
                # Create alternate keys (with and without -USDT/-USD suffix)
                for suffix in ["-USDT", "-USD"]:
                    if symbol.endswith(suffix):
                        ticker_map[symbol[:-len(suffix)]] = ticker
        
        logger.info(f"Loaded {len(ticker_map)} option tickers")
        self._ticker_cache.update(ticker_map)
        
        return ticker_map
    
    async def fetch_underlying_prices(
        self,
        base_coins: Set[str]
    ) -> Dict[str, float]:
        """
        Fetch perpetual (mark) prices for base coins
        Returns mapping of coin -> mark price
        """
        if not base_coins:
            return {}
        
        logger.info(f"Fetching underlying prices for: {base_coins}")
        
        # Construct perp symbols
        symbols = [f"{coin}USDT" for coin in base_coins]
        
        tasks = [
            self.connector.get_tickers(category="linear", symbol=symbol)
            for symbol in symbols
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        price_map = {}
        
        for coin, result in zip(base_coins, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to fetch price for {coin}: {result}")
                continue
            
            if result:
                ticker = result[0]
                mark_price = float(ticker.get("markPrice", 0))
                price_map[coin] = mark_price
                logger.info(f"  {coin}: ${mark_price:.2f}")
        
        return price_map
    
    async def fetch_atm_iv(
        self,
        base_coin: str,
        series: str,
        underlying_price: float
    ) -> Optional[float]:
        """
        Find ATM (At-The-Money) implied volatility for a given series
        
        Args:
            base_coin: e.g., 'BTC'
            series: e.g., '19DEC25'
            underlying_price: Current perp price
        
        Returns:
            ATM IV or None if not found
        """
        # Find options in this series
        pattern = f"{base_coin}-{series}-"
        
        candidates = []
        
        for symbol, ticker in self._ticker_cache.items():
            if pattern in symbol and "-C" in symbol:  # Use Calls
                strike_str = symbol.split("-")[2]
                try:
                    strike = float(strike_str)
                    iv = float(ticker.get("markIv", 0))
                    
                    if iv > 0:
                        distance = abs(strike - underlying_price)
                        candidates.append((strike, iv, distance))
                
                except (ValueError, IndexError):
                    continue
        
        if not candidates:
            return None
        
        # Find closest to ATM
        candidates.sort(key=lambda x: x[2])
        atm_strike, atm_iv, _ = candidates[0]
        
        logger.debug(
            f"ATM IV for {base_coin}-{series}: "
            f"Strike={atm_strike}, IV={atm_iv:.4f}"
        )
        
        return atm_iv
    
    def get_ticker(self, symbol: str) -> Optional[Dict]:
        """
        Get cached ticker data for a symbol
        """
        # Try direct lookup
        if symbol in self._ticker_cache:
            return self._ticker_cache[symbol]
        
        # Try without suffix
        for suffix in ["-USDT", "-USD"]:
            if symbol.endswith(suffix):
                clean = symbol[:-len(suffix)]
                if clean in self._ticker_cache:
                    return self._ticker_cache[clean]
        
        return None
    
    def calculate_slippage(
        self,
        symbol: str,
        mark_price: float
    ) -> Optional[SlippageMetrics]:
        """
        Calculate slippage metrics from cached ticker data
        """
        ticker = self.get_ticker(symbol)
        
        if not ticker:
            return None
        
        try:
            bid = float(ticker.get("bid1Price", 0))
            ask = float(ticker.get("ask1Price", 0))
            
            if bid == 0 or ask == 0:
                return None
            
            spread_abs = ask - bid
            mid = (bid + ask) / 2
            spread_pct = (spread_abs / mark_price) * 100 if mark_price > 0 else 0
            
            return SlippageMetrics(
                bid=bid,
                ask=ask,
                mark_price=mark_price,
                spread_abs=spread_abs,
                spread_pct=spread_pct,
                mid_price=mid
            )
        
        except (ValueError, KeyError) as e:
            logger.debug(f"Failed to calculate slippage for {symbol}: {e}")
            return None