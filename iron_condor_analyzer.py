#!/usr/bin/env python3
"""
Iron Condor + Vega Hedge Analyzer
Main script for analyzing Iron Condor strategies and calculating optimal vega hedges
"""
import asyncio
import logging
import argparse
from typing import Optional, Dict, List
from pathlib import Path
import sys

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from strategy_models import (
    IronCondorConfig,
    IronCondorLeg,
    AnalysisResult,
    StrategyType,
    HedgeInstrument,
)
from vega_hedge_calculator import VegaHedgeCalculator
from scenario_simulator import ScenarioSimulator, ScenarioParameters
from visualization import StrategyVisualizer
from bybit_options.models import PositionSide, OptionType, GreeksModel

# Try to import Bybit connector for real data
try:
    from bybit_options.services.bybit_connector import BybitConnector

    HAS_BYBIT_CONNECTOR = True
except ImportError:
    HAS_BYBIT_CONNECTOR = False
    print("Warning: bybit_connector not found. Using mock data for demonstration.")

logger = logging.getLogger(__name__)


class IronCondorAnalyzer:
    """Main analyzer for Iron Condor strategies with Vega hedging"""

    def __init__(
        self,
        config: IronCondorConfig,
        use_real_data: bool = False,
        output_dir: str = "./analysis_output",
    ):
        """
        Initialize Iron Condor analyzer

        Args:
            config: Iron Condor configuration
            use_real_data: Whether to use real Bybit data (requires API keys)
            output_dir: Directory for output files
        """
        self.config = config
        self.use_real_data = use_real_data and HAS_BYBIT_CONNECTOR
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.vega_calculator = VegaHedgeCalculator(tolerance=10.0)
        self.scenario_simulator = ScenarioSimulator()
        self.visualizer = StrategyVisualizer(output_dir=str(self.output_dir))

        # Initialize Bybit connector if using real data
        self.bybit_connector = None
        if self.use_real_data:
            try:
                self.bybit_connector = BybitConnector()
                logger.info("Bybit connector initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Bybit connector: {e}")
                self.use_real_data = False

        logger.info(
            f"Iron Condor Analyzer initialized for {config.underlying} {config.expiry}"
        )

    async def fetch_market_data(self) -> Dict:
        """
        Fetch market data for Iron Condor legs

        Returns:
            Dictionary with market data including underlying price and option data
        """
        if not self.use_real_data or not self.bybit_connector:
            logger.info("Using mock market data")
            return self._create_mock_market_data()

        try:
            logger.info("Fetching real market data from Bybit...")

            # Get underlying price
            underlying_price = await self.bybit_connector.get_underlying_price(
                self.config.underlying
            )

            # Get option data for each leg
            option_data = {}

            # Define legs to fetch
            legs_to_fetch = [
                ("long_put", self.config.long_put_strike, "P"),
                ("short_put", self.config.short_put_strike, "P"),
                ("short_call", self.config.short_call_strike, "C"),
                ("long_call", self.config.long_call_strike, "C"),
            ]

            for leg_name, strike, option_type in legs_to_fetch:
                symbol = self._create_option_symbol(strike, option_type)
                try:
                    data = await self.bybit_connector.get_option_data(
                        symbol, self.config.underlying, self.config.expiry
                    )
                    option_data[leg_name] = data
                    logger.debug(f"Fetched data for {leg_name}: {symbol}")
                except Exception as e:
                    logger.warning(f"Failed to fetch data for {leg_name}: {e}")
                    # Use mock data as fallback
                    option_data[leg_name] = self._create_mock_option_data(
                        strike, option_type
                    )

            # Get ATM straddle data for hedging
            atm_strike = round(underlying_price / 1000) * 1000  # Round to nearest 1000
            atm_call_data = await self._get_atm_option_data(atm_strike, "C")
            atm_put_data = await self._get_atm_option_data(atm_strike, "P")

            return {
                "underlying_price": underlying_price,
                "current_iv": 0.65,  # Would get from market data
                "option_data": option_data,
                "atm_strike": atm_strike,
                "atm_call_data": atm_call_data,
                "atm_put_data": atm_put_data,
                "timestamp": asyncio.get_event_loop().time(),
            }

        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
            logger.info("Falling back to mock data")
            return self._create_mock_market_data()

    def _create_mock_market_data(self) -> Dict:
        """Create mock market data for testing"""
        # Mock underlying price
        underlying_price = 95000.0

        # Mock option data for each leg
        option_data = {
            "long_put": {
                "greeks": GreeksModel(
                    delta_coin=-0.18,
                    gamma_coin=0.000032,
                    vega_usd=98.76,
                    theta_usd=-32.45,
                ),
                "mark_price": 1234.56,
            },
            "short_put": {
                "greeks": GreeksModel(
                    delta_coin=0.32,
                    gamma_coin=0.000045,
                    vega_usd=125.45,
                    theta_usd=45.67,
                ),
                "mark_price": 2345.67,
            },
            "short_call": {
                "greeks": GreeksModel(
                    delta_coin=-0.28,
                    gamma_coin=0.000038,
                    vega_usd=112.34,
                    theta_usd=40.12,
                ),
                "mark_price": 3456.78,
            },
            "long_call": {
                "greeks": GreeksModel(
                    delta_coin=0.42,
                    gamma_coin=0.000041,
                    vega_usd=87.65,
                    theta_usd=-38.90,
                ),
                "mark_price": 4567.89,
            },
        }

        # Mock ATM straddle data
        atm_strike = 95000.0
        atm_call_data = {
            "greeks": GreeksModel(
                delta_coin=0.52, gamma_coin=0.000065, vega_usd=145.67, theta_usd=-28.90
            ),
            "mark_price": 5678.90,
        }
        atm_put_data = {
            "greeks": GreeksModel(
                delta_coin=-0.48, gamma_coin=0.000062, vega_usd=143.21, theta_usd=-27.80
            ),
            "mark_price": 4321.09,
        }

        return {
            "underlying_price": underlying_price,
            "current_iv": 0.65,
            "option_data": option_data,
            "atm_strike": atm_strike,
            "atm_call_data": atm_call_data,
            "atm_put_data": atm_put_data,
            "timestamp": asyncio.get_event_loop().time(),
        }

    def _create_option_symbol(self, strike: float, option_type: str) -> str:
        """Create option symbol from strike and option type"""
        return (
            f"{self.config.underlying}-{self.config.expiry}-{strike:.0f}-{option_type}"
        )

    async def _get_atm_option_data(self, strike: float, option_type: str) -> Dict:
        """Get ATM option data (mock or real)"""
        if not self.use_real_data or not self.bybit_connector:
            # Return mock data
            if option_type == "C":
                return {
                    "greeks": GreeksModel(
                        delta_coin=0.52,
                        gamma_coin=0.000065,
                        vega_usd=145.67,
                        theta_usd=-28.90,
                    ),
                    "mark_price": 5678.90,
                }
            else:  # "P"
                return {
                    "greeks": GreeksModel(
                        delta_coin=-0.48,
                        gamma_coin=0.000062,
                        vega_usd=143.21,
                        theta_usd=-27.80,
                    ),
                    "mark_price": 4321.09,
                }

        try:
            symbol = self._create_option_symbol(strike, option_type)
            data = await self.bybit_connector.get_option_data(
                symbol, self.config.underlying, self.config.expiry
            )
            return data
        except Exception as e:
            logger.warning(f"Failed to fetch ATM {option_type} data: {e}")
            # Return mock data as fallback
            return self._get_atm_option_data(
                strike, option_type
            )  # Recursive with use_real_data=False

    def create_iron_condor_legs(self, market_data: Dict) -> List[IronCondorLeg]:
        """
        Create IronCondorLeg objects from market data

        Args:
            market_data: Dictionary with market data

        Returns:
            List of IronCondorLeg objects
        """
        legs = []
        option_data = market_data["option_data"]

        # Define leg configurations
        leg_configs = [
            ("long_put", PositionSide.BUY, OptionType.PUT, self.config.long_put_strike),
            (
                "short_put",
                PositionSide.SELL,
                OptionType.PUT,
                self.config.short_put_strike,
            ),
            (
                "short_call",
                PositionSide.SELL,
                OptionType.CALL,
                self.config.short_call_strike,
            ),
            (
                "long_call",
                PositionSide.BUY,
                OptionType.CALL,
                self.config.long_call_strike,
            ),
        ]

        for leg_name, side, option_type, strike in leg_configs:
            if leg_name in option_data:
                data = option_data[leg_name]
                size = self.config.sizes.get(leg_name, 1.0)

                leg = IronCondorLeg(
                    symbol=self._create_option_symbol(strike, option_type.value),
                    side=side,
                    option_type=option_type,
                    strike=strike,
                    size=size,
                    greeks=data["greeks"],
                    mark_price=data.get("mark_price"),
                )
                legs.append(leg)

                logger.debug(
                    f"Created leg {leg_name}: {leg.symbol}, "
                    f"Size={size}, Vega=${leg.vega_contribution:.2f}"
                )

        return legs

    def create_atm_straddle_instrument(self, market_data: Dict) -> HedgeInstrument:
        """
        Create ATM straddle hedge instrument

        Args:
            market_data: Dictionary with market data

        Returns:
            HedgeInstrument for ATM straddle
        """
        atm_strike = market_data["atm_strike"]
        call_data = market_data["atm_call_data"]
        put_data = market_data["atm_put_data"]

        # Calculate straddle Greeks (sum of call and put)
        straddle_vega = call_data["greeks"].vega_usd + put_data["greeks"].vega_usd
        straddle_delta = call_data["greeks"].delta_coin + put_data["greeks"].delta_coin
        straddle_gamma = call_data["greeks"].gamma_coin + put_data["greeks"].gamma_coin
        straddle_theta = call_data["greeks"].theta_usd + put_data["greeks"].theta_usd

        # Calculate straddle mark price
        straddle_mark_price = None
        if call_data.get("mark_price") and put_data.get("mark_price"):
            straddle_mark_price = call_data["mark_price"] + put_data["mark_price"]

        # Create symbols
        call_symbol = self._create_option_symbol(atm_strike, "C")
        put_symbol = self._create_option_symbol(atm_strike, "P")

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

        logger.info(
            f"Created ATM straddle instrument: "
            f"Strike=${atm_strike:.0f}, Vega=${straddle_vega:.2f}"
        )

        return instrument

    async def run_analysis(self) -> AnalysisResult:
        """
        Run complete Iron Condor analysis

        Returns:
            AnalysisResult with complete analysis
        """
        logger.info("Starting Iron Condor analysis...")

        # 1. Fetch market data
        market_data = await self.fetch_market_data()
        underlying_price = market_data["underlying_price"]
        current_iv = market_data["current_iv"]

        # 2. Create Iron Condor legs
        legs = self.create_iron_condor_legs(market_data)

        # 3. Calculate aggregated Greeks
        net_vega = self.vega_calculator.calculate_net_vega(legs)
        net_delta = sum(leg.delta_contribution for leg in legs)
        net_gamma = sum(leg.gamma_contribution for leg in legs)
        net_theta = sum(leg.theta_contribution for leg in legs)

        # 4. Create ATM straddle hedge instrument
        hedge_instrument = self.create_atm_straddle_instrument(market_data)

        # 5. Generate hedge recommendation
        hedge_recommendation = self.vega_calculator.generate_hedge_recommendation(
            legs, hedge_instrument
        )

        # 6. Run scenario analysis
        scenario_results, grid = self.scenario_simulator.simulate_all_scenarios(
            legs, underlying_price, current_iv
        )

        # 7. Calculate risk metrics
        extremes = self.scenario_simulator.find_extreme_scenarios(scenario_results)
        breakeven_points = self.scenario_simulator.calculate_breakeven_points(
            scenario_results, underlying_price
        )
        risk_metrics = self.scenario_simulator.calculate_risk_metrics(
            scenario_results, underlying_price
        )

        # 8. Generate warnings and recommendations
        warnings = self._generate_warnings(
            net_vega, net_delta, net_gamma, net_theta, legs
        )
        recommendations = self._generate_recommendations(
            hedge_recommendation, net_vega, net_delta
        )

        # 9. Create analysis result
        analysis_result = AnalysisResult(
            strategy_type=StrategyType.IRON_CONDOR,
            config=self.config,
            underlying_price=underlying_price,
            current_iv=current_iv,
            legs=legs,
            net_vega=net_vega,
            net_delta=net_delta,
            net_gamma=net_gamma,
            net_theta=net_theta,
            hedge_recommendation=hedge_recommendation,
            scenario_results=scenario_results,
            max_profit=(
                extremes.get("max_profit").pnl_total
                if extremes.get("max_profit")
                else None
            ),
            max_loss=(
                extremes.get("max_loss").pnl_total if extremes.get("max_loss") else None
            ),
            breakeven_points=breakeven_points,
            warnings=warnings,
            recommendations=recommendations,
        )

        logger.info("Analysis completed successfully")
        return analysis_result

    def _generate_warnings(
        self,
        net_vega: float,
        net_delta: float,
        net_gamma: float,
        net_theta: float,
        legs: List[IronCondorLeg],
    ) -> List[str]:
        """Generate warnings based on risk metrics"""
        warnings = []

        # Vega warnings
        if abs(net_vega) > 100:
            warnings.append(f"High vega exposure: ${net_vega:.2f}")
        elif abs(net_vega) > 50:
            warnings.append(f"Moderate vega exposure: ${net_vega:.2f}")

        # Delta warnings
        if abs(net_delta) > 0.5:
            warnings.append(f"High directional exposure: {net_delta:.4f} BTC")
        elif abs(net_delta) > 0.2:
            warnings.append(f"Moderate directional exposure: {net_delta:.4f} BTC")

        # Gamma warnings
        if net_gamma < -0.0005:
            warnings.append("High negative gamma (vulnerable to large price moves)")
        elif net_gamma < -0.0001:
            warnings.append("Moderate negative gamma")

        # Theta warnings
        if net_theta < -50:
            warnings.append(f"Paying high time decay: ${net_theta:.2f}/day")

        # Position size warnings
        total_size = sum(abs(leg.size) for leg in legs)
        if total_size > 10:
            warnings.append(f"Large total position size: {total_size:.1f} contracts")

        return warnings

    def _generate_recommendations(
        self, hedge_recommendation, net_vega: float, net_delta: float
    ) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []

        # Vega hedge recommendation
        if abs(net_vega) > 20 and hedge_recommendation:
            recommendations.append(
                f"Execute vega hedge: Buy {hedge_recommendation.optimal_quantity:.4f} "
                f"{hedge_recommendation.instrument.instrument_type} contracts"
            )

        # Delta adjustment recommendation
        if abs(net_delta) > 0.3:
            action = "Buy" if net_delta < 0 else "Sell"
            amount = abs(net_delta)
            recommendations.append(
                f"Adjust delta: {action} {amount:.4f} BTC to neutralize directional exposure"
            )

        # General recommendations
        if not recommendations:
            recommendations.append("Position looks well-balanced. Monitor regularly.")

        return recommendations

    async def generate_report(self, analysis_result: AnalysisResult) -> Dict[str, str]:
        """
        Generate comprehensive report with all outputs

        Args:
            analysis_result: Analysis result

        Returns:
            Dictionary with paths to generated files
        """
        output_files = {}

        # 1. Generate text report
        text_report_path = self.visualizer.generate_text_report(analysis_result)
        output_files["text_report"] = text_report_path

        # 2. Export to JSON
        json_path = self.visualizer.export_to_json(analysis_result)
        output_files["json_data"] = json_path

        # 3. Export to CSV
        csv_files = self.visualizer.export_to_csv(analysis_result)
        output_files["csv_files"] = csv_files

        # 4. Generate charts (if scenario results available)
        if analysis_result.scenario_results:
            # P&L curve chart
            pnl_fig = self.visualizer.create_pnl_curve_chart(
                analysis_result.scenario_results, analysis_result.underlying_price
            )
            pnl_chart_path = self.visualizer.save_chart(pnl_fig, "pnl_curve.png")
            output_files["pnl_chart"] = pnl_chart_path

            # Greeks breakdown chart
            greeks_fig = self.visualizer.create_greeks_breakdown_chart(analysis_result)
            greeks_chart_path = self.visualizer.save_chart(
                greeks_fig, "greeks_breakdown.png"
            )
            output_files["greeks_chart"] = greeks_chart_path

        logger.info(f"Generated {len(output_files)} output files")
        return output_files


