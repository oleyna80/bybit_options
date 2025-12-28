"""
Greeks Calculator using Black-Scholes Model
"""
import numpy as np
from scipy.stats import norm
from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class OptionInput:
    """Input data for Greeks calculation"""
    spot_price: float
    strike: float
    time_to_expiry_days: float
    implied_volatility: float
    option_type: str
    risk_free_rate: float = 0.05


@dataclass
class Greeks:
    """Greeks output"""
    delta: float
    gamma: float
    vega: float
    theta: float
    rho: float

    spot_price: float
    strike: float
    option_type: str
    calculated_at: datetime


class GreeksCalculator:
    """
    Black-Scholes Greeks Calculator

    Note: Designed for standard stablecoin-settled options (USDT/USDC).
    For inverse (coin-margined) options, Delta interpretation differs.

    Assumptions:
    - European-style options (crypto options are actually American, but BS is good approximation)
    - Log-normal price distribution
    - Constant volatility (we use current Mark IV)
    - No dividends (crypto has no dividends)
    - Standard options: P&L in USDT/USDC (not inverse/coin-margined)
    """

    def __init__(self, risk_free_rate: float = 0.05):
        """
        Args:
            risk_free_rate: Annual risk-free rate (default 5% = USDT staking)
        """
        self.risk_free_rate = risk_free_rate

    def calculate_greeks(self, option_input: OptionInput) -> Greeks:
        """
        Calculate all Greeks using Black-Scholes model

        Args:
            option_input: Option parameters

        Returns:
            Greeks object with all calculated values

        Raises:
            ValueError: If IV < 1% or spot price invalid
        """
        S = option_input.spot_price
        K = option_input.strike
        r = option_input.risk_free_rate
        sigma = option_input.implied_volatility
        option_type = option_input.option_type.lower()

        if S <= 0:
            raise ValueError(f"Invalid spot price: {S}")

        if sigma < 0.01:
            raise ValueError(
                f"Invalid or missing IV: {sigma*100:.2f}%. "
                f"Check data quality for strike {K}"
            )

        if option_input.time_to_expiry_days <= 0:
            return self._expired_option_greeks(S, K, option_type)

        T = option_input.time_to_expiry_days / 365.0
        T = max(T, 1e-5)

        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)

        if option_type == 'call':
            delta = norm.cdf(d1)
            theta_component = (
                -(S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T))
                - r * K * np.exp(-r * T) * norm.cdf(d2)
            ) / 365
            rho = K * T * np.exp(-r * T) * norm.cdf(d2) / 100
        elif option_type == 'put':
            delta = norm.cdf(d1) - 1
            theta_component = (
                -(S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T))
                + r * K * np.exp(-r * T) * norm.cdf(-d2)
            ) / 365
            rho = -K * T * np.exp(-r * T) * norm.cdf(-d2) / 100
        else:
            raise ValueError(f"Invalid option_type: {option_type}. Must be 'call' or 'put'")

        gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
        vega = S * norm.pdf(d1) * np.sqrt(T) / 100

        return Greeks(
            delta=delta,
            gamma=gamma,
            vega=vega,
            theta=theta_component,
            rho=rho,
            spot_price=S,
            strike=K,
            option_type=option_type,
            calculated_at=datetime.now(timezone.utc)
        )

    def _expired_option_greeks(self, spot: float, strike: float, option_type: str) -> Greeks:
        """
        Greeks for expired option (all zero except intrinsic delta)
        """
        if option_type == 'call':
            delta = 1.0 if spot > strike else 0.0
        else:
            delta = -1.0 if spot < strike else 0.0

        return Greeks(
            delta=delta,
            gamma=0.0,
            vega=0.0,
            theta=0.0,
            rho=0.0,
            spot_price=spot,
            strike=strike,
            option_type=option_type,
            calculated_at=datetime.now(timezone.utc)
        )

    def calculate_portfolio_greeks(self, positions: List[Dict]) -> Dict[str, float]:
        """
        Calculate aggregate Greeks for entire portfolio

        Args:
            positions: List of position dicts with keys:
                - spot_price: float
                - strike: float
                - time_to_expiry_days: float
                - implied_volatility: float
                - option_type: 'call' or 'put'
                - size: float (quantity, negative for short)
                - multiplier: float (contract multiplier, e.g., 0.01 BTC)

        Returns:
            Dict with aggregated Greeks
        """
        total_delta = 0.0
        total_gamma = 0.0
        total_vega = 0.0
        total_theta = 0.0
        total_rho = 0.0

        for pos in positions:
            option_input = OptionInput(
                spot_price=pos['spot_price'],
                strike=pos['strike'],
                time_to_expiry_days=pos['time_to_expiry_days'],
                implied_volatility=pos['implied_volatility'],
                option_type=pos['option_type'],
                risk_free_rate=self.risk_free_rate
            )

            greeks = self.calculate_greeks(option_input)

            position_weight = pos['size'] * pos.get('multiplier', 1.0)

            total_delta += greeks.delta * position_weight
            total_gamma += greeks.gamma * position_weight
            total_vega += greeks.vega * position_weight
            total_theta += greeks.theta * position_weight
            total_rho += greeks.rho * position_weight

        return {
            'delta': total_delta,
            'gamma': total_gamma,
            'vega': total_vega,
            'theta': total_theta,
            'rho': total_rho,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }


if __name__ == "__main__":
    print("Testing Greeks Calculator...")

    calculator = GreeksCalculator(risk_free_rate=0.05)

    test_call = OptionInput(
        spot_price=87540,
        strike=87500,
        time_to_expiry_days=7,
        implied_volatility=0.53,
        option_type='call'
    )

    greeks_call = calculator.calculate_greeks(test_call)
    print("\nATM Call (7 days, 53% IV):")
    print(f"  Delta: {greeks_call.delta:.4f}")
    print(f"  Gamma: {greeks_call.gamma:.6f}")
    print(f"  Vega:  {greeks_call.vega:.2f}")
    print(f"  Theta: {greeks_call.theta:.2f}")

    test_put = OptionInput(
        spot_price=87540,
        strike=85000,
        time_to_expiry_days=30,
        implied_volatility=0.48,
        option_type='put'
    )

    greeks_put = calculator.calculate_greeks(test_put)
    print("\nOTM Put (30 days, 48% IV):")
    print(f"  Delta: {greeks_put.delta:.4f}")
    print(f"  Gamma: {greeks_put.gamma:.6f}")
    print(f"  Vega:  {greeks_put.vega:.2f}")
    print(f"  Theta: {greeks_put.theta:.2f}")

    portfolio = [
        {
            'spot_price': 87540,
            'strike': 90000,
            'time_to_expiry_days': 7,
            'implied_volatility': 0.52,
            'option_type': 'call',
            'size': -2,
            'multiplier': 0.01
        },
        {
            'spot_price': 87540,
            'strike': 85000,
            'time_to_expiry_days': 7,
            'implied_volatility': 0.48,
            'option_type': 'put',
            'size': -2,
            'multiplier': 0.01
        }
    ]

    portfolio_greeks = calculator.calculate_portfolio_greeks(portfolio)
    print("\nPortfolio Greeks (Short Strangle):")
    print(f"  Delta: {portfolio_greeks['delta']:.4f}")
    print(f"  Gamma: {portfolio_greeks['gamma']:.6f}")
    print(f"  Vega:  {portfolio_greeks['vega']:.2f}")
    print(f"  Theta: {portfolio_greeks['theta']:.2f}")

    print("\n✅ Greeks Calculator test complete!")
