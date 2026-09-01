"""
Risk Director - Gatekeeper for AMM Robot (Stage 3)

Centralized risk management module that evaluates portfolio-level and per-leg
order decisions to prevent excessive Delta/Gamma/Vega exposure.
"""

from dataclasses import dataclass
from typing import Optional
from loguru import logger

from .greeks_aggregator import PortfolioGreeks
from .models import AmmLeg


@dataclass
class RiskLimits:
    """Configurable risk limits for Gatekeeper."""
    max_portfolio_delta: float = 1.0
    max_portfolio_gamma: float = 0.05
    max_portfolio_vega: float = 5000.0
    max_leg_delta: float = 0.3
    max_leg_gamma: float = 0.01


@dataclass
class RiskDecision:
    """Result of risk evaluation."""
    decision: str  # 'ALLOW' or 'BLOCK'
    reason: Optional[str] = None


class RiskDirector:
    """
    Centralized risk management for AMM Robot.
    
    Responsibilities:
    - Evaluate portfolio-level risk (total exposure across all strategies)
    - Evaluate per-leg order risk (individual order safety)
    - Log all decisions to database for audit
    
    Usage:
        risk_director = RiskDirector(repo, limits=RiskLimits(...))
        
        # Portfolio-level check
        decision = risk_director.evaluate_portfolio(portfolio_greeks)
        if decision.decision == "BLOCK":
            return  # Skip gardener cycle
        
        # Per-leg check
        for leg in legs:
            leg_decision = risk_director.evaluate_leg_order(leg, delta, gamma, portfolio_greeks)
            if leg_decision.decision == "BLOCK":
                continue  # Skip this leg
    """
    
    def __init__(self, repo, limits: Optional[RiskLimits] = None):
        """
        Initialize Risk Director.
        
        Args:
            repo: AmmRepository instance for database logging
            limits: RiskLimits instance (uses defaults if None)
        """
        self.repo = repo
        self.limits = limits or RiskLimits()
        logger.info(
            f"[Gatekeeper] Initialized with limits: "
            f"Portfolio Δ={self.limits.max_portfolio_delta} "
            f"Γ={self.limits.max_portfolio_gamma} "
            f"V={self.limits.max_portfolio_vega}"
        )
    
    def evaluate_portfolio(
        self, 
        portfolio_greeks: PortfolioGreeks
    ) -> RiskDecision:
        """
        Check if portfolio-level Greeks are within limits.
        
        If ANY limit is breached, the entire gardener cycle should be skipped
        to prevent further risk accumulation.
        
        Args:
            portfolio_greeks: Aggregated Greeks from GreeksAggregator
        
        Returns:
            RiskDecision(ALLOW) if all checks pass
            RiskDecision(BLOCK, reason=...) if any limit breached
        """
        # Delta check
        if abs(portfolio_greeks.total_delta) > self.limits.max_portfolio_delta:
            reason = (
                f"Portfolio Delta={portfolio_greeks.total_delta:.4f} "
                f"exceeds limit {self.limits.max_portfolio_delta}"
            )
            logger.warning(f"[Gatekeeper] 🚫 Portfolio BLOCKED: {reason}")
            return RiskDecision(decision="BLOCK", reason=reason)
        
        # Gamma check
        if abs(portfolio_greeks.total_gamma) > self.limits.max_portfolio_gamma:
            reason = (
                f"Portfolio Gamma={portfolio_greeks.total_gamma:.6f} "
                f"exceeds limit {self.limits.max_portfolio_gamma}"
            )
            logger.warning(f"[Gatekeeper] 🚫 Portfolio BLOCKED: {reason}")
            return RiskDecision(decision="BLOCK", reason=reason)
        
        # Vega check
        if abs(portfolio_greeks.total_vega) > self.limits.max_portfolio_vega:
            reason = (
                f"Portfolio Vega={portfolio_greeks.total_vega:.2f} "
                f"exceeds limit {self.limits.max_portfolio_vega}"
            )
            logger.warning(f"[Gatekeeper] 🚫 Portfolio BLOCKED: {reason}")
            return RiskDecision(decision="BLOCK", reason=reason)
        
        logger.debug("[Gatekeeper] ✅ Portfolio ALLOWED")
        return RiskDecision(decision="ALLOW")
    
    def evaluate_leg_order(
        self,
        leg: AmmLeg,
        leg_delta: float,
        leg_gamma: float,
        portfolio_greeks: PortfolioGreeks
    ) -> RiskDecision:
        """
        Check if placing/amending order for this leg is safe.
        
        Logic:
        1. Check per-leg limits (absolute Delta/Gamma for this single leg)
        2. Check directional exposure:
           - If portfolio Delta is high and leg is BUY (adds positive Delta) → BLOCK
           - If portfolio Delta is low and leg is SELL (adds negative Delta) → BLOCK
        
        Args:
            leg: AmmLeg instance
            leg_delta: Calculated delta for this leg
            leg_gamma: Calculated gamma for this leg
            portfolio_greeks: Current portfolio Greeks
        
        Returns:
            RiskDecision(ALLOW) or RiskDecision(BLOCK, reason=...)
        """
        # Per-leg Delta limit
        if abs(leg_delta) > self.limits.max_leg_delta:
            reason = f"Leg Delta={leg_delta:.4f} exceeds {self.limits.max_leg_delta}"
            logger.warning(f"[Gatekeeper] 🚫 Leg {leg.symbol} BLOCKED: {reason}")
            return RiskDecision(decision="BLOCK", reason=reason)
        
        # Per-leg Gamma limit
        if abs(leg_gamma) > self.limits.max_leg_gamma:
            reason = f"Leg Gamma={leg_gamma:.6f} exceeds {self.limits.max_leg_gamma}"
            logger.warning(f"[Gatekeeper] 🚫 Leg {leg.symbol} BLOCKED: {reason}")
            return RiskDecision(decision="BLOCK", reason=reason)
        
        # Directional exposure check
        # Prevent adding to already-high Delta exposure
        
        # If portfolio Delta > 0.7 (very bullish) and leg is BUY → BLOCK
        if portfolio_greeks.total_delta > 0.7 and leg.side == "BUY":
            reason = (
                f"Portfolio Delta={portfolio_greeks.total_delta:.4f} high, "
                f"BUY order would increase exposure"
            )
            logger.warning(f"[Gatekeeper] 🚫 Leg {leg.symbol} BLOCKED: {reason}")
            return RiskDecision(decision="BLOCK", reason=reason)
        
        # If portfolio Delta < -0.7 (very bearish) and leg is SELL → BLOCK
        if portfolio_greeks.total_delta < -0.7 and leg.side == "SELL":
            reason = (
                f"Portfolio Delta={portfolio_greeks.total_delta:.4f} low, "
                f"SELL order would increase exposure"
            )
            logger.warning(f"[Gatekeeper] 🚫 Leg {leg.symbol} BLOCKED: {reason}")
            return RiskDecision(decision="BLOCK", reason=reason)
        
        logger.debug(f"[Gatekeeper] ✅ Leg {leg.symbol} ALLOWED")
        return RiskDecision(decision="ALLOW")
    
    async def log_decision(
        self,
        decision_type: str,
        decision: RiskDecision,
        portfolio_greeks: PortfolioGreeks,
        strategy_id: Optional[int] = None,
        leg_id: Optional[int] = None
    ):
        """
        Log risk decision to database for audit.
        
        Non-blocking: If logging fails, we log the error but don't crash.
        The decision has already been made, so logging is secondary.
        
        Args:
            decision_type: "PORTFOLIO" or "LEG"
            decision: RiskDecision instance
            portfolio_greeks: Current portfolio Greeks
            strategy_id: Optional strategy ID (for LEG decisions)
            leg_id: Optional leg ID (for LEG decisions)
        """
        try:
            await self.repo.insert_risk_decision(
                decision_type=decision_type,
                decision=decision.decision,
                strategy_id=strategy_id,
                leg_id=leg_id,
                portfolio_delta=portfolio_greeks.total_delta,
                portfolio_gamma=portfolio_greeks.total_gamma,
                portfolio_vega=portfolio_greeks.total_vega,
                delta_limit=self.limits.max_portfolio_delta,
                gamma_limit=self.limits.max_portfolio_gamma,
                vega_limit=self.limits.max_portfolio_vega,
                reason=decision.reason
            )
        except Exception as e:
            logger.error(f"[Gatekeeper] Failed to log decision: {e}")
            # Continue - decision was already made, logging is secondary
