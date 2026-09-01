"""
Alligator State Detector for Technical Intelligence.

Determines Alligator indicator state and trend direction across multiple timeframes.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional

from strategy.indicators.alligator import AlligatorIndicator


class AlligatorState(str, Enum):
    """Alligator indicator states based on Williams' Chaos Theory."""
    SLEEPING = "SLEEPING"        # Lines intertwined, no trend
    AWAKENING = "AWAKENING"      # Lines starting to diverge
    EATING_UP = "EATING_UP"      # Bullish trend, lines spread upward
    EATING_DOWN = "EATING_DOWN"  # Bearish trend, lines spread downward
    SATED = "SATED"              # Lines converging, trend ending


@dataclass
class AlligatorContext:
    """Complete Alligator context for a given timeframe."""
    jaw: Optional[float]
    teeth: Optional[float]
    lips: Optional[float]
    state: AlligatorState
    spread_pct: float  # Distance between jaw and lips in %
    trend_direction: Optional[str]  # "UP" | "DOWN" | None


class AlligatorStateDetector:
    """
    Determines Alligator state and trend direction.
    
    States:
    - SLEEPING (<0.3% spread): No clear trend, avoid directional trades
    - AWAKENING (0.3-0.8% spread): Trend forming
    - EATING (>0.8% spread, expanding): Active trend, follow it
    - SATED (>0.8% spread, contracting): Trend exhaustion, prepare exit
    """
    
    def __init__(self, indicator: Optional[AlligatorIndicator] = None):
        self.indicator = indicator or AlligatorIndicator()
    
    def detect(self, candles: List[Dict]) -> AlligatorContext:
        """
        Detect Alligator state from candle data.
        
        Args:
            candles: List of OHLCV candles
            
        Returns:
            AlligatorContext with state and direction
        """
        if len(candles) < 2:
            return AlligatorContext(
                jaw=None, teeth=None, lips=None,
                state=AlligatorState.SLEEPING,
                spread_pct=0.0, trend_direction=None
            )
        
        # Get current and previous Alligator values
        current = self.indicator.calculate(candles)
        previous = self.indicator.calculate(candles[:-1])
        
        jaw, teeth, lips = current["jaw"], current["teeth"], current["lips"]
        
        # If any line is None, consider it sleeping
        if None in (jaw, teeth, lips):
            return AlligatorContext(
                jaw=jaw, teeth=teeth, lips=lips,
                state=AlligatorState.SLEEPING,
                spread_pct=0.0, trend_direction=None
            )
        
        # Calculate spread percentage
        price = float(candles[-1]["close"])
        spread = abs(jaw - lips)
        spread_pct = (spread / price) * 100
        
        # Determine trend direction based on line order
        # Bullish: Lips > Teeth > Jaw
        # Bearish: Lips < Teeth < Jaw
        is_bullish_order = lips > teeth > jaw
        is_bearish_order = lips < teeth < jaw
        
        if is_bullish_order:
            direction = "UP"
        elif is_bearish_order:
            direction = "DOWN"
        else:
            direction = None
        
        # Determine state based on spread and convergence/divergence
        if spread_pct < 0.3:
            state = AlligatorState.SLEEPING
            direction = None
        elif spread_pct < 0.8:
            state = AlligatorState.AWAKENING
        else:
            # Check if lines are converging or diverging
            prev_jaw = previous.get("jaw")
            prev_lips = previous.get("lips")
            
            if prev_jaw is not None and prev_lips is not None:
                prev_spread = abs(prev_jaw - prev_lips)
                is_converging = spread < prev_spread
                
                if is_converging:
                    state = AlligatorState.SATED
                else:
                    state = AlligatorState.EATING_UP if direction == "UP" else AlligatorState.EATING_DOWN
            else:
                # Can't determine convergence, default to eating if spread is large
                state = AlligatorState.EATING_UP if direction == "UP" else AlligatorState.EATING_DOWN
        
        return AlligatorContext(
            jaw=float(jaw),
            teeth=float(teeth),
            lips=float(lips),
            state=state,
            spread_pct=round(spread_pct, 4),
            trend_direction=direction
        )
