"""
Option Solver for Delta Hedger Bot.

Helper logic for selecting option contracts (Expiry, Strike) for hedging strategies.
"""
import locale
from datetime import datetime
from typing import List, Optional, Tuple

class OptionSolver:
    """Utilities for option selection."""
    
    @staticmethod
    def get_target_expiry(expiries: List[str], min_days: int = 2) -> Optional[str]:
        """
        Selects the nearest expiry date that is at least min_days away.
        
        Args:
            expiries: List of strings in "DDMMMYY" format (e.g., "2JAN26").
            min_days: Minimum days until expiry required.
            
        Returns:
            Selected expiry string or None.
        """
        if not expiries:
            return None
            
        # Force 'C' locale for correct month name parsing (JAN vs ЯНВ)
        saved_locale = locale.getlocale(locale.LC_TIME)
        try:
            locale.setlocale(locale.LC_TIME, 'C')
            
            now = datetime.now()
            candidates = []
            
            for exp_str in expiries:
                try:
                    # Parse "2JAN26" -> Day + AbbrMonth + 2-digit Year
                    dt = datetime.strptime(exp_str, "%d%b%y")
                    
                    # Check delta
                    days_diff = (dt - now).days
                    
                    if days_diff >= min_days:
                        candidates.append((days_diff, dt, exp_str))
                except ValueError:
                    # Ignore invalid formats
                    continue
            
            if not candidates:
                return None
                
            # Sort by days difference (ascending)
            candidates.sort(key=lambda x: x[0])
            
            return candidates[0][2]
            
        finally:
            try:
                locale.setlocale(locale.LC_TIME, saved_locale)
            except locale.Error:
                # Fallback if saved locale is invalid/None
                locale.setlocale(locale.LC_TIME, 'C')

    @staticmethod
    def get_atm_strike(current_price: float, step: Optional[int] = None, base_coin: str = "BTC") -> int:
        """
        Calculates At-The-Money strike based on current price.
        
        Args:
            current_price: Current market price of underlying.
            step: Strike price step (default None, auto-detect from base_coin).
            base_coin: Base coin symbol (BTC, ETH) to determine default step.
            
        Returns:
            Nearest strike price.
        """
        if step is None:
            # BTC: 500, ETH: 50
            if base_coin == "ETH":
                step = 50
            else:
                step = 500
                
        return int(round(current_price / step) * step)

    @staticmethod
    def format_symbol(base_coin: str, expiry: str, strike: int, option_type: str) -> str:
        """
        Constructs option symbol string.
        
        Format: BASE-EXPIRY-STRIKE-TYPE (e.g. BTC-29DEC23-40000-C)
        """
        return f"{base_coin}-{expiry}-{strike}-{option_type}"
