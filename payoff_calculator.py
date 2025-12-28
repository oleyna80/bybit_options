"""
Payoff Calculator for Options Portfolio
Calculates P&L at expiry for various underlying prices

Enhanced for real-time integration with Bybit portfolio data:
- Real positions from portfolio analysis
- Current market prices from Bybit API
- Performance optimizations for large portfolios
- Multi-currency support (BTC, ETH, etc.)
"""

import numpy as np
from typing import List, Dict, Any, Tuple, Optional
import logging
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import functools
import time

from data_models import (
    PositionModel,
    PositionSide,
    PositionType,
    OptionType,
    GreeksModel
)

logger = logging.getLogger(__name__)


class PayoffCalculationMode(str, Enum):
    """Mode for payoff calculation"""
    AT_EXPIRY = "at_expiry"  # Only intrinsic value
    WITH_THETA = "with_theta"  # Include time decay approximation
    FULL = "full"  # Include all Greeks (approximation)


@dataclass
class PayoffResult:
    """Result of payoff calculation"""
    price_range: np.ndarray  # Array of underlying prices
    pnl_array: np.ndarray    # P&L at each price point
    breakeven_points: List[float]  # Prices where P&L = 0
    max_profit: float
    max_loss: float
    max_profit_price: float  # Price where max profit occurs
    max_loss_price: float    # Price where max loss occurs
    current_price: float     # Current underlying price
    current_pnl: float       # P&L at current price
    mode: PayoffCalculationMode


