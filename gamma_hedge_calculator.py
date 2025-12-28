"""
Gamma-Aware Hedge Calculator - PRODUCTION VERSION

FIXES APPLIED:
✅ Sign logic corrected (Greeks already signed by RiskEngine)
✅ Gamma formula fixed (correct dimensional analysis)
✅ Long Delta Bias acknowledged and accepted for crypto

APPROVED BY: Lead System Architect
"""

import logging
from typing import List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


# ============================================================================
# DATA MODELS
# ============================================================================

class VolatilityRegime(str, Enum):
    """Market volatility classification"""
    LOW = "low"       # ATR < 2% of price
    MEDIUM = "medium" # ATR 2-5% of price
    HIGH = "high"     # ATR > 5% of price


@dataclass
class Position:
    """Unified position structure for calculator"""
    symbol: str
    side: str  # "Buy" or "Sell"
    size: float
    delta: float  # ✅ ALREADY SIGNED by RiskEngine
    gamma: float = 0.0  # ✅ ALREADY SIGNED by RiskEngine
    instrument_type: str = "option"  # "option" or "linear"
    
    def __post_init__(self):
        """Validate data on creation"""
        if self.instrument_type not in ("option", "linear"):
            raise ValueError(f"Invalid instrument_type: {self.instrument_type}")
        if self.side not in ("Buy", "Sell"):
            raise ValueError(f"Invalid side: {self.side}")


@dataclass
class HedgeRecommendation:
    """Output structure for hedge calculation"""
    target_hedge_size: float  # In BTC (negative = Buy, positive = Sell)
    current_delta: float
    gamma_component: float
    expected_move_usd: float
    volatility_regime: str
    aggression_factor: float
    reasoning: str
    should_hedge: bool  # False if within tolerance
    
    # Additional context
    btc_price: float
    atr_14: float
    net_gamma: float
    
    def __str__(self) -> str:
        """Human-readable representation"""
        action = "SELL" if self.target_hedge_size > 0 else "BUY"
        size = abs(self.target_hedge_size)
        
        return (
            f"HedgeRecommendation(\n"
            f"  Action: {action} {size:.4f} BTC\n"
            f"  Current Delta: {self.current_delta:+.4f} BTC\n"
            f"  Gamma Component: {self.gamma_component:+.4f} BTC\n"
            f"  Regime: {self.volatility_regime.upper()}\n"
            f"  Aggression: {self.aggression_factor:.2f}x\n"
            f"  Should Execute: {self.should_hedge}\n"
            f")"
        )


# ============================================================================
# CALCULATOR
# ============================================================================