async def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(
        description="Iron Condor + Vega Hedge Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --strikes 85000 90000 100000 105000 --expiry 19DEC25
  %(prog)s --config config.json --output ./reports
  %(prog)s --real-data --api-key YOUR_KEY --api-secret YOUR_SECRET
        """,
    )

    # Strategy configuration
    parser.add_argument(
        "--underlying", default="BTC", help="Underlying asset (default: BTC)"
    )
    parser.add_argument("--expiry", required=True, help="Expiry date (e.g., 19DEC25)")
    parser.add_argument(
        "--strikes",
        nargs=4,
        type=float,
        metavar=("LP", "SP", "SC", "LC"),
        help="Strike prices: LongPut ShortPut ShortCall LongCall",
    )

    # Data source
    parser.add_argument(
        "--real-data",
        action="store_true",
        help="Use real Bybit data (requires API keys)",
    )
    parser.add_argument("--api-key", help="Bybit API key (for real data)")
    parser.add_argument("--api-secret", help="Bybit API secret (for real data)")

    # Output options
    parser.add_argument(
        "--output",
        default="./analysis_output",
        help="Output directory (default: ./analysis_output)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    # Alternative: config file
    parser.add_argument("--config", help="JSON configuration file")

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    try:
        # Load configuration
        if args.config:
            # Load from JSON file
            import json

            with open(args.config, "r") as f:
                config_data = json.load(f)
            config = IronCondorConfig(**config_data)
        elif args.strikes:
            # Use command-line arguments
            config = IronCondorConfig(
                underlying=args.underlying,
                expiry=args.expiry,
                long_put_strike=args.strikes[0],
                short_put_strike=args.strikes[1],
                short_call_strike=args.strikes[2],
                long_call_strike=args.strikes[3],
            )
        else:
            parser.error("Either --strikes or --config must be provided")

        # Validate configuration
        validation_errors = config.validation_errors
        if validation_errors:
            print("Configuration errors:")
            for error in validation_errors:
                print(f"  - {error}")
            return 1

        print(f"\n{'='*60}")
        print("IRON CONDOR + VEGA HEDGE ANALYZER")
        print(f"{'='*60}")
        print(f"Underlying: {config.underlying}")
        print(f"Expiry: {config.expiry}")
        print(
            f"Strikes: LP=${config.long_put_strike:,.0f}, "
            f"SP=${config.short_put_strike:,.0f}, "
            f"SC=${config.short_call_strike:,.0f}, "
            f"LC=${config.long_call_strike:,.0f}"
        )
        print(f"Data Source: {'Real Bybit Data' if args.real_data else 'Mock Data'}")
        print(f"Output Directory: {args.output}")
        print(f"{'='*60}\n")

        # Create analyzer
        analyzer = IronCondorAnalyzer(
            config=config, use_real_data=args.real_data, output_dir=args.output
        )

        # Run analysis
        print("Running analysis...")
        analysis_result = await analyzer.run_analysis()

        # Generate reports
        print("Generating reports...")
        output_files = await analyzer.generate_report(analysis_result)

        # Print summary
        print(f"\n{'='*60}")
        print("ANALYSIS COMPLETE")
        print(f"{'='*60}")
        print(f"Net Vega: ${analysis_result.net_vega:.2f}")
        print(f"Net Delta: {analysis_result.net_delta:.4f} BTC")
        print(f"Vega Neutral: {'YES' if analysis_result.is_vega_neutral else 'NO'}")

        if analysis_result.hedge_recommendation:
            hedge = analysis_result.hedge_recommendation
            print(f"\nHedge Recommendation:")
            print(f"  Instrument: {hedge.instrument.instrument_type}")
            print(f"  Quantity: {hedge.optimal_quantity:.4f} contracts")
            print(f"  Effectiveness: {hedge.effectiveness:.1f}%")
            if hedge.hedge_cost:
                print(f"  Cost: ${hedge.hedge_cost:.2f}")

        print(f"\nGenerated Files:")
        for file_type, path in output_files.items():
            if isinstance(path, list):
                for p in path:
                    print(f"  - {p}")
            else:
                print(f"  - {path}")

        print(f"\nAnalysis saved to: {args.output}")
        print(f"{'='*60}")

        return 0

    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=args.verbose)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