class PayoffCalculator:
    """
    Calculator for portfolio P&L at expiry
    
    Enhanced for real-time integration:
    - Real positions from Bybit portfolio
    - Current market prices from Bybit API
    - Multi-currency support (BTC, ETH, etc.)
    - Performance optimizations for large portfolios
    - Caching for repeated calculations
    - Accurate theta decay with real days to expiry
    
    Supports:
    - Options (Calls/Puts) with Buy/Sell sides
    - Linear positions (futures/spot)
    - Theta decay approximation
    - Breakeven point calculation
    - Max profit/loss analysis
    - Per-expiry series calculations
    """
    
    def __init__(self, precision: int = 1000, enable_cache: bool = True, max_cache_size: int = 100):
        """
        Args:
            precision: Number of price points in range (default: 1000)
            enable_cache: Enable caching for performance (default: True)
            max_cache_size: Maximum number of cached results (default: 100)
        """
        self.precision = precision
        self.enable_cache = enable_cache
        self.max_cache_size = max_cache_size
        self._cache: Dict[str, Tuple[float, PayoffResult]] = {}
        self._cache_ttl = 30.0  # Cache TTL in seconds
        self._last_cleanup = time.time()
        
    def calculate_payoff_at_expiry(
        self,
        positions: List[PositionModel],
        current_price: float,
        price_range_pct: float = 20.0,
        days_to_expiry: Optional[int] = None,
        mode: PayoffCalculationMode = PayoffCalculationMode.AT_EXPIRY,
        cache_key: Optional[str] = None
    ) -> PayoffResult:
        """
        Calculate P&L for portfolio across a range of underlying prices
        
        Enhanced for real-time integration:
        - Caching for identical inputs
        - Performance optimizations for large position sets
        - Accurate current price interpolation
        - Support for multi-currency portfolios
        
        Args:
            positions: List of PositionModel objects from real portfolio
            current_price: Current underlying price from market data
            price_range_pct: Percentage range around current price (default: ±20%)
            days_to_expiry: Days until expiry (for theta decay)
            mode: Calculation mode (at_expiry, with_theta, full)
            cache_key: Optional cache key for repeated calculations
            
        Returns:
            PayoffResult with P&L data
        """
        # Check cache if enabled
        if self.enable_cache and cache_key:
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                logger.debug(f"Using cached payoff result for key: {cache_key}")
                return cached_result
        
        # Validate inputs
        if not positions:
            logger.warning("No positions provided for payoff calculation")
            return self._empty_result(current_price)
        
        # Start timing for performance monitoring
        start_time = time.time()
        
        # Generate price range
        price_range = self._generate_price_range(
            current_price, price_range_pct
        )
        
        # Calculate P&L for each position with vectorized operations
        total_pnl = self._calculate_portfolio_pnl_vectorized(
            positions, price_range, current_price,
            days_to_expiry, mode
        )
        
        # Calculate metrics
        breakeven_points = self._find_breakeven_points(price_range, total_pnl)
        max_profit, max_profit_price = self._find_max_profit(price_range, total_pnl)
        max_loss, max_loss_price = self._find_max_loss(price_range, total_pnl)
        
        # Current P&L (interpolate at current_price)
        current_pnl = np.interp(
            current_price, price_range, total_pnl
        )
        
        result = PayoffResult(
            price_range=price_range,
            pnl_array=total_pnl,
            breakeven_points=breakeven_points,
            max_profit=max_profit,
            max_loss=max_loss,
            max_profit_price=max_profit_price,
            max_loss_price=max_loss_price,
            current_price=current_price,
            current_pnl=current_pnl,
            mode=mode
        )
        
        # Cache the result if enabled
        if self.enable_cache and cache_key:
            self._cache_result(cache_key, result)
        
        # Log performance metrics
        elapsed = time.time() - start_time
        logger.debug(f"Payoff calculation completed in {elapsed:.3f}s for {len(positions)} positions")
        
        return result
    
    def _calculate_portfolio_pnl_vectorized(
        self,
        positions: List[PositionModel],
        price_range: np.ndarray,
        current_price: float,
        days_to_expiry: Optional[int],
        mode: PayoffCalculationMode
    ) -> np.ndarray:
        """
        Vectorized calculation of portfolio P&L for better performance
        
        Args:
            positions: List of positions
            price_range: Array of underlying prices
            current_price: Current underlying price
            days_to_expiry: Days to expiry
            mode: Calculation mode
            
        Returns:
            Total P&L array across price range
        """
        total_pnl = np.zeros_like(price_range, dtype=float)
        
        # Group positions by type for batch processing
        option_positions = [p for p in positions if p.pos_type == PositionType.OPTION]
        linear_positions = [p for p in positions if p.pos_type != PositionType.OPTION]
        
        # Process option positions
        for position in option_positions:
            position_pnl = self._calculate_option_payoff_vectorized(
                position, price_range, current_price
            )
            
            # Apply side and size multipliers
            side_multiplier = 1.0 if position.side == PositionSide.BUY else -1.0
            position_pnl *= side_multiplier * position.size
            
            # Apply theta decay if requested
            if mode != PayoffCalculationMode.AT_EXPIRY and days_to_expiry:
                theta_adjustment = self._calculate_theta_adjustment(
                    position, days_to_expiry, mode
                )
                position_pnl += theta_adjustment
            
            total_pnl += position_pnl
        
        # Process linear positions
        for position in linear_positions:
            position_pnl = self._calculate_linear_payoff(
                position, price_range, current_price
            )
            
            side_multiplier = 1.0 if position.side == PositionSide.BUY else -1.0
            position_pnl *= side_multiplier * position.size
            
            total_pnl += position_pnl
        
        return total_pnl
    
    def _calculate_option_payoff_vectorized(
        self,
        position: PositionModel,
        price_range: np.ndarray,
        current_price: float
    ) -> np.ndarray:
        """
        Vectorized calculation of option intrinsic value at expiry
        
        Args:
            position: Option position
            price_range: Array of underlying prices
            current_price: Current underlying price
            
        Returns:
            Option P&L array
        """
        if not position.strike or not position.option_type:
            logger.warning(f"Option {position.symbol} missing strike or type")
            return np.zeros_like(price_range)
        
        strike = position.strike
        
        if position.option_type == OptionType.CALL:
            # Call option: max(0, S - K)
            intrinsic = np.maximum(0, price_range - strike)
        else:  # PUT
            # Put option: max(0, K - S)
            intrinsic = np.maximum(0, strike - price_range)
        
        # Subtract premium (approximated by mark value)
        premium = position.mark_value or 0
        if premium > 0:
            intrinsic -= premium
        
        return intrinsic
    
    def _get_cached_result(self, cache_key: str) -> Optional[PayoffResult]:
        """Get cached result if valid"""
        # Periodic cleanup to prevent memory leak
        self._cleanup_expired_cache()

        if cache_key not in self._cache:
            return None

        timestamp, result = self._cache[cache_key]
        if time.time() - timestamp > self._cache_ttl:
            del self._cache[cache_key]
            return None

        return result
    
    def _cache_result(self, cache_key: str, result: PayoffResult):
        """Cache calculation result"""
        self._cache[cache_key] = (time.time(), result)
        
    def clear_cache(self):
        """Clear all cached results"""
        self._cache.clear()
        logger.debug("Payoff calculator cache cleared")

    def _cleanup_expired_cache(self):
        """
        Clean up expired cache entries to prevent memory leak

        Runs every 60 seconds and:
        1. Removes expired entries (older than TTL)
        2. Enforces max cache size (LRU eviction)
        """
        current_time = time.time()

        # Only run cleanup every 60 seconds
        if current_time - self._last_cleanup < 60:
            return

        self._last_cleanup = current_time

        # Remove expired entries
        expired_keys = [
            key for key, (timestamp, _) in self._cache.items()
            if current_time - timestamp > self._cache_ttl
        ]

        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

        # Enforce max cache size (LRU eviction)
        if len(self._cache) > self.max_cache_size:
            # Sort by timestamp (oldest first)
            sorted_items = sorted(
                self._cache.items(),
                key=lambda x: x[1][0]
            )

            # Remove oldest entries
            num_to_remove = len(self._cache) - self.max_cache_size
            for key, _ in sorted_items[:num_to_remove]:
                del self._cache[key]

            logger.debug(
                f"Cache size limit reached. Evicted {num_to_remove} oldest entries. "
                f"Current size: {len(self._cache)}/{self.max_cache_size}"
            )
    
    def _generate_price_range(
        self,
        current_price: float,
        price_range_pct: float
    ) -> np.ndarray:
        """Generate price range around current price"""
        min_price = current_price * (1 - price_range_pct / 100)
        max_price = current_price * (1 + price_range_pct / 100)
        
        # Ensure min_price is positive
        min_price = max(min_price, 0.01)
        
        return np.linspace(min_price, max_price, self.precision)
    
    def _calculate_position_payoff(
        self,
        position: PositionModel,
        price_range: np.ndarray,
        current_price: float,
        days_to_expiry: Optional[int],
        mode: PayoffCalculationMode
    ) -> np.ndarray:
        """
        Calculate P&L for a single position across price range
        """
        # Base P&L from intrinsic value
        if position.pos_type == PositionType.OPTION:
            pnl = self._calculate_option_payoff(
                position, price_range, current_price
            )
        else:
            # Linear position (futures/spot)
            pnl = self._calculate_linear_payoff(
                position, price_range, current_price
            )
        
        # Apply side multiplier (Buy: +1, Sell: -1)
        side_multiplier = 1.0 if position.side == PositionSide.BUY else -1.0
        pnl *= side_multiplier
        
        # Apply size multiplier
        pnl *= position.size
        
        # Apply theta decay if requested
        if mode != PayoffCalculationMode.AT_EXPIRY and days_to_expiry:
            theta_adjustment = self._calculate_theta_adjustment(
                position, days_to_expiry, mode
            )
            pnl += theta_adjustment
        
        return pnl
    
    def _calculate_option_payoff(
        self,
        position: PositionModel,
        price_range: np.ndarray,
        current_price: float
    ) -> np.ndarray:
        """
        Calculate option intrinsic value at expiry
        """
        if not position.strike or not position.option_type:
            logger.warning(f"Option {position.symbol} missing strike or type")
            return np.zeros_like(price_range)
        
        strike = position.strike
        
        if position.option_type == OptionType.CALL:
            # Call option: max(0, S - K)
            intrinsic = np.maximum(0, price_range - strike)
        else:  # PUT
            # Put option: max(0, K - S)
            intrinsic = np.maximum(0, strike - price_range)
        
        # Subtract premium (approximated by mark value)
        premium = position.mark_value or 0
        if premium > 0:
            intrinsic -= premium
        
        return intrinsic
    
    def _calculate_linear_payoff(
        self,
        position: PositionModel,
        price_range: np.ndarray,
        current_price: float
    ) -> np.ndarray:
        """
        Calculate linear position P&L
        """
        # Linear position P&L = (price - entry_price) * size
        # For simplicity, we calculate P&L from current price
        entry_price = position.entry_price or current_price
        return price_range - entry_price
    
    def _calculate_theta_adjustment(
        self,
        position: PositionModel,
        days_to_expiry: int,
        mode: PayoffCalculationMode
    ) -> float:
        """
        Calculate theta decay adjustment
        """
        if days_to_expiry <= 0:
            return 0.0
        
        # Get theta from Greeks (USD per day)
        theta_usd = position.greeks.theta_usd if position.greeks else 0
        
        if mode == PayoffCalculationMode.WITH_THETA:
            # Simple linear theta decay
            return theta_usd * days_to_expiry
        elif mode == PayoffCalculationMode.FULL:
            # More sophisticated adjustment including other Greeks
            # For now, same as WITH_THETA
            return theta_usd * days_to_expiry
        else:
            return 0.0
    
    def _find_breakeven_points(
        self,
        price_range: np.ndarray,
        pnl_array: np.ndarray
    ) -> List[float]:
        """Find prices where P&L crosses zero"""
        breakeven_points = []
        
        # Find sign changes
        for i in range(len(pnl_array) - 1):
            if pnl_array[i] == 0:
                breakeven_points.append(price_range[i])
            elif pnl_array[i] * pnl_array[i + 1] < 0:
                # Linear interpolation for zero crossing
                x1, x2 = price_range[i], price_range[i + 1]
                y1, y2 = pnl_array[i], pnl_array[i + 1]
                
                # Avoid division by zero
                if y2 != y1:
                    zero_x = x1 - y1 * (x2 - x1) / (y2 - y1)
                    breakeven_points.append(zero_x)
        
        return sorted(set(round(p, 2) for p in breakeven_points))
    
    def _find_max_profit(
        self,
        price_range: np.ndarray,
        pnl_array: np.ndarray
    ) -> Tuple[float, float]:
        """Find maximum profit and corresponding price"""
        max_idx = np.argmax(pnl_array)
        return float(pnl_array[max_idx]), float(price_range[max_idx])
    
    def _find_max_loss(
        self,
        price_range: np.ndarray,
        pnl_array: np.ndarray
    ) -> Tuple[float, float]:
        """Find maximum loss and corresponding price"""
        min_idx = np.argmin(pnl_array)
        return float(pnl_array[min_idx]), float(price_range[min_idx])
    
    def _empty_result(self, current_price: float) -> PayoffResult:
        """Return empty result for no positions"""
        price_range = np.array([current_price * 0.8, current_price * 1.2])
        pnl_array = np.zeros_like(price_range)
        
        return PayoffResult(
            price_range=price_range,
            pnl_array=pnl_array,
            breakeven_points=[],
            max_profit=0.0,
            max_loss=0.0,
            max_profit_price=current_price,
            max_loss_price=current_price,
            current_price=current_price,
            current_pnl=0.0,
            mode=PayoffCalculationMode.AT_EXPIRY
        )
    
    def calculate_portfolio_summary(
        self,
        positions: List[PositionModel],
        current_price: float
    ) -> Dict[str, Any]:
        """
        Calculate summary metrics for portfolio
        
        Enhanced for real-time data:
        - Per-expiry series breakdown
        - Greeks aggregation with side adjustments
        - Premium analysis
        - Risk metrics
        
        Returns:
            Dictionary with portfolio summary
        """
        if not positions:
            return {
                "total_positions": 0,
                "options_count": 0,
                "linear_count": 0,
                "total_delta": 0.0,
                "total_theta": 0.0,
                "net_premium": 0.0,
                "expiry_breakdown": {},
                "coin_breakdown": {}
            }
        
        options_count = 0
        linear_count = 0
        total_delta = 0.0
        total_gamma = 0.0
        total_vega = 0.0
        total_theta = 0.0
        net_premium = 0.0
        
        # Breakdown by expiry series
        expiry_breakdown: Dict[str, Dict[str, Any]] = {}
        coin_breakdown: Dict[str, Dict[str, Any]] = {}
        
        for position in positions:
            # Count by type
            if position.pos_type == PositionType.OPTION:
                options_count += 1
                # Premium paid/received
                premium = position.mark_value or 0
                if position.side == PositionSide.BUY:
                    net_premium -= premium  # Paid premium
                else:
                    net_premium += premium  # Received premium
                
                # Update expiry breakdown
                if position.series:
                    if position.series not in expiry_breakdown:
                        expiry_breakdown[position.series] = {
                            "options_count": 0,
                            "total_delta": 0.0,
                            "total_theta": 0.0,
                            "net_premium": 0.0
                        }
                    
                    expiry_breakdown[position.series]["options_count"] += 1
            else:
                linear_count += 1
            
            # Update coin breakdown
            coin = position.base_coin
            if coin not in coin_breakdown:
                coin_breakdown[coin] = {
                    "positions_count": 0,
                    "total_delta": 0.0,
                    "total_theta": 0.0
                }
            
            coin_breakdown[coin]["positions_count"] += 1
            
            # Aggregate Greeks
            if position.greeks:
                delta_multiplier = 1.0 if position.side == PositionSide.BUY else -1.0
                total_delta += position.greeks.delta_coin * delta_multiplier
                total_gamma += position.greeks.gamma_coin * delta_multiplier
                total_vega += position.greeks.vega_usd * delta_multiplier
                total_theta += position.greeks.theta_usd * delta_multiplier
                
                # Update expiry breakdown Greeks
                if position.series and position.series in expiry_breakdown:
                    expiry_breakdown[position.series]["total_delta"] += position.greeks.delta_coin * delta_multiplier
                    expiry_breakdown[position.series]["total_theta"] += position.greeks.theta_usd * delta_multiplier
                
                # Update coin breakdown Greeks
                coin_breakdown[coin]["total_delta"] += position.greeks.delta_coin * delta_multiplier
                coin_breakdown[coin]["total_theta"] += position.greeks.theta_usd * delta_multiplier
        
        return {
            "total_positions": len(positions),
            "options_count": options_count,
            "linear_count": linear_count,
            "total_delta": round(total_delta, 6),
            "total_gamma": round(total_gamma, 6),
            "total_vega": round(total_vega, 2),
            "total_theta": round(total_theta, 2),
            "net_premium": round(net_premium, 2),
            "premium_direction": "paid" if net_premium < 0 else "received",
            "expiry_breakdown": expiry_breakdown,
            "coin_breakdown": coin_breakdown
        }
    
    def calculate_payoff_by_expiry(
        self,
        positions: List[PositionModel],
        current_price: float,
        expiry_series: str,
        price_range_pct: float = 20.0,
        days_to_expiry: Optional[int] = None,
        mode: PayoffCalculationMode = PayoffCalculationMode.AT_EXPIRY
    ) -> PayoffResult:
        """
        Calculate P&L for positions in a specific expiry series
        
        Useful for analyzing individual expiry dates separately
        
        Args:
            positions: All portfolio positions
            current_price: Current underlying price
            expiry_series: Expiry series to filter (e.g., '19DEC25')
            price_range_pct: Percentage range around current price
            days_to_expiry: Days until expiry
            mode: Calculation mode
            
        Returns:
            PayoffResult for the specified expiry series
        """
        # Filter positions by expiry series
        filtered_positions = [
            p for p in positions
            if p.series == expiry_series
        ]
        
        if not filtered_positions:
            logger.warning(f"No positions found for expiry series: {expiry_series}")
            return self._empty_result(current_price)
        
        # Generate cache key for this specific calculation
        cache_key = f"payoff_expiry_{expiry_series}_{len(filtered_positions)}"
        
        return self.calculate_payoff_at_expiry(
            positions=filtered_positions,
            current_price=current_price,
            price_range_pct=price_range_pct,
            days_to_expiry=days_to_expiry,
            mode=mode,
            cache_key=cache_key
        )
    
    def calculate_payoff_by_coin(
        self,
        positions: List[PositionModel],
        current_prices: Dict[str, float],
        coin: str,
        price_range_pct: float = 20.0,
        days_to_expiry: Optional[int] = None,
        mode: PayoffCalculationMode = PayoffCalculationMode.AT_EXPIRY
    ) -> PayoffResult:
        """
        Calculate P&L for positions in a specific coin
        
        Args:
            positions: All portfolio positions
            current_prices: Dictionary of current prices by coin
            coin: Base coin to filter (e.g., 'BTC')
            price_range_pct: Percentage range around current price
            days_to_expiry: Days until expiry
            mode: Calculation mode
            
        Returns:
            PayoffResult for the specified coin
        """
        # Filter positions by coin
        filtered_positions = [
            p for p in positions
            if p.base_coin == coin
        ]
        
        if not filtered_positions:
            logger.warning(f"No positions found for coin: {coin}")
            return self._empty_result(current_prices.get(coin, 0))
        
        current_price = current_prices.get(coin)
        if not current_price:
            logger.warning(f"No current price available for coin: {coin}")
            # Try to get price from first position's mark value or use default
            current_price = filtered_positions[0].mark_value or 1000
        
        # Generate cache key
        cache_key = f"payoff_coin_{coin}_{len(filtered_positions)}"
        
        return self.calculate_payoff_at_expiry(
            positions=filtered_positions,
            current_price=current_price,
            price_range_pct=price_range_pct,
            days_to_expiry=days_to_expiry,
            mode=mode,
            cache_key=cache_key
        )


