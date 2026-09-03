"""
Portfolio Greeks Aggregator for AMM Robot

Calculates aggregated Greeks across all active strategies for risk management.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional
from decimal import Decimal
from loguru import logger

from .models import AmmStrategy
from .pricing import OptionPricing
from bybit_options.core.risk_engine import RiskEngine


@dataclass
class PortfolioGreeks:
    """Aggregated Greeks for the entire AMM portfolio."""
    delta: float = 0.0
    gamma: float = 0.0
    vega: float = 0.0
    theta: float = 0.0


class GreeksAggregator:
    """
    Aggregates Greeks across all active AMM strategies.
    
    Used for portfolio-level risk management and delta gating.
    """
    
    def calculate(
        self,
        strategies: List[AmmStrategy],
        spot_prices: Dict[str, float],       # {"BTC": 104500.0}
        market_ivs: Dict[str, float],        # {"BTC-26JUN26-100000-C": 0.45}
        time_to_expiries: Dict[str, float]   # {"BTC-26JUN26-100000-C": 0.42}
    ) -> PortfolioGreeks:
        """
        Calculate portfolio-level Greeks.
        
        Args:
            strategies: List of active strategies
            spot_prices: Current spot prices by base coin
            market_ivs: Market IVs by option symbol
            time_to_expiries: Time to expiry by option symbol
            
        Returns:
            PortfolioGreeks with aggregated delta, gamma, vega, theta
            
        Notes:
            - BUY legs contribute positive Greeks
            - SELL legs contribute negative Greeks
            - Position size is multiplied by Greeks
        """
        total = PortfolioGreeks()
        
        legs_processed = 0
        legs_skipped = 0
        
        for strategy in strategies:
            if not strategy.is_active or strategy.is_paused:
                continue
            
            for leg in strategy.legs:
                if not leg.is_active:
                    continue
                
                symbol = leg.symbol
                
                # Parse symbol for option parameters
                try:
                    parsed = RiskEngine.parse_symbol(symbol)
                    base = parsed.get("base")
                    strike = parsed.get("strike")
                    opt_type = parsed.get("type", "C")
                    
                    if not all([base, strike, opt_type]):
                        logger.warning(f"[GreeksAgg] Incomplete parse for {symbol}")
                        legs_skipped += 1
                        continue
                    
                    # Get market data
                    spot = spot_prices.get(base)
                    iv = market_ivs.get(symbol)
                    T = time_to_expiries.get(symbol)
                    
                    # Skip if data incomplete
                    if not all([spot, iv, T]):
                        logger.debug(f"[GreeksAgg] Missing data for {symbol}: spot={spot}, iv={iv}, T={T}")
                        legs_skipped += 1
                        continue
                    
                    # Calculate Greeks for this leg
                    greeks = OptionPricing.calculate_greeks(
                        spot=spot,
                        strike=float(strike),
                        time_to_expiry=T,
                        risk_free_rate=0.0,
                        iv=iv,
                        option_type=opt_type
                    )
                    
                    # Position size (use total_filled, default to 0)
                    size = float(leg.total_filled or 0)
                    
                    if size == 0:
                        continue

                    # Side multiplier: BUY = +, SELL = -
                    multiplier = size if leg.side == "BUY" else -size
                    
                    # Accumulate
                    total.delta += greeks["delta"] * multiplier
                    total.gamma += greeks["gamma"] * multiplier
                    total.vega += (greeks["vega"] / 100.0) * multiplier  # Standardize Vega per 1% vol
                    total.theta += greeks["theta"] * multiplier
                    
                    legs_processed += 1
                    
                except Exception as e:
                    logger.error(f"[GreeksAgg] Error processing {symbol}: {e}")
                    legs_skipped += 1
                    continue
        
        logger.info(
            f"[GreeksAgg] Processed {legs_processed} legs, skipped {legs_skipped}. "
            f"Portfolio: Δ={total.delta:.4f} Γ={total.gamma:.6f} ν={total.vega:.2f} θ={total.theta:.2f}"
        )
        
        return total
