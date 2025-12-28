"""
Vega Hedge Calculator for options strategies
Calculates optimal hedge quantities for vega neutral positions
"""

import logging
from typing import Optional, Dict, List, Tuple
from decimal import Decimal

from strategy_models import (
    IronCondorLeg,
    HedgeInstrument,
    HedgeRecommendation,
    GreeksModel,
)
from data_models import PositionSide, OptionType

logger = logging.getLogger(__name__)


class VegaHedgeCalculator:
    """Calculator for vega hedging of options positions"""

    def __init__(self, tolerance: float = 10.0):
        """
        Initialize the vega hedge calculator

        Args:
            tolerance: Tolerance for vega neutrality in USD (default: $10)
        """
        self.tolerance = tolerance
        self.logger = logging.getLogger(__name__)

    def calculate_net_vega(self, legs: List[IronCondorLeg]) -> float:
        """
        Calculate net vega exposure for a list of legs

        Args:
            legs: List of IronCondorLeg objects

        Returns:
            Net vega exposure in USD
        """
        net_vega = 0.0

        for leg in legs:
            leg_vega = leg.vega_contribution
            net_vega += leg_vega

            self.logger.debug(
                f"Leg {leg.symbol} ({leg.side} {leg.option_type}): "
                f"Vega={leg.greeks.vega_usd:.2f}, "
                f"Size={leg.size}, "
                f"Direction={leg.direction_multiplier}, "
                f"Contribution={leg_vega:.2f}"
            )

        self.logger.info(f"Total net vega: ${net_vega:.2f}")
        return net_vega

    def calculate_optimal_hedge_quantity(
        self,
        net_vega: float,
        hedge_instrument: HedgeInstrument,
        target_vega: float = 0.0,
    ) -> float:
        """
        Calculate optimal hedge quantity to achieve target vega

        Args:
            net_vega: Current net vega exposure
            hedge_instrument: Hedge instrument to use
            target_vega: Target vega exposure (default: 0 for vega neutral)

        Returns:
            Optimal quantity of hedge instrument (positive = buy, negative = sell)
        """
        if abs(hedge_instrument.unit_vega) < 1e-10:
            raise ValueError(
                f"Hedge instrument has zero or near-zero vega: "
                f"{hedge_instrument.unit_vega}"
            )

        # Calculate required vega change
        vega_change_needed = target_vega - net_vega

        # Calculate optimal quantity
        optimal_quantity = vega_change_needed / hedge_instrument.unit_vega

        self.logger.info(
            f"Hedge calculation: "
            f"NetVega=${net_vega:.2f}, "
            f"TargetVega=${target_vega:.2f}, "
            f"UnitVega=${hedge_instrument.unit_vega:.2f}, "
            f"OptimalQty={optimal_quantity:.4f}"
        )

        return optimal_quantity

    def calculate_hedge_effectiveness(
        self, net_vega: float, hedge_instrument: HedgeInstrument, hedge_quantity: float
    ) -> float:
        """
        Calculate effectiveness of hedge

        Args:
            net_vega: Current net vega exposure
            hedge_instrument: Hedge instrument used
            hedge_quantity: Quantity of hedge instrument

        Returns:
            Effectiveness percentage (0-100%)
        """
        # Calculate vega after hedge
        hedge_vega_impact = hedge_quantity * hedge_instrument.unit_vega
        vega_after_hedge = net_vega + hedge_vega_impact

        # Calculate effectiveness (how close to zero)
        effectiveness = 100.0 * (1.0 - abs(vega_after_hedge) / max(abs(net_vega), 1.0))

        # Clamp to 0-100%
        effectiveness = max(0.0, min(100.0, effectiveness))

        self.logger.debug(
            f"Hedge effectiveness: "
            f"Before=${net_vega:.2f}, "
            f"Impact=${hedge_vega_impact:.2f}, "
            f"After=${vega_after_hedge:.2f}, "
            f"Effectiveness={effectiveness:.1f}%"
        )

        return effectiveness

    def calculate_hedge_cost(
        self, hedge_instrument: HedgeInstrument, hedge_quantity: float
    ) -> Optional[float]:
        """
        Calculate cost of hedge

        Args:
            hedge_instrument: Hedge instrument
            hedge_quantity: Quantity to hedge

        Returns:
            Cost in USD, or None if mark price not available
        """
        if hedge_instrument.mark_price is None:
            self.logger.warning("Hedge instrument mark price not available")
            return None

        # Cost = quantity * mark price
        # For straddle: cost includes both call and put
        if hedge_instrument.instrument_type == "STRADDLE":
            # Assuming mark_price is for the straddle (call + put)
            cost = abs(hedge_quantity) * hedge_instrument.mark_price
        else:
            cost = abs(hedge_quantity) * hedge_instrument.mark_price

        self.logger.info(f"Hedge cost: ${cost:.2f} for {hedge_quantity:.4f} contracts")
        return cost

    def create_atm_straddle_instrument(
        self,
        underlying: str,
        expiry: str,
        atm_strike: float,
        call_greeks: GreeksModel,
        put_greeks: GreeksModel,
        call_mark_price: Optional[float] = None,
        put_mark_price: Optional[float] = None,
    ) -> HedgeInstrument:
        """
        Create an ATM straddle hedge instrument

        Args:
            underlying: Underlying asset (BTC, ETH, etc)
            expiry: Expiry date (e.g., 19DEC25)
            atm_strike: At-the-money strike price
            call_greeks: Greeks for the call option
            put_greeks: Greeks for the put option
            call_mark_price: Mark price for call (optional)
            put_mark_price: Mark price for put (optional)

        Returns:
            HedgeInstrument for the ATM straddle
        """
        # Calculate straddle Greeks (sum of call and put)
        straddle_vega = call_greeks.vega_usd + put_greeks.vega_usd
        straddle_delta = call_greeks.delta_coin + put_greeks.delta_coin
        straddle_gamma = call_greeks.gamma_coin + put_greeks.gamma_coin
        straddle_theta = call_greeks.theta_usd + put_greeks.theta_usd

        # Calculate straddle mark price
        straddle_mark_price = None
        if call_mark_price is not None and put_mark_price is not None:
            straddle_mark_price = call_mark_price + put_mark_price

        # Create symbols
        call_symbol = f"{underlying}-{expiry}-{atm_strike:.0f}-C"
        put_symbol = f"{underlying}-{expiry}-{atm_strike:.0f}-P"

        instrument = HedgeInstrument(
            instrument_type="STRADDLE",
            call_symbol=call_symbol,
            put_symbol=put_symbol,
            strike=atm_strike,
            unit_vega=straddle_vega,
            unit_delta=straddle_delta,
            unit_gamma=straddle_gamma,
            unit_theta=straddle_theta,
            mark_price=straddle_mark_price,
        )

        self.logger.info(
            f"Created ATM straddle instrument: "
            f"Strike=${atm_strike:.0f}, "
            f"Vega=${straddle_vega:.2f}, "
            f"Delta={straddle_delta:.4f}"
        )

        return instrument

    def generate_hedge_recommendation(
        self,
        legs: List[IronCondorLeg],
        hedge_instrument: HedgeInstrument,
        target_vega: float = 0.0,
    ) -> HedgeRecommendation:
        """
        Generate complete hedge recommendation

        Args:
            legs: List of IronCondorLeg objects
            hedge_instrument: Hedge instrument to use
            target_vega: Target vega exposure (default: 0)

        Returns:
            Complete HedgeRecommendation
        """
        # Calculate current net vega
        net_vega = self.calculate_net_vega(legs)

        # Calculate optimal hedge quantity
        optimal_quantity = self.calculate_optimal_hedge_quantity(
            net_vega, hedge_instrument, target_vega
        )

        # Calculate hedge effectiveness
        effectiveness = self.calculate_hedge_effectiveness(
            net_vega, hedge_instrument, optimal_quantity
        )

        # Calculate hedge cost
        hedge_cost = self.calculate_hedge_cost(hedge_instrument, optimal_quantity)

        # Calculate impact on other Greeks
        delta_impact = optimal_quantity * hedge_instrument.unit_delta
        gamma_impact = optimal_quantity * hedge_instrument.unit_gamma
        vega_impact = optimal_quantity * hedge_instrument.unit_vega
        theta_impact = optimal_quantity * hedge_instrument.unit_theta

        # Create recommendation
        recommendation = HedgeRecommendation(
            instrument=hedge_instrument,
            optimal_quantity=optimal_quantity,
            hedge_cost=hedge_cost,
            effectiveness=effectiveness,
            delta_impact=delta_impact,
            gamma_impact=gamma_impact,
            vega_impact=vega_impact,
            theta_impact=theta_impact,
        )

        # Log recommendation
        self.logger.info(
            f"Hedge recommendation: "
            f"Quantity={optimal_quantity:.4f}, "
            f"Cost=${hedge_cost if hedge_cost else 'N/A'}, "
            f"Effectiveness={effectiveness:.1f}%, "
            f"VegaImpact=${vega_impact:.2f}"
        )

        return recommendation

    def analyze_hedge_alternatives(
        self,
        legs: List[IronCondorLeg],
        hedge_instruments: List[HedgeInstrument],
        target_vega: float = 0.0,
    ) -> List[HedgeRecommendation]:
        """
        Analyze multiple hedge alternatives and rank them

        Args:
            legs: List of IronCondorLeg objects
            hedge_instruments: List of potential hedge instruments
            target_vega: Target vega exposure

        Returns:
            List of HedgeRecommendation sorted by effectiveness
        """
        net_vega = self.calculate_net_vega(legs)

        recommendations = []
        for instrument in hedge_instruments:
            try:
                recommendation = self.generate_hedge_recommendation(
                    legs, instrument, target_vega
                )
                recommendations.append(recommendation)
            except Exception as e:
                self.logger.error(
                    f"Failed to generate hedge recommendation for "
                    f"{instrument.instrument_type}: {e}"
                )

        # Sort by effectiveness (descending) and cost (ascending)
        recommendations.sort(
            key=lambda r: (r.effectiveness, -r.hedge_cost if r.hedge_cost else 0),
            reverse=True,
        )

        return recommendations

    def is_vega_neutral(
        self, legs: List[IronCondorLeg], tolerance: Optional[float] = None
    ) -> bool:
        """
        Check if position is vega neutral within tolerance

        Args:
            legs: List of IronCondorLeg objects
            tolerance: Tolerance in USD (uses instance tolerance if None)

        Returns:
            True if vega neutral within tolerance
        """
        if tolerance is None:
            tolerance = self.tolerance

        net_vega = self.calculate_net_vega(legs)
        is_neutral = abs(net_vega) <= tolerance

        self.logger.debug(
            f"Vega neutrality check: "
            f"NetVega=${net_vega:.2f}, "
            f"Tolerance=${tolerance:.2f}, "
            f"IsNeutral={is_neutral}"
        )

        return is_neutral

    def calculate_required_hedge_for_neutrality(
        self, legs: List[IronCondorLeg], hedge_instrument: HedgeInstrument
    ) -> Dict[str, float]:
        """
        Calculate hedge required to achieve vega neutrality

        Args:
            legs: List of IronCondorLeg objects
            hedge_instrument: Hedge instrument to use

        Returns:
            Dictionary with hedge details
        """
        net_vega = self.calculate_net_vega(legs)

        # Calculate quantity to achieve exact neutrality
        neutral_quantity = -net_vega / hedge_instrument.unit_vega

        # Calculate vega after hedge
        vega_after_hedge = net_vega + (neutral_quantity * hedge_instrument.unit_vega)

        # Calculate effectiveness
        effectiveness = self.calculate_hedge_effectiveness(
            net_vega, hedge_instrument, neutral_quantity
        )

        result = {
            "net_vega_before": net_vega,
            "hedge_quantity": neutral_quantity,
            "vega_after_hedge": vega_after_hedge,
            "effectiveness": effectiveness,
            "is_neutral_after": abs(vega_after_hedge) <= self.tolerance,
        }

        self.logger.info(
            f"Required hedge for neutrality: "
            f"Quantity={neutral_quantity:.4f}, "
            f"VegaBefore=${net_vega:.2f}, "
            f"VegaAfter=${vega_after_hedge:.2f}, "
            f"Effective={effectiveness:.1f}%"
        )

        return result


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Create example legs
    example_legs = [
        IronCondorLeg(
            symbol="BTC-19DEC25-90000-P",
            side=PositionSide.SELL,
            option_type=OptionType.PUT,
            strike=90000.0,
            size=1.0,
            greeks=GreeksModel(
                delta_coin=0.32, gamma_coin=0.000045, vega_usd=125.45, theta_usd=45.67
            ),
        ),
        IronCondorLeg(
            symbol="BTC-19DEC25-85000-P",
            side=PositionSide.BUY,
            option_type=OptionType.PUT,
            strike=85000.0,
            size=1.0,
            greeks=GreeksModel(
                delta_coin=-0.18, gamma_coin=0.000032, vega_usd=98.76, theta_usd=-32.45
            ),
        ),
    ]

    # Create hedge calculator
    calculator = VegaHedgeCalculator(tolerance=10.0)

    # Calculate net vega
    net_vega = calculator.calculate_net_vega(example_legs)
    print(f"Net Vega: ${net_vega:.2f}")

    # Check if vega neutral
    is_neutral = calculator.is_vega_neutral(example_legs)
    print(f"Is Vega Neutral: {is_neutral}")

    # Create example hedge instrument
    hedge_instrument = HedgeInstrument(
        instrument_type="STRADDLE",
        call_symbol="BTC-19DEC25-95000-C",
        put_symbol="BTC-19DEC25-95000-P",
        unit_vega=245.67,
        unit_delta=0.05,
        unit_gamma=0.00012,
        unit_theta=-45.67,
        mark_price=2345.67,
    )

    # Generate hedge recommendation
    recommendation = calculator.generate_hedge_recommendation(
        example_legs, hedge_instrument
    )

    print(f"\nHedge Recommendation:")
    print(f"  Instrument: {recommendation.instrument.instrument_type}")
    print(f"  Optimal Quantity: {recommendation.optimal_quantity:.4f}")
    print(f"  Hedge Cost: ${recommendation.hedge_cost:.2f}")
    print(f"  Effectiveness: {recommendation.effectiveness:.1f}%")
    print(f"  Vega Impact: ${recommendation.vega_impact:.2f}")
