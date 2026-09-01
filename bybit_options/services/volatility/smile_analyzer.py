"""
Volatility Smile Analyzer.
Builds market smile from option chain and fits SVI model.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

import numpy as np
from scipy.optimize import minimize
from loguru import logger


@dataclass
class SmilePoint:
    """Single point on volatility smile."""
    strike: float
    moneyness: float      # log(K/F)
    market_iv: float      # IV from exchange
    delta: Optional[float] = None


@dataclass
class VolatilitySmile:
    """Full volatility smile with metrics."""
    symbol: str
    expiry: str
    spot_price: float
    forward_price: float
    time_to_expiry: float
    
    # Raw data
    market_points: List[SmilePoint] = field(default_factory=list)
    
    # Fitted SVI parameters
    svi_params: Optional[Dict[str, float]] = None  # {a, b, rho, m, sigma}
    
    # Key metrics
    atm_iv: float = 0.0
    put_skew_25d: float = 0.0   # IV(25d put) - ATM
    call_skew_25d: float = 0.0  # IV(25d call) - ATM
    skew_slope: float = 0.0     # dIV/dMoneyness at ATM
    
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def get_model_iv(self, strike: float) -> float:
        """
        Get model IV for any strike using fitted SVI.
        
        Args:
            strike: Strike price
        
        Returns:
            Model-implied IV or 0 if no fit
        """
        if not self.svi_params or self.time_to_expiry <= 0:
            return 0.0
        
        k = np.log(strike / self.forward_price)
        a = self.svi_params['a']
        b = self.svi_params['b']
        rho = self.svi_params['rho']
        m = self.svi_params['m']
        sigma = self.svi_params['sigma']
        
        # SVI total variance
        w = a + b * (rho * (k - m) + np.sqrt((k - m)**2 + sigma**2))
        
        if w < 0:
            return 0.0
        
        return np.sqrt(w / self.time_to_expiry)


class SmileAnalyzer:
    """
    Analyzes volatility smile from option chain data.
    
    Builds two smiles:
    1. Market smile - from exchange IV data
    2. Model smile - fitted SVI curve
    """
    
    def __init__(self, market_data=None):
        """
        Args:
            market_data: MarketDataActor for fetching option tickers
        """
        self.market_data = market_data
    
    async def build_smile(
        self,
        symbol: str,
        expiry: str,
        spot_price: float,
        option_chain: Optional[List[Dict[str, Any]]] = None
    ) -> VolatilitySmile:
        """
        Build volatility smile from option chain.
        
        Args:
            symbol: "BTC" or "ETH"
            expiry: "26JAN26" format
            spot_price: Current spot price
            option_chain: Optional pre-fetched option data
        
        Returns:
            VolatilitySmile with market data and fitted model
        """
        try:
            # Get option chain if not provided
            if option_chain is None:
                if self.market_data is None:
                    logger.warning("No market data source provided")
                    return self._empty_smile(symbol, expiry, spot_price)
                
                option_chain = await self._fetch_option_chain(symbol, expiry)
            
            if not option_chain or len(option_chain) < 5:
                logger.warning(f"Not enough options for smile: {len(option_chain) if option_chain else 0}")
                return self._empty_smile(symbol, expiry, spot_price)
            
            # Calculate forward price (simplified: F ≈ S for short expiry)
            # In practice, use put-call parity or futures price
            forward_price = spot_price
            
            # Extract time to expiry from first option
            time_to_expiry = self._parse_time_to_expiry(expiry)
            
            # Build market points
            market_points = []
            for opt in option_chain:
                strike = float(opt.get('strike', 0))
                iv = float(opt.get('iv', 0) or opt.get('mark_iv', 0))
                
                if strike <= 0 or iv <= 0:
                    continue
                
                moneyness = np.log(strike / forward_price)
                
                market_points.append(SmilePoint(
                    strike=strike,
                    moneyness=moneyness,
                    market_iv=iv,
                    delta=opt.get('delta')
                ))
            
            if len(market_points) < 5:
                logger.warning(f"Not enough valid points for smile: {len(market_points)}")
                return self._empty_smile(symbol, expiry, spot_price)
            
            # Sort by strike
            market_points.sort(key=lambda p: p.strike)
            
            # Fit SVI model
            svi_params = self._fit_svi(market_points, forward_price, time_to_expiry)
            
            # Calculate skew metrics
            atm_iv, put_skew, call_skew, skew_slope = self._calculate_skew_metrics(
                market_points, spot_price, forward_price
            )
            
            return VolatilitySmile(
                symbol=symbol,
                expiry=expiry,
                spot_price=spot_price,
                forward_price=forward_price,
                time_to_expiry=time_to_expiry,
                market_points=market_points,
                svi_params=svi_params,
                atm_iv=atm_iv,
                put_skew_25d=put_skew,
                call_skew_25d=call_skew,
                skew_slope=skew_slope
            )
            
        except Exception as e:
            logger.error(f"Failed to build smile for {symbol}/{expiry}: {e}")
            return self._empty_smile(symbol, expiry, spot_price)
    
    def _fit_svi(
        self, 
        points: List[SmilePoint],
        forward: float,
        T: float
    ) -> Optional[Dict[str, float]]:
        """
        Fit SVI model to market data.
        
        SVI formula:
        w(k) = a + b * (ρ*(k-m) + sqrt((k-m)² + σ²))
        
        where k = log(K/F), w = IV² * T
        
        Returns:
            Dict with SVI parameters {a, b, rho, m, sigma} or None
        """
        if len(points) < 5:
            return None
        
        try:
            # Prepare data
            strikes = np.array([p.strike for p in points])
            ivs = np.array([p.market_iv for p in points])
            k = np.log(strikes / forward)  # Log-moneyness
            
            # Initial guess
            x0 = [0.04, 0.1, -0.3, 0.0, 0.1]  # a, b, rho, m, sigma
            
            # Bounds to ensure no-arbitrage
            bounds = [
                (0.001, 1.0),    # a > 0
                (0.001, 1.0),    # b > 0
                (-0.99, 0.99),   # -1 < rho < 1
                (-0.5, 0.5),     # m around 0
                (0.001, 1.0)     # sigma > 0
            ]
            
            def objective(params):
                a, b, rho, m, sigma = params
                w_model = a + b * (rho * (k - m) + np.sqrt((k - m)**2 + sigma**2))
                
                # Avoid negative variance
                w_model = np.maximum(w_model, 0.001)
                
                iv_model = np.sqrt(w_model / T)
                return np.sum((iv_model - ivs)**2)
            
            result = minimize(objective, x0, bounds=bounds, method='L-BFGS-B')
            
            if result.success:
                a, b, rho, m, sigma = result.x
                return {'a': float(a), 'b': float(b), 'rho': float(rho), 'm': float(m), 'sigma': float(sigma)}
            else:
                logger.warning(f"SVI fit failed: {result.message}")
                return None
                
        except Exception as e:
            logger.error(f"SVI fitting error: {e}")
            return None
    
    def _calculate_skew_metrics(
        self,
        points: List[SmilePoint],
        spot: float,
        forward: float
    ) -> tuple:
        """
        Calculate skew metrics.
        
        Returns:
            (atm_iv, put_skew_25d, call_skew_25d, skew_slope)
        """
        if not points:
            return 0.0, 0.0, 0.0, 0.0
        
        # Find ATM strike (closest to spot)
        atm_point = min(points, key=lambda p: abs(p.strike - spot))
        atm_iv = atm_point.market_iv
        
        # Find approximate 25-delta strikes
        # 25 delta put ≈ 0.9 * spot
        # 25 delta call ≈ 1.1 * spot
        put_25d_strike = spot * 0.9
        call_25d_strike = spot * 1.1
        
        # Find closest points
        put_25d_point = min(points, key=lambda p: abs(p.strike - put_25d_strike))
        call_25d_point = min(points, key=lambda p: abs(p.strike - call_25d_strike))
        
        put_skew = put_25d_point.market_iv - atm_iv
        call_skew = call_25d_point.market_iv - atm_iv
        
        # Calculate skew slope at ATM (dIV/dMoneyness)
        # Use finite difference around ATM
        atm_idx = points.index(atm_point)
        
        if atm_idx > 0 and atm_idx < len(points) - 1:
            left = points[atm_idx - 1]
            right = points[atm_idx + 1]
            
            dm = right.moneyness - left.moneyness
            div = right.market_iv - left.market_iv
            
            skew_slope = div / dm if abs(dm) > 0.001 else 0.0
        else:
            skew_slope = 0.0
        
        return atm_iv, put_skew, call_skew, skew_slope
    
    async def _fetch_option_chain(self, symbol: str, expiry: str) -> List[Dict]:
        """
        Fetch option chain from market data.
        """
        if self.market_data is None:
            return []
        
        # Use market data actor's ticker cache
        # Filter by symbol and expiry
        all_tickers = getattr(self.market_data, 'ticker_cache', {})
        
        chain = []
        for ticker_symbol, data in all_tickers.items():
            if symbol in ticker_symbol and expiry in ticker_symbol:
                chain.append({
                    'symbol': ticker_symbol,
                    'strike': self._parse_strike(ticker_symbol),
                    'iv': data.get('iv') or data.get('markIv'),
                    'delta': data.get('delta')
                })
        
        return chain
    
    def _parse_strike(self, symbol: str) -> float:
        """
        Parse strike from option symbol.
        Example: BTC-26JAN26-100000-C -> 100000
        """
        try:
            parts = symbol.split('-')
            if len(parts) >= 3:
                return float(parts[2])
        except:
            pass
        return 0.0
    
    def _parse_time_to_expiry(self, expiry: str) -> float:
        """
        Parse time to expiry from expiry string.
        """
        from bybit_options.services.amm.time_calculator import calculate_time_to_expiry
        
        try:
            # Create dummy symbol to use existing calculator
            dummy_symbol = f"BTC-{expiry}-100000-C"
            return calculate_time_to_expiry(dummy_symbol)
        except:
            return 0.5  # Default to ~6 months
    
    def _empty_smile(self, symbol: str, expiry: str, spot: float) -> VolatilitySmile:
        """Create empty smile when data is unavailable."""
        return VolatilitySmile(
            symbol=symbol,
            expiry=expiry,
            spot_price=spot,
            forward_price=spot,
            time_to_expiry=0.5,
            market_points=[],
            svi_params=None,
            atm_iv=0.0,
            put_skew_25d=0.0,
            call_skew_25d=0.0,
            skew_slope=0.0
        )