# Convenience function for API usage
def calculate_payoff_at_expiry(
    positions: List[PositionModel],
    current_price: float,
    price_range_pct: float = 20.0,
    days_to_expiry: Optional[int] = None,
    include_theta: bool = False,
    enable_cache: bool = True
) -> Dict[str, Any]:
    """
    High-level function for API usage with real-time data integration
    
    Enhanced for frontend integration:
    - Caching for performance
    - Detailed summary with expiry breakdown
    - Support for theta decay calculations
    - Performance metrics
    
    Args:
        positions: List of PositionModel objects from real portfolio
        current_price: Current underlying price from market data
        price_range_pct: Percentage range around current price
        days_to_expiry: Days until expiry
        include_theta: Whether to include theta decay
        enable_cache: Enable caching for repeated calculations
        
    Returns:
        Dictionary with payoff data for JSON serialization
    """
    calculator = PayoffCalculator(enable_cache=enable_cache)
    
    mode = (
        PayoffCalculationMode.WITH_THETA if include_theta
        else PayoffCalculationMode.AT_EXPIRY
    )
    
    # Generate cache key based on inputs
    import hashlib
    inputs_str = f"{len(positions)}_{current_price}_{price_range_pct}_{days_to_expiry}_{mode}"
    cache_key = hashlib.md5(inputs_str.encode()).hexdigest() if enable_cache else None
    
    result = calculator.calculate_payoff_at_expiry(
        positions=positions,
        current_price=current_price,
        price_range_pct=price_range_pct,
        days_to_expiry=days_to_expiry,
        mode=mode,
        cache_key=cache_key
    )
    
    # Calculate detailed summary
    summary = calculator.calculate_portfolio_summary(positions, current_price)
    
    # Calculate per-expiry payoff if multiple expiry series exist
    expiry_payoffs = {}
    expiry_series = set(p.series for p in positions if p.series)
    
    if len(expiry_series) > 1:
        for series in expiry_series:
            expiry_result = calculator.calculate_payoff_by_expiry(
                positions=positions,
                current_price=current_price,
                expiry_series=series,
                price_range_pct=price_range_pct,
                days_to_expiry=days_to_expiry,
                mode=mode
            )
            
            expiry_payoffs[series] = {
                "current_pnl": round(expiry_result.current_pnl, 2),
                "max_profit": round(expiry_result.max_profit, 2),
                "max_loss": round(expiry_result.max_loss, 2),
                "breakeven_points": expiry_result.breakeven_points,
                "positions_count": len([p for p in positions if p.series == series])
            }
    
    # Convert to JSON-serializable format
    return {
        "current_price": result.current_price,
        "current_pnl": round(result.current_pnl, 2),
        "price_range": [round(p, 2) for p in result.price_range.tolist()],
        "pnl": [round(p, 2) for p in result.pnl_array.tolist()],
        "breakeven_points": result.breakeven_points,
        "max_profit": round(result.max_profit, 2),
        "max_loss": round(result.max_loss, 2),
        "max_profit_price": round(result.max_profit_price, 2),
        "max_loss_price": round(result.max_loss_price, 2),
        "mode": result.mode.value,
        "summary": summary,
        "expiry_payoffs": expiry_payoffs,
        "metadata": {
            "positions_count": len(positions),
            "options_count": summary["options_count"],
            "linear_count": summary["linear_count"],
            "calculation_timestamp": datetime.utcnow().isoformat(),
            "cache_used": cache_key is not None,
            "theta_included": include_theta,
            "days_to_expiry": days_to_expiry
        }
    }


