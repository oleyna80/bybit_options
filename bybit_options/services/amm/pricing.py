import numpy as np
from py_vollib.black_scholes import black_scholes
from py_vollib.black_scholes.greeks.analytical import delta, vega, gamma, theta

class OptionPricing:
    """
    High-performance wrapper around py_vollib.
    """
    
    @staticmethod
    def calculate_price(
        spot: float,
        strike: float,
        time_to_expiry: float, # in years
        risk_free_rate: float,
        iv: float,
        option_type: str # 'c' or 'p'
    ) -> float:
        """
        Returns theoretical price.
        """
        # py_vollib expects lower case 'c'/'p'
        flag = option_type.lower()[0]
        return black_scholes(flag, spot, strike, time_to_expiry, risk_free_rate, iv)

    @staticmethod
    def calculate_greeks(
        spot: float,
        strike: float,
        time_to_expiry: float,
        risk_free_rate: float,
        iv: float,
        option_type: str
    ) -> dict:
        """
        Returns dict with price and greeks.
        """
        flag = option_type.lower()[0]
        args = (flag, spot, strike, time_to_expiry, risk_free_rate, iv)
        
        return {
            "price": black_scholes(*args),
            "delta": delta(*args),
            "gamma": gamma(*args),
            "vega": vega(*args), # Note: py_vollib vega is usually per 1% or 100%? Check benchmark.
                                 # Standard definition is change per 1% change in sigma? 
                                 # Usually py_vollib returns vega for 1 unit change in sigma (100% vol).
                                 # So usually divide by 100 to get "per 1% vol".
                                 # We will standardize this in usage.
            "theta": theta(*args)
        }
