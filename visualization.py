"""
Visualization module for options strategy analysis
Generates charts and reports for Iron Condor + Vega Hedge analysis
"""

import logging
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import json
import csv
from datetime import datetime

from strategy_models import AnalysisResult, ScenarioResult, SimulationGrid, ExportFormat
from scenario_simulator import ScenarioSimulator

logger = logging.getLogger(__name__)


class StrategyVisualizer:
    """Visualizer for options strategy analysis results"""

    def __init__(self, output_dir: str = "./output"):
        """
        Initialize visualizer

        Args:
            output_dir: Directory to save output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)

        # Configure matplotlib style
        plt.style.use("seaborn-v0_8-darkgrid")
        self.colors = {
            "primary": "#1f77b4",
            "secondary": "#ff7f0e",
            "success": "#2ca02c",
            "danger": "#d62728",
            "neutral": "#7f7f7f",
        }

    def create_pnl_curve_chart(
        self,
        scenario_results: List[ScenarioResult],
        current_price: float,
        title: str = "P&L Curve - Iron Condor",
        include_vega_neutral: bool = False,
        vega_neutral_results: Optional[List[ScenarioResult]] = None,
    ) -> plt.Figure:
        """
        Create P&L curve chart (price vs P&L)

        Args:
            scenario_results: List of scenario results
            current_price: Current underlying price
            title: Chart title
            include_vega_neutral: Whether to include vega-neutral comparison
            vega_neutral_results: Vega-neutral scenario results

        Returns:
            Matplotlib Figure object
        """
        fig, ax = plt.subplots(figsize=(12, 6))

        # Group results by price and calculate average P&L
        price_to_pnl = {}
        for result in scenario_results:
            price = result.underlying_price
            if price not in price_to_pnl:
                price_to_pnl[price] = []
            price_to_pnl[price].append(result.pnl_total)

        prices = sorted(price_to_pnl.keys())
        avg_pnls = [np.mean(price_to_pnl[p]) for p in prices]

        # Plot current Iron Condor P&L curve
        ax.plot(
            prices,
            avg_pnls,
            label="Current Iron Condor",
            color=self.colors["primary"],
            linewidth=2,
        )

        # Plot vega-neutral P&L curve if requested
        if include_vega_neutral and vega_neutral_results:
            vn_price_to_pnl = {}
            for result in vega_neutral_results:
                price = result.underlying_price
                if price not in vn_price_to_pnl:
                    vn_price_to_pnl[price] = []
                vn_price_to_pnl[price].append(result.pnl_total)

            vn_prices = sorted(vn_price_to_pnl.keys())
            vn_avg_pnls = [np.mean(vn_price_to_pnl[p]) for p in vn_prices]

            ax.plot(
                vn_prices,
                vn_avg_pnls,
                label="Vega-Neutral Portfolio",
                color=self.colors["secondary"],
                linewidth=2,
                linestyle="--",
            )

        # Add current price line
        ax.axvline(
            x=current_price,
            color="black",
            linestyle=":",
            alpha=0.7,
            label=f"Current Price (${current_price:,.0f})",
        )

        # Add zero P&L line
        ax.axhline(y=0, color="gray", linestyle="-", alpha=0.5)

        # Find and mark breakeven points
        breakeven_points = []
        for i in range(len(prices) - 1):
            pnl1 = avg_pnls[i]
            pnl2 = avg_pnls[i + 1]
            if pnl1 == 0:
                breakeven_points.append(prices[i])
            elif pnl1 * pnl2 < 0:
                # Linear interpolation
                price1 = prices[i]
                price2 = prices[i + 1]
                breakeven_price = price1 + (0 - pnl1) * (price2 - price1) / (
                    pnl2 - pnl1
                )
                breakeven_points.append(breakeven_price)

        for be_price in breakeven_points:
            ax.axvline(
                x=be_price, color=self.colors["neutral"], linestyle="--", alpha=0.5
            )
            ax.text(
                be_price,
                ax.get_ylim()[0] * 0.9,
                f"${be_price:,.0f}",
                rotation=90,
                ha="center",
                va="bottom",
                color=self.colors["neutral"],
            )

        # Customize chart
        ax.set_xlabel("Underlying Price ($)", fontsize=12)
        ax.set_ylabel("P&L ($)", fontsize=12)
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.grid(True, alpha=0.3)
        ax.legend(loc="best")

        # Format axes
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x:,.0f}"))
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x:,.0f}"))

        # Add summary text
        max_profit = max(avg_pnls)
        max_loss = min(avg_pnls)
        summary_text = f"Max Profit: ${max_profit:,.2f}\nMax Loss: ${max_loss:,.2f}"
        ax.text(
            0.02,
            0.98,
            summary_text,
            transform=ax.transAxes,
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
        )

        plt.tight_layout()
        return fig

    def create_heatmap_chart(
        self,
        grid: SimulationGrid,
        current_price: float,
        current_iv: float,
        title: str = "P&L Heatmap - Price vs IV",
    ) -> plt.Figure:
        """
        Create P&L heatmap (price vs IV)

        Args:
            grid: SimulationGrid with P&L data
            current_price: Current underlying price
            current_iv: Current implied volatility
            title: Chart title

        Returns:
            Matplotlib Figure object
        """
        fig, ax = plt.subplots(figsize=(12, 8))

        # Create heatmap
        im = ax.imshow(
            grid.pnl_grid.T,
            aspect="auto",
            origin="lower",
            cmap="RdYlGn",
            extent=[
                grid.price_grid[0],
                grid.price_grid[-1],
                grid.iv_grid[0],
                grid.iv_grid[-1],
            ],
        )

        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label("P&L ($)", fontsize=12)

        # Add current price/IV point
        ax.scatter(
            [current_price],
            [current_iv],
            color="black",
            s=100,
            marker="o",
            label=f"Current (${current_price:,.0f}, IV={current_iv:.1%})",
            edgecolors="white",
            linewidth=2,
        )

        # Add contour lines
        contour_levels = np.linspace(np.min(grid.pnl_grid), np.max(grid.pnl_grid), 10)
        contour = ax.contour(
            grid.price_grid,
            grid.iv_grid,
            grid.pnl_grid.T,
            levels=contour_levels,
            colors="black",
            alpha=0.5,
            linewidths=0.5,
        )
        ax.clabel(contour, inline=True, fontsize=8, fmt="$%.0f")

        # Customize chart
        ax.set_xlabel("Underlying Price ($)", fontsize=12)
        ax.set_ylabel("Implied Volatility", fontsize=12)
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.legend(loc="upper right")

        # Format axes
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x:,.0f}"))
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{x:.1%}"))

        # Add grid
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        return fig

    def create_greeks_breakdown_chart(
        self, analysis_result: AnalysisResult, title: str = "Greeks Breakdown"
    ) -> plt.Figure:
        """
        Create Greeks breakdown chart

        Args:
            analysis_result: Analysis result with Greeks data
            title: Chart title

        Returns:
            Matplotlib Figure object
        """
        # Extract Greeks data
        greeks_data = {
            "Delta": analysis_result.net_delta,
            "Gamma": analysis_result.net_gamma * 1000,  # Scale for visibility
            "Vega": analysis_result.net_vega / 100,  # Scale for visibility
            "Theta": analysis_result.net_theta,
        }

        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        # Bar chart for Greek values
        colors = []
        for greek, value in greeks_data.items():
            if value > 0:
                colors.append(self.colors["success"])
            elif value < 0:
                colors.append(self.colors["danger"])
            else:
                colors.append(self.colors["neutral"])

        bars = ax1.bar(greeks_data.keys(), greeks_data.values(), color=colors)
        ax1.axhline(y=0, color="black", linewidth=0.8)
        ax1.set_ylabel("Value", fontsize=12)
        ax1.set_title("Greek Values", fontsize=13, fontweight="bold")
        ax1.grid(True, alpha=0.3, axis="y")

        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax1.text(
                bar.get_x() + bar.get_width() / 2.0,
                height + (0.01 if height >= 0 else -0.01),
                f"{height:+.2f}",
                ha="center",
                va="bottom" if height >= 0 else "top",
                fontsize=10,
            )

        # Pie chart for P&L contribution (if scenario results available)
        if analysis_result.scenario_results:
            # Calculate average P&L contributions
            avg_delta_pnl = np.mean(
                [r.pnl_delta for r in analysis_result.scenario_results]
            )
            avg_gamma_pnl = np.mean(
                [r.pnl_gamma for r in analysis_result.scenario_results]
            )
            avg_vega_pnl = np.mean(
                [r.pnl_vega for r in analysis_result.scenario_results]
            )
            avg_theta_pnl = np.mean(
                [r.pnl_theta for r in analysis_result.scenario_results]
            )

            contributions = {
                "Delta": abs(avg_delta_pnl),
                "Gamma": abs(avg_gamma_pnl),
                "Vega": abs(avg_vega_pnl),
                "Theta": abs(avg_theta_pnl),
            }

            # Filter out zero contributions
            contributions = {k: v for k, v in contributions.items() if v > 0}

            if contributions:
                labels = list(contributions.keys())
                sizes = list(contributions.values())
                colors = [
                    self.colors["primary"],
                    self.colors["secondary"],
                    self.colors["success"],
                    self.colors["danger"],
                ][: len(labels)]

                ax2.pie(
                    sizes,
                    labels=labels,
                    colors=colors,
                    autopct="%1.1f%%",
                    startangle=90,
                )
                ax2.set_title(
                    "P&L Contribution by Greek", fontsize=13, fontweight="bold"
                )
            else:
                ax2.text(
                    0.5,
                    0.5,
                    "No P&L data available",
                    ha="center",
                    va="center",
                    transform=ax2.transAxes,
                )
                ax2.set_title(
                    "P&L Contribution (No Data)", fontsize=13, fontweight="bold"
                )
        else:
            ax2.text(
                0.5,
                0.5,
                "No scenario data available",
                ha="center",
                va="center",
                transform=ax2.transAxes,
            )
            ax2.set_title("P&L Contribution (No Data)", fontsize=13, fontweight="bold")

        fig.suptitle(title, fontsize=14, fontweight="bold")
        plt.tight_layout()
        return fig

    def create_risk_summary_chart(
        self, risk_metrics: Dict[str, float], title: str = "Risk Metrics Summary"
    ) -> plt.Figure:
        """
        Create risk metrics summary chart

        Args:
            risk_metrics: Dictionary with risk metrics
            title: Chart title

        Returns:
            Matplotlib Figure object
        """
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        axes = axes.flatten()

        # 1. Profit/Loss Distribution
        if "max_profit" in risk_metrics and "max_loss" in risk_metrics:
            ax1 = axes[0]
            profit_loss_data = [risk_metrics["max_profit"], risk_metrics["max_loss"]]
            colors = [self.colors["success"], self.colors["danger"]]
            bars = ax1.bar(["Max Profit", "Max Loss"], profit_loss_data, color=colors)
            ax1.set_ylabel("Amount ($)", fontsize=11)
            ax1.set_title("Profit/Loss Extremes", fontsize=12, fontweight="bold")
            ax1.grid(True, alpha=0.3, axis="y")

            for bar in bars:
                height = bar.get_height()
                ax1.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height + (10 if height >= 0 else -10),
                    f"${height:,.0f}",
                    ha="center",
                    va="bottom" if height >= 0 else "top",
                    fontsize=10,
                )

        # 2. Probability Metrics
        ax2 = axes[1]
        if "probability_of_profit" in risk_metrics:
            prob_data = [
                risk_metrics["probability_of_profit"],
                100 - risk_metrics["probability_of_profit"],
            ]
            ax2.pie(
                prob_data,
                labels=["Profit", "Loss"],
                colors=[self.colors["success"], self.colors["danger"]],
                autopct="%1.1f%%",
            )
            ax2.set_title("Probability of Profit/Loss", fontsize=12, fontweight="bold")

        # 3. Risk Measures
        ax3 = axes[2]
        risk_measures = {}
        if "var_95" in risk_metrics:
            risk_measures["VaR 95%"] = risk_metrics["var_95"]
        if "expected_shortfall" in risk_metrics:
            risk_measures["Expected Shortfall"] = risk_metrics["expected_shortfall"]
        if "std_dev" in risk_metrics:
            risk_measures["Std Dev"] = risk_metrics["std_dev"]

        if risk_measures:
            x_pos = range(len(risk_measures))
            bars = ax3.bar(x_pos, risk_measures.values(), color=self.colors["primary"])
            ax3.set_xticks(x_pos)
            ax3.set_xticklabels(risk_measures.keys(), rotation=45, ha="right")
            ax3.set_ylabel("Amount ($)", fontsize=11)
            ax3.set_title("Risk Measures", fontsize=12, fontweight="bold")
            ax3.grid(True, alpha=0.3, axis="y")

            for bar, value in zip(bars, risk_measures.values()):
                ax3.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    bar.get_height() + 5,
                    f"${value:,.0f}",
                    ha="center",
                    va="bottom",
                    fontsize=9,
                )

        # 4. Performance Metrics
        ax4 = axes[3]
        perf_metrics = {}
        if "expected_return" in risk_metrics:
            perf_metrics["Expected Return"] = risk_metrics["expected_return"]
        if "sharpe_ratio" in risk_metrics:
            perf_metrics["Sharpe Ratio"] = risk_metrics["sharpe_ratio"]

        if perf_metrics:
            x_pos = range(len(perf_metrics))
            colors = [
                self.colors["success"] if v > 0 else self.colors["danger"]
                for v in perf_metrics.values()
            ]
            bars = ax4.bar(x_pos, perf_metrics.values(), color=colors)
            ax4.set_xticks(x_pos)
            ax4.set_xticklabels(perf_metrics.keys(), rotation=45, ha="right")
            ax4.set_title("Performance Metrics", fontsize=12, fontweight="bold")
            ax4.grid(True, alpha=0.3, axis="y")

            for bar, value in zip(bars, perf_metrics.values()):
                ax4.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    bar.get_height() + (0.1 if value >= 0 else -0.1),
                    f"{value:+.2f}",
                    ha="center",
                    va="bottom" if value >= 0 else "top",
                    fontsize=9,
                )

        fig.suptitle(title, fontsize=14, fontweight="bold")
        plt.tight_layout()
        return fig

    def export_to_json(
        self, analysis_result: AnalysisResult, filename: str = "analysis_result.json"
    ) -> str:
        """
        Export analysis result to JSON file

        Args:
            analysis_result: Analysis result to export
            filename: Output filename

        Returns:
            Path to saved file
        """
        filepath = self.output_dir / filename

        # Convert to dict (Pydantic models have .dict() method)
        result_dict = analysis_result.dict()

        # Convert datetime to string
        if "timestamp" in result_dict:
            result_dict["timestamp"] = result_dict["timestamp"].isoformat()

        # Save to file
        with open(filepath, "w") as f:
            json.dump(result_dict, f, indent=2, default=str)

        self.logger.info(f"Exported analysis result to {filepath}")
        return str(filepath)

    def export_to_csv(
        self, analysis_result: AnalysisResult, filename: str = "analysis_result.csv"
    ) -> str:
        """
        Export analysis result to CSV files

        Args:
            analysis_result: Analysis result to export
            filename: Base filename (will create multiple files)

        Returns:
            List of paths to saved files
        """
        files_created = []

        # 1. Export legs data
        legs_filename = filename.replace(".csv", "_legs.csv")
        legs_filepath = self.output_dir / legs_filename

        if analysis_result.legs:
            with open(legs_filepath, "w", newline="") as f:
                writer = csv.writer(f)
                # Write header
                writer.writerow(
                    [
                        "symbol",
                        "side",
                        "option_type",
                        "strike",
                        "size",
                        "delta",
                        "gamma",
                        "vega",
                        "theta",
                        "delta_contribution",
                        "gamma_contribution",
                        "vega_contribution",
                        "theta_contribution",
                    ]
                )

                # Write data
                for leg in analysis_result.legs:
                    writer.writerow(
                        [
                            leg.symbol,
                            leg.side.value,
                            leg.option_type.value,
                            leg.strike,
                            leg.size,
                            leg.greeks.delta_coin,
                            leg.greeks.gamma_coin,
                            leg.greeks.vega_usd,
                            leg.greeks.theta_usd,
                            leg.delta_contribution,
                            leg.gamma_contribution,
                            leg.vega_contribution,
                            leg.theta_contribution,
                        ]
                    )

            files_created.append(str(legs_filepath))

        # 2. Export scenario results
        if analysis_result.scenario_results:
            scenarios_filename = filename.replace(".csv", "_scenarios.csv")
            scenarios_filepath = self.output_dir / scenarios_filename

            with open(scenarios_filepath, "w", newline="") as f:
                writer = csv.writer(f)
                # Write header
                writer.writerow(
                    [
                        "underlying_price",
                        "iv_change_pct",
                        "time_elapsed_days",
                        "pnl_total",
                        "pnl_delta",
                        "pnl_gamma",
                        "pnl_vega",
                        "pnl_theta",
                        "delta_after",
                        "gamma_after",
                        "vega_after",
                        "theta_after",
                    ]
                )

                # Write data
                for scenario in analysis_result.scenario_results:
                    writer.writerow(
                        [
                            scenario.underlying_price,
                            scenario.iv_change_pct,
                            scenario.time_elapsed_days,
                            scenario.pnl_total,
                            scenario.pnl_delta,
                            scenario.pnl_gamma,
                            scenario.pnl_vega,
                            scenario.pnl_theta,
                            scenario.delta_after,
                            scenario.gamma_after,
                            scenario.vega_after,
                            scenario.theta_after,
                        ]
                    )

            files_created.append(str(scenarios_filepath))

        # 3. Export summary
        summary_filename = filename.replace(".csv", "_summary.csv")
        summary_filepath = self.output_dir / summary_filename

        with open(summary_filepath, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["metric", "value"])

            summary_data = [
                ("timestamp", analysis_result.timestamp.isoformat()),
                ("strategy_type", analysis_result.strategy_type.value),
                ("underlying_price", analysis_result.underlying_price),
                ("current_iv", analysis_result.current_iv),
                ("net_delta", analysis_result.net_delta),
                ("net_gamma", analysis_result.net_gamma),
                ("net_vega", analysis_result.net_vega),
                ("net_theta", analysis_result.net_theta),
                ("max_profit", analysis_result.max_profit or 0),
                ("max_loss", analysis_result.max_loss or 0),
            ]

            for metric, value in summary_data:
                writer.writerow([metric, value])

        files_created.append(str(summary_filepath))

        self.logger.info(f"Exported {len(files_created)} CSV files")
        return files_created

    def generate_text_report(
        self, analysis_result: AnalysisResult, filename: str = "analysis_report.txt"
    ) -> str:
        """
        Generate text report

        Args:
            analysis_result: Analysis result
            filename: Output filename

        Returns:
            Path to saved file
        """
        filepath = self.output_dir / filename

        with open(filepath, "w") as f:
            f.write("=" * 70 + "\n")
            f.write("IRON CONDOR + VEGA HEDGE ANALYSIS REPORT\n")
            f.write("=" * 70 + "\n\n")

            f.write(
                f"Analysis Time: {analysis_result.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
            )
            f.write(f"Strategy Type: {analysis_result.strategy_type.value}\n")
            f.write(f"Underlying: BTC @ ${analysis_result.underlying_price:,.2f}\n")
            f.write(f"Current IV: {analysis_result.current_iv:.1%}\n\n")

            f.write("1. IRON CONDOR POSITION\n")
            f.write("-" * 40 + "\n")
            for i, leg in enumerate(analysis_result.legs, 1):
                f.write(
                    f"Leg {i}: {leg.symbol} ({leg.side.value} {leg.option_type.value})\n"
                )
                f.write(
                    f"       Strike: ${leg.strike:,.0f}, Size: {leg.size:.1f} contracts\n"
                )
                f.write(
                    f"       Greeks: Delta={leg.greeks.delta_coin:.4f}, "
                    f"Gamma={leg.greeks.gamma_coin:.6f}, "
                    f"Vega=${leg.greeks.vega_usd:.2f}, "
                    f"Theta=${leg.greeks.theta_usd:.2f}/day\n"
                )
                f.write(
                    f"       Contribution: Delta={leg.delta_contribution:.4f}, "
                    f"Vega=${leg.vega_contribution:.2f}\n\n"
                )

            f.write("2. AGGREGATED GREEKS\n")
            f.write("-" * 40 + "\n")
            f.write(f"Net Delta: {analysis_result.net_delta:.4f} BTC\n")
            f.write(f"Net Gamma: {analysis_result.net_gamma:.6f}\n")
            f.write(f"Net Vega: ${analysis_result.net_vega:.2f}\n")
            f.write(f"Net Theta: ${analysis_result.net_theta:.2f}/day\n\n")

            f.write("3. RISK SUMMARY\n")
            f.write("-" * 40 + "\n")
            risk_summary = analysis_result.risk_summary
            for greek, risk_level in risk_summary.items():
                f.write(f"{greek.capitalize()}: {risk_level}\n")

            f.write(
                f"\nVega Neutral: {'YES' if analysis_result.is_vega_neutral else 'NO'}\n"
            )
            f.write(
                f"Delta Neutral: {'YES' if analysis_result.is_delta_neutral else 'NO'}\n\n"
            )

            if analysis_result.hedge_recommendation:
                f.write("4. HEDGE RECOMMENDATION\n")
                f.write("-" * 40 + "\n")
                hedge = analysis_result.hedge_recommendation
                f.write(f"Instrument: {hedge.instrument.instrument_type}\n")
                if hedge.instrument.call_symbol:
                    f.write(f"Call: {hedge.instrument.call_symbol}\n")
                if hedge.instrument.put_symbol:
                    f.write(f"Put: {hedge.instrument.put_symbol}\n")
                f.write(f"Optimal Quantity: {hedge.optimal_quantity:.4f} contracts\n")
                if hedge.hedge_cost:
                    f.write(f"Hedge Cost: ${hedge.hedge_cost:.2f}\n")
                f.write(f"Effectiveness: {hedge.effectiveness:.1f}%\n")
                f.write(f"Vega Impact: ${hedge.vega_impact:.2f}\n\n")

            f.write("5. SCENARIO ANALYSIS\n")
            f.write("-" * 40 + "\n")
            if analysis_result.max_profit:
                f.write(f"Max Profit: ${analysis_result.max_profit:,.2f}\n")
            if analysis_result.max_loss:
                f.write(f"Max Loss: ${analysis_result.max_loss:,.2f}\n")
            if analysis_result.breakeven_points:
                f.write(
                    f"Breakeven Points: {', '.join(f'${p:,.0f}' for p in analysis_result.breakeven_points)}\n"
                )

            f.write(f"\n6. WARNINGS & RECOMMENDATIONS\n")
            f.write("-" * 40 + "\n")
            if analysis_result.warnings:
                for warning in analysis_result.warnings:
                    f.write(f"⚠️  {warning}\n")
            else:
                f.write("No warnings\n")

            f.write("\n")
            if analysis_result.recommendations:
                for i, recommendation in enumerate(analysis_result.recommendations, 1):
                    f.write(f"{i}. {recommendation}\n")
            else:
                f.write("No specific recommendations\n")

            f.write("\n" + "=" * 70 + "\n")
            f.write("END OF REPORT\n")
            f.write("=" * 70 + "\n")

        self.logger.info(f"Generated text report: {filepath}")
        return str(filepath)

    def save_chart(self, fig: plt.Figure, filename: str, dpi: int = 300) -> str:
        """
        Save chart to file

        Args:
            fig: Matplotlib Figure object
            filename: Output filename
            dpi: Resolution in DPI

        Returns:
            Path to saved file
        """
        filepath = self.output_dir / filename
        fig.savefig(filepath, dpi=dpi, bbox_inches="tight")
        plt.close(fig)

        self.logger.info(f"Saved chart to {filepath}")
        return str(filepath)


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Create example analysis result
    from strategy_models import (
        AnalysisResult,
        IronCondorConfig,
        IronCondorLeg,
        StrategyType,
    )
    from bybit_options.models import PositionSide, OptionType, GreeksModel

    # Create example config
    config = IronCondorConfig(
        underlying="BTC",
        expiry="19DEC25",
        long_put_strike=85000.0,
        short_put_strike=90000.0,
        short_call_strike=100000.0,
        long_call_strike=105000.0,
    )

    # Create example legs
    legs = [
        IronCondorLeg(
            symbol="BTC-19DEC25-90000-P",
            side=PositionSide.SELL,
            option_type=OptionType.PUT,
            strike=90000.0,
            size=1.0,
            greeks=GreeksModel(
                delta_coin=0.32, gamma_coin=0.000045, vega_usd=125.45, theta_usd=45.67
            ),
        )
    ]

    # Create example analysis result
    analysis_result = AnalysisResult(
        strategy_type=StrategyType.IRON_CONDOR,
        config=config,
        underlying_price=95000.0,
        current_iv=0.65,
        legs=legs,
        net_delta=0.28,
        net_gamma=-0.00034,
        net_vega=-51.38,
        net_theta=14.44,
        max_profit=2345.67,
        max_loss=-1234.56,
        breakeven_points=[88500.0, 101500.0],
        warnings=["Negative gamma exposure", "Short vega position"],
        recommendations=["Consider vega hedge with ATM straddle"],
    )

    # Create visualizer
    visualizer = StrategyVisualizer(output_dir="./test_output")

    # Generate text report
    report_path = visualizer.generate_text_report(analysis_result)
    print(f"Generated report: {report_path}")

    # Export to JSON
    json_path = visualizer.export_to_json(analysis_result)
    print(f"Exported JSON: {json_path}")

    # Export to CSV
    csv_files = visualizer.export_to_csv(analysis_result)
    print(f"Exported CSV files: {csv_files}")

    print("\nVisualization module ready for use!")
