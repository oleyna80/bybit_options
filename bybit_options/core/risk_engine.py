"""
Risk Engine - Pure business logic (no API calls)
Calculates Greeks, risk metrics, and aggregations

CRITICAL DESIGN PRINCIPLE:
This module contains ZERO I/O operations. All methods are deterministic:
Same input → Same output. This enables:
- Easy unit testing
- Predictable behavior
- Thread-safe execution
- Clear separation of concerns
"""
from typing import Dict, List, Optional, Set, Tuple
import logging
from collections import defaultdict

from bybit_options.models import (
    PositionModel, PositionType, PositionSide, OptionType,
    GreeksModel, CoinRiskModel, PortfolioRiskModel,
    MarginModel, IVMetrics, GammaRentMetrics
)

logger = logging.getLogger(__name__)


class RiskEngine:
    """
    Pure risk calculation engine
    All methods are static and deterministic
    """
    
    @staticmethod
    def parse_symbol(symbol: str) -> Dict[str, Optional[str]]:
        """
        Parse trading symbol into components
        
        IMPORTANT: Handles USDT-settled options (BTC-19DEC25-100000-C-USDT)
        
        Examples:
            BTC-19DEC25-103000-C-USDT -> {
                'base': 'BTC',
                'series': '19DEC25',
                'strike': '103000',
                'type': 'C',
                'settlement': 'USDT'
            }
            BTCUSDT -> {'base': 'BTC'}
            BTC-PERP -> {'base': 'BTC'}
        """
        symbol = symbol.strip().upper()
        original_symbol = symbol
        
        # Remove known settlement currency suffixes
        # Order matters: Check longer suffixes first
        settlement = None
        for suffix in ["-USDT", "-USDC", "-USD", "USDT", "USDC", "USD"]:
            if symbol.endswith(suffix):
                settlement = suffix.lstrip("-")
                symbol = symbol[:-len(suffix)]
                break
        
        # Remove -PERP suffix for futures
        if symbol.endswith("-PERP"):
            symbol = symbol[:-5]
            return {"base": symbol, "settlement": settlement}
        
        # Check if option (has dashes after removing settlement suffix)
        if "-" in symbol:
            parts = symbol.split("-")
            
            if len(parts) >= 4:
                # Full option format: BTC-19DEC25-103000-C
                return {
                    "base": parts[0],
                    "series": parts[1],
                    "strike": parts[2],
                    "type": parts[3],
                    "settlement": settlement
                }
            elif len(parts) >= 2:
                # Futures or incomplete format: BTC-PERP
                return {
                    "base": parts[0],
                    "settlement": settlement
                }
        
        # Simple format: BTCUSDT -> BTC (after suffix removal)
        return {
            "base": symbol if symbol else original_symbol,
            "settlement": settlement
        }
    
    @staticmethod
    def extract_base_coin(symbol: str) -> str:
        """
        Extract base coin from any symbol format
        
        Examples:
            BTC-19DEC25-100000-C-USDT -> BTC
            BTCUSDT -> BTC
            BTC-PERP -> BTC
        """
        parsed = RiskEngine.parse_symbol(symbol)
        return parsed.get("base", "UNKNOWN")
    
    @staticmethod
    def extract_option_details(
        symbol: str
    ) -> Tuple[Optional[str], Optional[OptionType], Optional[float]]:
        """
        Extract option-specific details
        
        Returns:
            (series, option_type, strike)
        
        Example:
            BTC-19DEC25-100000-C-USDT -> ("19DEC25", OptionType.CALL, 100000.0)
        """
        parsed = RiskEngine.parse_symbol(symbol)
        
        series = parsed.get("series")
        
        # Option type
        opt_type_str = parsed.get("type")
        option_type = None
        if opt_type_str == "C":
            option_type = OptionType.CALL
        elif opt_type_str == "P":
            option_type = OptionType.PUT
        
        # Strike price
        strike = None
        strike_str = parsed.get("strike")
        if strike_str:
            try:
                strike = float(strike_str)
            except ValueError:
                logger.warning(f"Could not parse strike from: {strike_str}")
        
        return series, option_type, strike
    
    @staticmethod
    def calculate_position_greeks(
        raw_position: Dict,
        ticker_data: Optional[Dict],
        pos_type: PositionType
    ) -> GreeksModel:
        """
        Calculate Greeks for a single position
        
        CRITICAL RULES (Options Greeks Math):
        1. Bybit API returns Greeks for the option itself (not position-adjusted)
        2. Call Delta: [0, 1], Put Delta: [-1, 0]
        3. Gamma, Vega: Always positive for the option
        4. Theta: Negative for long positions (time decay)
        5. For Short positions: All Greeks flip sign
        
        Position Greek Formula:
            position_greek = option_greek * size * direction
            where direction = +1 (Buy/Long) or -1 (Sell/Short)
        
        Args:
            raw_position: Raw position data from API
            ticker_data: Market ticker data (contains Greeks for options)
            pos_type: LINEAR or OPTION
        
        Returns:
            Calculated Greeks with proper signs
        """
        symbol = raw_position.get("symbol", "")
        size = float(raw_position.get("size", 0))
        side = raw_position.get("side", "")
        
        # Position sign: +1 for Buy (Long), -1 for Sell (Short)
        sign = 1.0 if side == "Buy" else -1.0
        signed_size = size * sign
        
        # Futures/Perpetuals: Only delta = position size
        if pos_type == PositionType.LINEAR:
            return GreeksModel(delta_coin=signed_size)
        
        # Options: Load Greeks from market data
        if pos_type == PositionType.OPTION:
            if not ticker_data:
                logger.warning(
                    f"⚠️  No ticker data for {symbol} - Greeks unavailable"
                )
                return GreeksModel()
            
            try:
                # Extract raw Greeks from Bybit API
                # These are for the option itself, not position-adjusted
                raw_delta = float(ticker_data.get("delta", 0))
                raw_gamma = float(ticker_data.get("gamma", 0))
                raw_vega = float(ticker_data.get("vega", 0))
                raw_theta = float(ticker_data.get("theta", 0))
                
                # === SANITY CHECKS (Defensive Programming) ===
                # Extract option type for validation
                _, option_type, _ = RiskEngine.extract_option_details(symbol)
                
                # Check 1: CALL options should have positive delta
                if option_type == OptionType.CALL and raw_delta < -0.1:
                    logger.warning(
                        f"🚨 SUSPICIOUS: CALL option {symbol} has negative delta "
                        f"({raw_delta:.4f}). Possible API data issue or extremely "
                        f"deep OTM. Verify data source."
                    )
                
                # Check 2: PUT options should have negative delta
                if option_type == OptionType.PUT and raw_delta > 0.1:
                    logger.warning(
                        f"🚨 SUSPICIOUS: PUT option {symbol} has positive delta "
                        f"({raw_delta:.4f}). Possible API data issue or extremely "
                        f"deep OTM. Verify data source."
                    )
                
                # Check 3: Gamma should always be positive for the option itself
                if raw_gamma < 0:
                    logger.warning(
                        f"🚨 INVALID: {symbol} has negative gamma ({raw_gamma:.6f}). "
                        f"This violates option pricing theory. Data corruption likely."
                    )
                
                # === POSITION GREEKS CALCULATION ===
                # Apply position size and direction
                # 
                # Bybit V5 API Behavior:
                # - Delta: Already signed (Calls +, Puts -)
                # - Gamma: Always positive
                # - Vega: Always positive
                # - Theta: Negative for long positions
                #
                # For Short positions (sign = -1):
                # - All Greeks flip sign
                # - Short Call: Delta becomes negative
                # - Short Put: Delta becomes positive
                # - Short any: Vega negative (profit from IV drop)
                # - Short any: Theta positive (profit from decay)
                
                return GreeksModel(
                    delta_coin=raw_delta * signed_size,
                    gamma_coin=raw_gamma * signed_size,
                    vega_usd=raw_vega * signed_size,
                    theta_usd=raw_theta * signed_size
                )
            
            except (ValueError, KeyError, TypeError) as e:
                logger.error(
                    f"❌ Failed to parse Greeks for {symbol}: {e}. "
                    f"Ticker data: {ticker_data}"
                )
                return GreeksModel()
        
        return GreeksModel()
    
    @staticmethod
    def calculate_iv_metrics(
        position_iv: Optional[float],
        atm_iv: Optional[float]
    ) -> Optional[IVMetrics]:
        """
        Calculate IV comparison metrics
        
        Compares position IV to ATM IV to determine if option is expensive/cheap
        
        Edge Cases Handled:
        - IV <= 0: Deep OTM options with no bids return IV=0, skip calculation
        - None values: Missing data, return None
        """
        # Validation: Check for None
        if position_iv is None or atm_iv is None:
            return None
        
        # Validation: Check for zero or negative IV
        # Deep OTM options often have markIv=0.0 when there's no bid
        if position_iv <= 0.0 or atm_iv <= 0.0:
            logger.debug(
                f"Invalid IV data: position_iv={position_iv:.4f}, "
                f"atm_iv={atm_iv:.4f}. Skipping IV comparison. "
                f"(Likely deep OTM with no liquidity)"
            )
            return None
        
        # Calculate percentage difference
        iv_diff_pct = ((position_iv - atm_iv) / atm_iv) * 100
        
        return IVMetrics(
            position_iv=position_iv,
            atm_iv=atm_iv,
            iv_diff_pct=iv_diff_pct
        )
    
    @staticmethod
    def calculate_gamma_rent(
        theta_usd: float,
        gamma_coin: float
    ) -> Optional[GammaRentMetrics]:
        """
        Calculate Gamma Rent = Theta / Gamma
        
        Physical Interpretation:
        - "How much theta (time decay) am I paying/earning per unit of gamma"
        - Standard metric in volatility trading
        
        Sign Interpretation:
        - Negative (typical): Paying theta to hold gamma
          Example: Long straddle → Gamma Rent = -5000
                   "Paying $5000/day per 1 BTC of gamma"
        
        - Positive (rare): Earning theta while exposed to gamma
          Example: Certain calendar spreads
        
        - More negative = More expensive gamma
        - Less negative = Cheaper gamma
        
        Note: We keep the raw signed value (not absolute) because the sign
        contains important directional information about the trade structure.
        """
        # Avoid division by zero
        if abs(gamma_coin) < 1e-10:
            return GammaRentMetrics(
                theta_usd=theta_usd,
                gamma_coin=gamma_coin,
                gamma_rent=None
            )
        
        gamma_rent = theta_usd / gamma_coin
        
        return GammaRentMetrics(
            theta_usd=theta_usd,
            gamma_coin=gamma_coin,
            gamma_rent=gamma_rent
        )
    
    @staticmethod
    def build_position_model(
        raw_position: Dict,
        greeks: GreeksModel,
        pos_type: PositionType,
        base_coin: str,
        series: Optional[str] = None,
        option_type: Optional[OptionType] = None,
        strike: Optional[float] = None
    ) -> PositionModel:
        """
        Build a complete PositionModel from raw data and calculations
        """
        symbol = raw_position.get("symbol", "")
        side_str = raw_position.get("side", "Buy")
        size = float(raw_position.get("size", 0))
        
        side = (
            PositionSide.BUY if side_str == "Buy"
            else PositionSide.SELL
        )
        
        # Extract pricing
        entry_price = None
        avg_price = raw_position.get("avgPrice")
        if avg_price:
            try:
                entry_price = float(avg_price)
            except (ValueError, TypeError):
                pass
        
        mark_value = None
        pnl = None
        unrealized_pnl = raw_position.get("unrealisedPnl")
        if unrealized_pnl:
            try:
                pnl = float(unrealized_pnl)
            except (ValueError, TypeError):
                pass
        
        return PositionModel(
            symbol=symbol,
            side=side,
            size=size,
            pos_type=pos_type,
            base_coin=base_coin,
            series=series,
            option_type=option_type,
            strike=strike,
            greeks=greeks,
            entry_price=entry_price,
            mark_value=mark_value,
            unrealized_pnl=pnl
        )
    
    @staticmethod
    def aggregate_coin_risk(
        positions: List[PositionModel],
        base_coin: str,
        underlying_price: Optional[float] = None
    ) -> CoinRiskModel:
        """
        Aggregate all positions for a single base coin
        """
        coin_risk = CoinRiskModel(
            base_coin=base_coin,
            underlying_price=underlying_price
        )
        
        for pos in positions:
            if pos.base_coin != base_coin:
                continue
            
            coin_risk.positions.append(pos)
            
            # Aggregate total Greeks
            coin_risk.total_greeks += pos.greeks
            
            # Split by type
            if pos.pos_type == PositionType.LINEAR:
                coin_risk.futures_greeks += pos.greeks
            
            elif pos.pos_type == PositionType.OPTION:
                coin_risk.options_greeks += pos.greeks
                
                # Aggregate by series
                if pos.series:
                    if pos.series not in coin_risk.series_greeks:
                        coin_risk.series_greeks[pos.series] = GreeksModel()
                    
                    coin_risk.series_greeks[pos.series] += pos.greeks
        
        return coin_risk
    
    @staticmethod
    def build_portfolio_risk(
        positions: List[PositionModel],
        margin: Optional[MarginModel],
        underlying_prices: Dict[str, float]
    ) -> PortfolioRiskModel:
        """
        Build complete portfolio risk model
        """
        # Group positions by coin
        by_coin: Dict[str, List[PositionModel]] = defaultdict(list)
        for pos in positions:
            by_coin[pos.base_coin].append(pos)
        
        # Build coin risk models
        coin_risks = {}
        for coin, coin_positions in by_coin.items():
            coin_risks[coin] = RiskEngine.aggregate_coin_risk(
                positions=coin_positions,
                base_coin=coin,
                underlying_price=underlying_prices.get(coin)
            )
        
        # Portfolio-level Greeks (only Vega and Theta are additive)
        total_vega = sum(
            cr.total_greeks.vega_usd
            for cr in coin_risks.values()
        )
        total_theta = sum(
            cr.total_greeks.theta_usd
            for cr in coin_risks.values()
        )
        
        # Generate warnings
        warnings = RiskEngine.generate_warnings(coin_risks, margin)
        
        # Use default margin if None
        if margin is None:
            margin = MarginModel(
                account_type="UNIFIED",
                total_equity=0.0,
                available_balance=0.0,
                used_margin=0.0
            )
        
        return PortfolioRiskModel(
            margin=margin,
            coin_risks=coin_risks,
            total_vega_usd=total_vega,
            total_theta_usd=total_theta,
            warnings=warnings
        )
    
    @staticmethod
    def generate_warnings(
        coin_risks: Dict[str, CoinRiskModel],
        margin: Optional[MarginModel]
    ) -> List[str]:
        """
        Generate risk warnings based on thresholds
        
        Thresholds are calibrated for typical BTC/ETH options trading:
        - Gamma > 0.01: Significant convexity (Delta changes by 1.0 per $100 move)
        - Vega > $1000: Large IV exposure
        - Theta < -$100/day: Significant time decay cost
        - Margin > 60%: Elevated leverage
        - Margin > 80%: Critical leverage
        
        Note: These are static thresholds for MVP. Future enhancement could
        normalize by underlying price for cross-coin comparison.
        """
        warnings = []
        
        # Margin warnings
        if margin and margin.margin_ratio:
            if margin.margin_ratio > 80:
                warnings.append(
                    f"🚨 CRITICAL: Margin ratio {margin.margin_ratio:.1f}% "
                    f"(>80%) - Risk of liquidation!"
                )
            elif margin.margin_ratio > 60:
                warnings.append(
                    f"⚠️  HIGH: Margin ratio {margin.margin_ratio:.1f}% "
                    f"(>60%) - Consider reducing leverage"
                )
        
        # Greeks warnings (per coin)
        for coin, risk in coin_risks.items():
            g = risk.total_greeks
            
            # High Gamma
            # Gamma of 0.01 means Delta changes by 1.0 for every $100 move
            # For BTC at $100k, a 1% move = $1000 = 10 delta change
            if abs(g.gamma_coin) > 0.01:
                warnings.append(
                    f"🚨 HIGH GAMMA ({coin}): "
                    f"Γ={g.gamma_coin:+.6f} - "
                    f"Delta will change rapidly with price movement!"
                )
            
            # High Vega
            if abs(g.vega_usd) > 1000:
                direction = "LONG" if g.vega_usd > 0 else "SHORT"
                warnings.append(
                    f"⚠️  HIGH VEGA ({coin}): "
                    f"${g.vega_usd:+.2f} ({direction}) - "
                    f"Highly exposed to IV changes"
                )
            
            # Significant Theta
            if g.theta_usd < -100:
                warnings.append(
                    f"⚠️  NEGATIVE THETA ({coin}): "
                    f"${g.theta_usd:+.2f}/day - "
                    f"Time decay working against you"
                )
        
        return warnings