def calculate_payoff_for_api(
    positions: List[PositionModel],
    current_prices: Dict[str, float],
    base_coin: str = "BTC",
    price_range_pct: float = 20.0,
    days_to_expiry: Optional[int] = None,
    include_theta: bool = False
) -> Dict[str, Any]:
    """
    API-friendly function for frontend integration
    
    Handles multi-coin portfolios and provides comprehensive payoff data
    
    Args:
        positions: All portfolio positions
        current_prices: Dictionary of current prices by coin
        base_coin: Primary coin for calculation (default: BTC)
        price_range_pct: Percentage range around current price
        days_to_expiry: Days until expiry
        include_theta: Whether to include theta decay
        
    Returns:
        Comprehensive payoff data for frontend display
    """
    # Filter positions for the base coin
    coin_positions = [p for p in positions if p.base_coin == base_coin]
    
    if not coin_positions:
        return {
            "error": f"No positions found for base coin: {base_coin}",
            "current_price": current_prices.get(base_coin, 0),
            "price_range": [],
            "pnl": [],
            "breakeven_points": [],
            "max_profit": 0,
            "max_loss": 0
        }
    
    current_price = current_prices.get(base_coin)
    if not current_price:
        # Fallback to average of position mark values
        mark_values = [p.mark_value for p in coin_positions if p.mark_value]
        current_price = sum(mark_values) / len(mark_values) if mark_values else 1000
    
    # Calculate payoff
    payoff_data = calculate_payoff_at_expiry(
        positions=coin_positions,
        current_price=current_price,
        price_range_pct=price_range_pct,
        days_to_expiry=days_to_expiry,
        include_theta=include_theta,
        enable_cache=True
    )
    
    # Add coin-specific metadata
    payoff_data["base_coin"] = base_coin
    payoff_data["current_price_source"] = "market" if base_coin in current_prices else "estimated"
    
    return payoff_data