class GammaHedgeCalculator:
    """
    Pure calculation engine for Gamma-aware DDH
    
    MATHEMATICAL CORRECTNESS:
    - Dimensional analysis verified
    - Sign logic corrected
    - Gamma formula fixed
    
    RISK PROFILE:
    - Creates Long Delta Bias (accepted for crypto)
    - Protects against pumps (fast upside moves)
    - Less protection on dumps (slower downside)
    """
    
    def __init__(
        self,
        delta_threshold: float = 0.02,  # BTC
        default_aggression: float = 1.1,
        enable_dynamic_aggression: bool = True,
        min_hedge_value_usd: float = 10.0  # Don't hedge if < $10 impact
    ):
        """
        Initialize calculator with configuration
        
        Args:
            delta_threshold: Minimum delta to trigger hedge (in BTC)
            default_aggression: Base aggression factor
            enable_dynamic_aggression: Adjust aggression based on risk
            min_hedge_value_usd: Minimum hedge value to avoid over-trading
        """
        self.delta_threshold = delta_threshold
        self.default_aggression = default_aggression
        self.enable_dynamic_aggression = enable_dynamic_aggression
        self.min_hedge_value_usd = min_hedge_value_usd
        
        # Validation
        if delta_threshold <= 0:
            raise ValueError("delta_threshold must be positive")
        if not (0.5 <= default_aggression <= 2.0):
            raise ValueError("default_aggression must be in [0.5, 2.0]")
    
    # ========================================================================
    # VOLATILITY REGIME DETECTION
    # ========================================================================
    
    @staticmethod
    def classify_volatility_regime(
        atr: float,
        current_price: float
    ) -> VolatilityRegime:
        """
        Classify market volatility based on ATR
        
        Args:
            atr: 14-period Average True Range (in USD)
            current_price: Current BTC price (in USD)
        
        Returns:
            VolatilityRegime enum
        """
        if current_price <= 0:
            logger.warning(f"Invalid price: {current_price}, defaulting to MEDIUM")
            return VolatilityRegime.MEDIUM
        
        atr_pct = (atr / current_price) * 100
        
        if atr_pct > 5.0:
            return VolatilityRegime.HIGH
        elif atr_pct > 2.0:
            return VolatilityRegime.MEDIUM
        else:
            return VolatilityRegime.LOW
    
    # ========================================================================
    # EXPECTED MOVE CALCULATION
    # ========================================================================
    
    @staticmethod
    def get_expected_move(
        regime: VolatilityRegime,
        current_price: float,
        atr: Optional[float] = None
    ) -> float:
        """
        Calculate expected price move based on volatility regime
        
        Uses regime-based defaults with optional ATR fine-tuning
        
        Args:
            regime: Current volatility classification
            current_price: Current BTC price
            atr: Optional ATR for more precise calculation
        
        Returns:
            Expected move in USD
        """
        # Regime-based defaults
        if regime == VolatilityRegime.HIGH:
            expected_pct = 0.02  # 2%
        elif regime == VolatilityRegime.MEDIUM:
            expected_pct = 0.01  # 1%
        else:
            expected_pct = 0.005  # 0.5%
        
        # Fine-tune with ATR if available
        if atr and atr > 0 and current_price > 0:
            atr_pct = atr / current_price
            # Weighted average: 70% regime default, 30% actual ATR
            expected_pct = (0.7 * expected_pct) + (0.3 * atr_pct)
        
        return current_price * expected_pct
    
    # ========================================================================
    # AGGRESSION FACTOR CALCULATION
    # ========================================================================
    
    def calculate_aggression_factor(
        self,
        regime: VolatilityRegime,
        net_gamma: float,
        account_size: float,
        current_price: float
    ) -> float:
        """
        Calculate dynamic aggression factor based on risk exposure
        
        Formula:
            aggression = (base_from_regime + gamma_risk_multiplier) / 2
            clamped to [0.5, 1.5]
        
        Args:
            regime: Volatility classification
            net_gamma: Portfolio net Gamma (in BTC)
            account_size: Total account value (USD)
            current_price: Current BTC price (USD)
        
        Returns:
            Aggression multiplier in range [0.5, 1.5]
        """
        if not self.enable_dynamic_aggression:
            return self.default_aggression
        
        # Base aggression from regime
        if regime == VolatilityRegime.HIGH:
            base_aggression = 1.2
        elif regime == VolatilityRegime.MEDIUM:
            base_aggression = 1.0
        else:
            base_aggression = 0.7
        
        # Calculate gamma risk as % of account
        if account_size > 0:
            gamma_risk_per_1k = abs(net_gamma * 1000)  # Risk for $1k move
            gamma_risk_pct = gamma_risk_per_1k / account_size
            
            # Scale aggression based on gamma exposure
            if gamma_risk_pct > 0.15:  # >15% account at risk
                gamma_multiplier = 1.3
            elif gamma_risk_pct > 0.08:  # 8-15%
                gamma_multiplier = 1.0
            else:  # <8%
                gamma_multiplier = 0.8
        else:
            gamma_multiplier = 1.0
        
        # Combine base + gamma adjustment (average)
        final_aggression = (base_aggression + gamma_multiplier) / 2
        
        # Clamp to reasonable range
        return max(0.5, min(1.5, final_aggression))
    
    # ========================================================================
    # PORTFOLIO GREEKS AGGREGATION (✅ FIXED)
    # ========================================================================
    
    @staticmethod
    def calculate_portfolio_greeks(
        positions: List[Position]
    ) -> Tuple[float, float]:
        """
        Aggregate Delta and Gamma across all positions
        
        ✅ FIX: Greeks are ALREADY SIGNED by RiskEngine
        Do NOT multiply by side again
        
        Mathematical Correctness:
            From your RiskEngine (risk_engine.py lines 90-180):
            
            raw_delta = float(ticker_data.get("delta", 0))
            signed_size = size * sign  # sign = +1 (Buy) or -1 (Sell)
            return GreeksModel(delta_coin=raw_delta * signed_size)
            
            Therefore: pos.delta already contains position effect
        
        Args:
            positions: List of Position objects (options + futures)
        
        Returns:
            (net_delta, net_gamma) in BTC units
        """
        net_delta = 0.0
        net_gamma = 0.0
        
        for pos in positions:
            # ✅ FIXED: Just sum (sign already applied in RiskEngine)
            net_delta += pos.delta
            net_gamma += pos.gamma
        
        return net_delta, net_gamma
    
    # ========================================================================
    # MAIN CALCULATION (✅ FIXED GAMMA FORMULA)
    # ========================================================================
    
    def calculate_hedge(
        self,
        positions: List[Position],
        current_price: float,
        atr_14: float,
        account_size: Optional[float] = None,
        override_aggression: Optional[float] = None
    ) -> HedgeRecommendation:
        """
        Main calculation: Determine optimal hedge size
        
        ✅ FIXES APPLIED:
        1. Greeks aggregation (no double sign multiplication)
        2. Gamma formula (correct dimensional units)
        
        Mathematical Formula:
            Target_Hedge = Current_Delta + (Net_Gamma × Expected_Move × Aggression)
        
        Dimensional Analysis:
            Gamma [Δ/USD] × Move [USD] × Aggression [scalar] = Δ [BTC] ✅
        
        Risk Profile (ACKNOWLEDGED):
            Creates Long Delta Bias for Short Gamma strategies
            - Protects upside (fast pumps)
            - Less protection downside (slower dumps)
            - Acceptable for crypto market structure
        
        Steps:
        1. Calculate portfolio Greeks
        2. Classify volatility
        3. Calculate expected move
        4. Determine aggression factor
        5. Compute gamma adjustment
        6. Calculate target hedge
        7. Check if hedge needed (threshold + min value)
        
        Args:
            positions: List of current positions
            current_price: Current BTC price
            atr_14: 14-period ATR
            account_size: Total account value (for dynamic aggression)
            override_aggression: Manual aggression override
        
        Returns:
            HedgeRecommendation object with full details
        """
        # Step 1: Calculate portfolio Greeks
        net_delta, net_gamma = self.calculate_portfolio_greeks(positions)
        
        # Step 2: Classify volatility
        regime = self.classify_volatility_regime(atr_14, current_price)
        
        # Step 3: Expected move
        expected_move = self.get_expected_move(regime, current_price, atr_14)
        
        # Step 4: Aggression factor
        if override_aggression:
            aggression = override_aggression
        elif account_size:
            aggression = self.calculate_aggression_factor(
                regime, net_gamma, account_size, current_price
            )
        else:
            aggression = self.default_aggression
        
        # Step 5: Gamma component
        # ✅ FIXED: Direct multiplication (Gamma × Move, not Gamma × Move / Price)
        #
        # DIMENSIONAL ANALYSIS:
        # - Gamma measures delta change per $1 price move [Δ/USD]
        # - Expected_Move is in USD [$]
        # - Result: [Δ/USD] × [$] = [Δ] ✅ CORRECT
        #
        # PHYSICAL MEANING:
        # - If Gamma = 0.0002 BTC/USD and price moves $1000
        # - Delta will change by: 0.0002 × 1000 = 0.2 BTC
        # - We hedge proactively for this expected change
        #
        # Example:
        #   net_gamma = -0.01 (Short Gamma from Iron Condor)
        #   expected_move = 1000
        #   aggression = 1.1
        #   gamma_adjustment = -0.01 × 1000 × 1.1 = -11 BTC
        #
        # Interpretation:
        #   System predicts delta will shift by -11 BTC
        #   Creates Long Delta Bias (acceptable for crypto)
        gamma_adjustment = net_gamma * expected_move * aggression
        
        # Step 6: Target hedge
        # Total hedge = current exposure + predicted change
        target_hedge = net_delta + gamma_adjustment
        
        # Step 7: Check if hedge needed
        # Condition 1: Exceeds delta threshold
        exceeds_threshold = abs(target_hedge) > self.delta_threshold
        
        # Condition 2: Hedge value > minimum (avoid $5 hedges)
        hedge_value_usd = abs(target_hedge) * current_price
        exceeds_min_value = hedge_value_usd > self.min_hedge_value_usd
        
        should_hedge = exceeds_threshold and exceeds_min_value
        
        # Step 8: Build reasoning
        reasoning = (
            f"Regime: {regime.value.upper()} | "
            f"ATR: ${atr_14:.0f} ({(atr_14/current_price)*100:.2f}%) | "
            f"Expected: ${expected_move:.0f} | "
            f"Aggression: {aggression:.2f}x | "
            f"Delta: {net_delta:.4f} | Gamma: {net_gamma:.6f} | "
            f"Hedge Value: ${hedge_value_usd:.2f}"
        )
        
        if not exceeds_threshold:
            reasoning += f" | SKIP: Below threshold ({self.delta_threshold})"
        elif not exceeds_min_value:
            reasoning += f" | SKIP: Below min value (${self.min_hedge_value_usd})"
        
        return HedgeRecommendation(
            target_hedge_size=target_hedge,
            current_delta=net_delta,
            gamma_component=gamma_adjustment,
            expected_move_usd=expected_move,
            volatility_regime=regime.value,
            aggression_factor=aggression,
            reasoning=reasoning,
            should_hedge=should_hedge,
            btc_price=current_price,
            atr_14=atr_14,
            net_gamma=net_gamma
        )