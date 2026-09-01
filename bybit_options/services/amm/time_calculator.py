"""
Time-to-Expiry Calculator for AMM Robot

Parses Bybit option symbols and calculates time to expiry in years.
"""
from datetime import datetime
from typing import Optional
from loguru import logger

from bybit_options.core.risk_engine import RiskEngine


def calculate_time_to_expiry(symbol: str) -> float:
    """
    Parse symbol and calculate time to expiry in years.
    
    Bybit expiry format: DDMMMYY (e.g., 26JUN26)
    
    Args:
        symbol: Option symbol (e.g., "BTC-26JUN26-100000-C")
        
    Returns:
        Time to expiry in years (e.g., 0.42 for ~5 months)
        
    Raises:
        ValueError: If symbol format is invalid or no series found
        
    Examples:
        >>> calculate_time_to_expiry("BTC-26JUN26-100000-C")
        0.42  # Approximate for ~5 months
        
        >>> calculate_time_to_expiry("BTC-31DEC26-110000-P")
        0.93  # Approximate for ~11 months
    """
    # Parse symbol using existing RiskEngine
    parsed = RiskEngine.parse_symbol(symbol)
    series = parsed.get("series")
    
    if not series:
        raise ValueError(f"No series found in symbol: {symbol}")
    
    try:
        # Parse Bybit date format: DDMMMYY (e.g., 26JUN26)
        expiry_date = datetime.strptime(series, "%d%b%y")
    except ValueError as e:
        raise ValueError(f"Invalid expiry format '{series}' in symbol {symbol}: {e}")
    
    # Calculate days to expiry
    now = datetime.utcnow()
    days_to_expiry = (expiry_date - now).days
    
    # Avoid division by zero for expired/near-expiry options
    # Minimum 0.001 years (~8.76 hours) to prevent pricing errors
    T = max(days_to_expiry / 365.0, 0.001)
    
    logger.debug(f"Symbol {symbol}: Expiry={series}, T={T:.4f} years ({days_to_expiry} days)")
    
    return T