if __name__ == "__main__":
    # Test the calculator
    import sys
    sys.path.append(".")
    
    from data_models import PositionModel, PositionSide, PositionType, OptionType, GreeksModel
    
    # Create test positions
    test_positions = [
        PositionModel(
            symbol="BTC-19DEC25-95000-C-USDT",
            side=PositionSide.BUY,
            size=1.0,
            pos_type=PositionType.OPTION,
            base_coin="BTC",
            series="19DEC25",
            option_type=OptionType.CALL,
            strike=95000.0,
            greeks=GreeksModel(
                delta_coin=0.5234,
                theta_usd=-45.67
            ),
            mark_value=2345.67
        ),
        PositionModel(
            symbol="BTCUSDT",
            side=PositionSide.SELL,
            size=0.5,
            pos_type=PositionType.LINEAR,
            base_coin="BTC",
            entry_price=96000.0
        )
    ]
    
    calculator = PayoffCalculator(precision=100)
    result = calculator.calculate_payoff_at_expiry(
        positions=test_positions,
        current_price=95000.0,
        price_range_pct=20.0,
        days_to_expiry=7,
        mode=PayoffCalculationMode.WITH_THETA
    )
    
    print("Payoff Calculation Test")
    print(f"Current price: ${result.current_price:,.2f}")
    print(f"Current P&L: ${result.current_pnl:,.2f}")
    print(f"Breakeven points: {result.breakeven_points}")
    print(f"Max profit: ${result.max_profit:,.2f} at ${result.max_profit_price:,.2f}")
    print(f"Max loss: ${result.max_loss:,.2f} at ${result.max_loss_price:,.2f}")
    
    summary = calculator.calculate_portfolio_summary(test_positions, 95000.0)
    print(f"\nPortfolio summary: {summary}")