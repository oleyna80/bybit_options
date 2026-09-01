"""
Scenario Simulator for options strategies
Simulates P&L under various price and volatility scenarios
"""

import logging
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from strategy_models import (
    IronCondorLeg,
    ScenarioParameters,
    ScenarioResult,
    GreeksModel,
)

logger = logging.getLogger(__name__)


@dataclass
class SimulationGrid:
    """Grid for scenario simulation"""

    price_grid: np.ndarray  # Underlying prices
    iv_grid: np.ndarray  # Implied volatility changes (%)
    time_grid: np.ndarray  # Time elapsed (days)
    pnl_grid: np.ndarray  # P&L results (price_steps × iv_steps)


class ScenarioSimulator:
    """Simulator for scenario analysis of options strategies"""

    def __init__(self, parameters: Optional[ScenarioParameters] = None):
        """
        Initialize scenario simulator

        Args:
            parameters: Scenario parameters (uses defaults if None)
        """
        self.parameters = parameters or ScenarioParameters()
        self.logger = logging.getLogger(__name__)

    def create_simulation_grid(
        self,
        current_price: float,
        current_iv: float,
        time_horizon_days: Optional[float] = None,
    ) -> SimulationGrid:
        """
        Create simulation grid for scenario analysis

        Args:
            current_price: Current underlying price
            current_iv: Current implied volatility
            time_horizon_days: Time horizon (uses parameters if None)

        Returns:
            SimulationGrid with price, IV, time, and P&L grids
        """
        if time_horizon_days is None:
            time_horizon_days = self.parameters.time_horizon_days

        # Create price grid
        price_min = current_price * (1 + self.parameters.price_range_pct[0] / 100)
        price_max = current_price * (1 + self.parameters.price_range_pct[1] / 100)
        price_grid = np.linspace(price_min, price_max, self.parameters.price_steps)

        # Create IV grid
        iv_min = current_iv * (1 + self.parameters.iv_range_pct[0] / 100)
        iv_max = current_iv * (1 + self.parameters.iv_range_pct[1] / 100)
        iv_grid = np.linspace(iv_min, iv_max, self.parameters.iv_steps)

        # Create time grid (single value for now)
        time_grid = np.array([time_horizon_days])

        # Initialize P&L grid
        pnl_grid = np.zeros((len(price_grid), len(iv_grid)))

        self.logger.info(
            f"Created simulation grid: "
            f"Price={price_min:.0f}-{price_max:.0f} ({len(price_grid)} steps), "
            f"IV={iv_min:.3f}-{iv_max:.3f} ({len(iv_grid)} steps), "
            f"Time={time_horizon_days} days"
        )

        return SimulationGrid(price_grid, iv_grid, time_grid, pnl_grid)

    def calculate_greek_sensitivities(
        self,
        leg: IronCondorLeg,
        price_change_pct: float,
        iv_change_pct: float,
        time_elapsed_days: float,
    ) -> Dict[str, float]:
        """
        Calculate Greek sensitivities for a single leg

        Args:
            leg: IronCondorLeg to analyze
            price_change_pct: Price change percentage
            iv_change_pct: IV change percentage
            time_elapsed_days: Time elapsed in days

        Returns:
            Dictionary with Greek sensitivities and P&L components
        """
        # Convert percentages to absolute changes
        price_change = price_change_pct / 100
        iv_change = iv_change_pct / 100

        # Get current Greeks
        delta = leg.greeks.delta_coin
        gamma = leg.greeks.gamma_coin
        vega = leg.greeks.vega_usd
        theta = leg.greeks.theta_usd

        # Calculate P&L components using Taylor expansion
        # ΔP&L ≈ ΔS * Delta + 0.5 * (ΔS)² * Gamma + Δσ * Vega + Δt * Theta

        # Delta component (linear)
        pnl_delta = price_change * delta

        # Gamma component (quadratic)
        pnl_gamma = 0.5 * (price_change**2) * gamma

        # Vega component
        pnl_vega = iv_change * vega

        # Theta component
        pnl_theta = (time_elapsed_days / 365) * theta  # Convert to annual

        # Total P&L
        pnl_total = pnl_delta + pnl_gamma + pnl_vega + pnl_theta

        # Apply position size and direction
        multiplier = leg.size * leg.direction_multiplier
        pnl_total *= multiplier
        pnl_delta *= multiplier
        pnl_gamma *= multiplier
        pnl_vega *= multiplier
        pnl_theta *= multiplier

        # Calculate Greeks after scenario (simplified)
        # For simplicity, assume Greeks change linearly with price
        delta_after = delta + price_change * gamma
        gamma_after = gamma  # Assume gamma constant (second-order approximation)
        vega_after = vega  # Assume vega constant
        theta_after = theta  # Assume theta constant

        return {
            "pnl_total": pnl_total,
            "pnl_delta": pnl_delta,
            "pnl_gamma": pnl_gamma,
            "pnl_vega": pnl_vega,
            "pnl_theta": pnl_theta,
            "delta_after": delta_after,
            "gamma_after": gamma_after,
            "vega_after": vega_after,
            "theta_after": theta_after,
        }

    def simulate_single_scenario(
        self,
        legs: List[IronCondorLeg],
        underlying_price: float,
        iv_value: float,
        time_elapsed_days: float,
        current_price: float,
        current_iv: float,
    ) -> ScenarioResult:
        """
        Simulate a single scenario

        Args:
            legs: List of IronCondorLeg objects
            underlying_price: Simulated underlying price
            iv_value: Simulated IV value
            time_elapsed_days: Time elapsed in days
            current_price: Current underlying price (for calculating changes)
            current_iv: Current IV (for calculating changes)

        Returns:
            ScenarioResult for this scenario
        """
        # Calculate percentage changes
        price_change_pct = ((underlying_price - current_price) / current_price) * 100
        iv_change_pct = ((iv_value - current_iv) / current_iv) * 100

        # Initialize totals
        total_pnl = 0.0
        total_pnl_delta = 0.0
        total_pnl_gamma = 0.0
        total_pnl_vega = 0.0
        total_pnl_theta = 0.0

        total_delta_after = 0.0
        total_gamma_after = 0.0
        total_vega_after = 0.0
        total_theta_after = 0.0

        # Calculate for each leg
        for leg in legs:
            sensitivities = self.calculate_greek_sensitivities(
                leg, price_change_pct, iv_change_pct, time_elapsed_days
            )

            total_pnl += sensitivities["pnl_total"]
            total_pnl_delta += sensitivities["pnl_delta"]
            total_pnl_gamma += sensitivities["pnl_gamma"]
            total_pnl_vega += sensitivities["pnl_vega"]
            total_pnl_theta += sensitivities["pnl_theta"]

            total_delta_after += (
                sensitivities["delta_after"] * leg.size * leg.direction_multiplier
            )
            total_gamma_after += (
                sensitivities["gamma_after"] * leg.size * leg.direction_multiplier
            )
            total_vega_after += (
                sensitivities["vega_after"] * leg.size * leg.direction_multiplier
            )
            total_theta_after += (
                sensitivities["theta_after"] * leg.size * leg.direction_multiplier
            )

        # Create scenario result
        result = ScenarioResult(
            underlying_price=underlying_price,
            iv_change_pct=iv_change_pct,
            time_elapsed_days=time_elapsed_days,
            pnl_total=total_pnl,
            pnl_delta=total_pnl_delta,
            pnl_gamma=total_pnl_gamma,
            pnl_vega=total_pnl_vega,
            pnl_theta=total_pnl_theta,
            delta_after=total_delta_after,
            gamma_after=total_gamma_after,
            vega_after=total_vega_after,
            theta_after=total_theta_after,
        )

        return result

    def simulate_all_scenarios(
        self,
        legs: List[IronCondorLeg],
        current_price: float,
        current_iv: float,
        time_horizon_days: Optional[float] = None,
    ) -> Tuple[List[ScenarioResult], SimulationGrid]:
        """
        Simulate all scenarios in the grid

        Args:
            legs: List of IronCondorLeg objects
            current_price: Current underlying price
            current_iv: Current implied volatility
            time_horizon_days: Time horizon (uses parameters if None)

        Returns:
            Tuple of (scenario_results, simulation_grid)
        """
        if time_horizon_days is None:
            time_horizon_days = self.parameters.time_horizon_days

        # Create simulation grid
        grid = self.create_simulation_grid(current_price, current_iv, time_horizon_days)

        scenario_results = []

        # Simulate all price × IV combinations
        for i, price in enumerate(grid.price_grid):
            for j, iv in enumerate(grid.iv_grid):
                # Simulate scenario
                result = self.simulate_single_scenario(
                    legs=legs,
                    underlying_price=price,
                    iv_value=iv,
                    time_elapsed_days=time_horizon_days,
                    current_price=current_price,
                    current_iv=current_iv,
                )

                scenario_results.append(result)
                grid.pnl_grid[i, j] = result.pnl_total

        self.logger.info(
            f"Simulated {len(scenario_results)} scenarios: "
            f"Best P&L=${np.max(grid.pnl_grid):.2f}, "
            f"Worst P&L=${np.min(grid.pnl_grid):.2f}"
        )

        return scenario_results, grid

    def find_extreme_scenarios(
        self, scenario_results: List[ScenarioResult]
    ) -> Dict[str, ScenarioResult]:
        """
        Find extreme scenarios (max profit, max loss, etc.)

        Args:
            scenario_results: List of scenario results

        Returns:
            Dictionary with extreme scenarios
        """
        if not scenario_results:
            return {}

        # Find max profit scenario
        max_profit_scenario = max(scenario_results, key=lambda r: r.pnl_total)

        # Find max loss scenario
        max_loss_scenario = min(scenario_results, key=lambda r: r.pnl_total)

        # Find scenarios closest to breakeven
        breakeven_scenarios = sorted(scenario_results, key=lambda r: abs(r.pnl_total))[
            :3
        ]  # Top 3 closest to breakeven

        # Find best IV scenario (highest vega P&L)
        best_iv_scenario = max(scenario_results, key=lambda r: r.pnl_vega)

        # Find worst IV scenario (lowest vega P&L)
        worst_iv_scenario = min(scenario_results, key=lambda r: r.pnl_vega)

        extremes = {
            "max_profit": max_profit_scenario,
            "max_loss": max_loss_scenario,
            "breakeven_candidates": breakeven_scenarios,
            "best_iv": best_iv_scenario,
            "worst_iv": worst_iv_scenario,
        }

        self.logger.info(
            f"Extreme scenarios: "
            f"MaxProfit=${max_profit_scenario.pnl_total:.2f} "
            f"@ ${max_profit_scenario.underlying_price:.0f}, "
            f"MaxLoss=${max_loss_scenario.pnl_total:.2f} "
            f"@ ${max_loss_scenario.underlying_price:.0f}"
        )

        return extremes

    def calculate_breakeven_points(
        self, scenario_results: List[ScenarioResult], current_price: float
    ) -> List[float]:
        """
        Calculate breakeven price points

        Args:
            scenario_results: List of scenario results
            current_price: Current underlying price

        Returns:
            List of breakeven price points
        """
        if not scenario_results:
            return []

        # Group by price and find closest to zero P&L
        price_to_pnl = {}
        for result in scenario_results:
            price = result.underlying_price
            pnl = result.pnl_total

            if price not in price_to_pnl:
                price_to_pnl[price] = []
            price_to_pnl[price].append(pnl)

        # For each price, calculate average P&L
        price_avg_pnl = {price: np.mean(pnls) for price, pnls in price_to_pnl.items()}

        # Find prices where P&L crosses zero
        prices = sorted(price_avg_pnl.keys())
        pnls = [price_avg_pnl[p] for p in prices]

        breakeven_points = []

        # Find zero crossings
        for i in range(len(prices) - 1):
            pnl1 = pnls[i]
            pnl2 = pnls[i + 1]

            # Check if sign changes
            if pnl1 == 0:
                breakeven_points.append(prices[i])
            elif pnl1 * pnl2 < 0:
                # Linear interpolation to find exact breakeven
                price1 = prices[i]
                price2 = prices[i + 1]

                # Interpolate: price = price1 + (0 - pnl1) * (price2 - price1) / (pnl2 - pnl1)
                breakeven_price = price1 + (0 - pnl1) * (price2 - price1) / (
                    pnl2 - pnl1
                )
                breakeven_points.append(breakeven_price)

        # Sort and deduplicate
        breakeven_points = sorted(set(round(p, 2) for p in breakeven_points))

        self.logger.info(
            f"Found {len(breakeven_points)} breakeven points: {breakeven_points}"
        )

        return breakeven_points

    def calculate_risk_metrics(
        self, scenario_results: List[ScenarioResult], current_price: float
    ) -> Dict[str, float]:
        """
        Calculate risk metrics from scenario analysis

        Args:
            scenario_results: List of scenario results
            current_price: Current underlying price

        Returns:
            Dictionary with risk metrics
        """
        if not scenario_results:
            return {}

        # Extract P&L values
        pnls = [r.pnl_total for r in scenario_results]

        # Basic metrics
        max_profit = max(pnls)
        max_loss = min(pnls)
        avg_pnl = np.mean(pnls)
        std_pnl = np.std(pnls)

        # Calculate Value at Risk (VaR) at 95% confidence
        var_95 = np.percentile(pnls, 5)  # 5th percentile (worst 5%)

        # Calculate Expected Shortfall (ES) - average of worst 5%
        worst_5_percent = [p for p in pnls if p <= var_95]
        expected_shortfall = np.mean(worst_5_percent) if worst_5_percent else var_95

        # Calculate probability of profit
        profitable_scenarios = sum(1 for p in pnls if p > 0)
        prob_profit = profitable_scenarios / len(pnls) * 100

        # Calculate expected return
        expected_return = avg_pnl

        # Calculate Sharpe ratio (simplified)
        sharpe_ratio = expected_return / std_pnl if std_pnl > 0 else 0

        metrics = {
            "max_profit": max_profit,
            "max_loss": max_loss,
            "expected_return": expected_return,
            "std_dev": std_pnl,
            "var_95": var_95,
            "expected_shortfall": expected_shortfall,
            "probability_of_profit": prob_profit,
            "sharpe_ratio": sharpe_ratio,
            "total_scenarios": len(scenario_results),
        }

        self.logger.info(
            f"Risk metrics: "
            f"MaxProfit=${max_profit:.2f}, "
            f"MaxLoss=${max_loss:.2f}, "
            f"ProbProfit={prob_profit:.1f}%, "
            f"VaR95=${var_95:.2f}"
        )

        return metrics

    def generate_scenario_summary(
        self,
        legs: List[IronCondorLeg],
        current_price: float,
        current_iv: float,
        time_horizon_days: Optional[float] = None,
    ) -> Dict:
        """
        Generate comprehensive scenario summary

        Args:
            legs: List of IronCondorLeg objects
            current_price: Current underlying price
            current_iv: Current implied volatility
            time_horizon_days: Time horizon (uses parameters if None)

        Returns:
            Dictionary with complete scenario analysis
        """
        # Simulate all scenarios
        scenario_results, grid = self.simulate_all_scenarios(
            legs, current_price, current_iv, time_horizon_days
        )

        # Find extreme scenarios
        extremes = self.find_extreme_scenarios(scenario_results)

        # Calculate breakeven points
        breakeven_points = self.calculate_breakeven_points(
            scenario_results, current_price
        )

        # Calculate risk metrics
        risk_metrics = self.calculate_risk_metrics(scenario_results, current_price)

        # Create summary
        summary = {
            "scenario_count": len(scenario_results),
            "current_price": current_price,
            "current_iv": current_iv,
            "time_horizon_days": time_horizon_days or self.parameters.time_horizon_days,
            "extremes": {
                "max_profit": {
                    "pnl": extremes["max_profit"].pnl_total,
                    "price": extremes["max_profit"].underlying_price,
                    "iv_change": extremes["max_profit"].iv_change_pct,
                },
                "max_loss": {
                    "pnl": extremes["max_loss"].pnl_total,
                    "price": extremes["max_loss"].underlying_price,
                    "iv_change": extremes["max_loss"].iv_change_pct,
                },
            },
            "breakeven_points": breakeven_points,
            "risk_metrics": risk_metrics,
            "grid_shape": grid.pnl_grid.shape,
            "pnl_range": {
                "min": float(np.min(grid.pnl_grid)),
                "max": float(np.max(grid.pnl_grid)),
                "mean": float(np.mean(grid.pnl_grid)),
            },
        }

        self.logger.info(
            f"Scenario summary: "
            f"{summary['scenario_count']} scenarios, "
            f"Breakeven points: {len(breakeven_points)}, "
            f"P&L range: ${summary['pnl_range']['min']:.2f} to ${summary['pnl_range']['max']:.2f}"
        )

        return summary


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Create example legs
    from strategy_models import IronCondorLeg
    from bybit_options.models import PositionSide, OptionType, GreeksModel

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

    # Create simulator
    simulator = ScenarioSimulator()

    # Current market conditions
    current_price = 95000.0
    current_iv = 0.65  # 65%

    # Generate scenario summary
    summary = simulator.generate_scenario_summary(
        example_legs, current_price, current_iv, time_horizon_days=7.0
    )

    print(f"\nScenario Analysis Summary:")
    print(f"  Scenarios simulated: {summary['scenario_count']}")
    print(
        f"  Max Profit: ${summary['extremes']['max_profit']['pnl']:.2f} "
        f"@ ${summary['extremes']['max_profit']['price']:.0f}"
    )
    print(
        f"  Max Loss: ${summary['extremes']['max_loss']['pnl']:.2f} "
        f"@ ${summary['extremes']['max_loss']['price']:.0f}"
    )
    print(f"  Breakeven Points: {summary['breakeven_points']}")
    print(
        f"  Probability of Profit: {summary['risk_metrics']['probability_of_profit']:.1f}%"
    )
    print(f"  VaR 95%: ${summary['risk_metrics']['var_95']:.2f}")
