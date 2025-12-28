"""
Display Manager - Console output formatting
Separates presentation from business logic
"""
import os
import shutil
from datetime import datetime
from typing import Dict, List
from data_models import (
    PortfolioRiskModel, CoinRiskModel, PositionModel,
    PositionType, GreeksModel
)


class DisplayManager:
    """
    Handles all console output formatting
    In production, this would be replaced by API serialization
    """
    
    @staticmethod
    def print_header(title: str, width: int = 120):
        """Print section header"""
        print("\n" + "=" * width)
        print(f"{title:^{width}}")
        print("=" * width)
    
    @staticmethod
    def print_subheader(title: str, width: int = 120):
        """Print subsection header"""
        print(f"\n┌─ {title} " + "─" * (width - len(title) - 4))
    
    @staticmethod
    def print_positions_table(positions: List[PositionModel]):
        """Display all positions in a formatted table"""
        if not positions:
            print("\n⚠️  No positions found")
            return
        
        DisplayManager.print_header("POSITIONS OVERVIEW")
        
        # Group by coin
        by_coin: Dict[str, List[PositionModel]] = {}
        for pos in positions:
            if pos.base_coin not in by_coin:
                by_coin[pos.base_coin] = []
            by_coin[pos.base_coin].append(pos)
        
        # Table header
        print(
            f"\n{'SYMBOL':<45} | {'TYPE':<8} | {'SIDE':<5} | "
            f"{'SIZE':<12} | {'DELTA':<12} | {'GAMMA':<12} | "
            f"{'VEGA':<12} | {'THETA':<12}"
        )
        print("─" * 150)
        
        # Sort coins (futures-only last)
        sorted_coins = sorted(
            by_coin.keys(),
            key=lambda c: (
                all(p.pos_type == PositionType.LINEAR for p in by_coin[c]),
                c
            )
        )
        
        for coin in sorted_coins:
            coin_positions = by_coin[coin]
            
            # Coin divider
            print(f"\n{'─' * 60} {coin} {'─' * (89 - len(coin))}")
            
            for pos in coin_positions:
                g = pos.greeks
                
                # Format symbol with strike if option
                symbol_display = pos.symbol
                if pos.strike:
                    symbol_display = f"{pos.symbol} (K={pos.strike:.0f})"
                
                print(
                    f"{symbol_display:<45} | "
                    f"{pos.pos_type.value:<8} | "
                    f"{pos.side.value:<5} | "
                    f"{pos.size:<12.4f} | "
                    f"{g.delta_coin:+12.4f} | "
                    f"{g.gamma_coin:+12.6f} | "
                    f"${g.vega_usd:+11.2f} | "
                    f"${g.theta_usd:+11.2f}"
                )
        
        print("\n" + "=" * 150)
    
    @staticmethod
    def print_coin_risk(coin_risk: CoinRiskModel):
        """Display risk metrics for a single coin"""
        coin = coin_risk.base_coin
        g = coin_risk.total_greeks
        
        print(f"│")
        print(f"│ 📊 TOTAL EXPOSURE:")
        print(
            f"│   Delta: {g.delta_coin:+15.4f} {coin:<6} │ "
            f"Gamma: {g.gamma_coin:+12.6f} │ "
            f"Vega: ${g.vega_usd:+10.2f} │ "
            f"Theta: ${g.theta_usd:+10.2f}"
        )
        
        # Underlying price
        if coin_risk.underlying_price:
            print(f"│   Underlying Price: ${coin_risk.underlying_price:,.2f}")
        
        # Breakdown
        if coin_risk.futures_greeks.delta_coin != 0 or \
           coin_risk.options_greeks.delta_coin != 0:
            
            print(f"│")
            print(f"│ 📈 BREAKDOWN:")
            
            fg = coin_risk.futures_greeks
            og = coin_risk.options_greeks
            
            print(f"│   Futures:  Δ = {fg.delta_coin:+15.4f} {coin}")
            print(
                f"│   Options:  Δ = {og.delta_coin:+15.4f} {coin} │ "
                f"Γ = {og.gamma_coin:+12.6f} │ "
                f"ν = ${og.vega_usd:+10.2f} │ "
                f"θ = ${og.theta_usd:+10.2f}"
            )
        
        # Series breakdown
        if coin_risk.series_greeks:
            print(f"│")
            print(f"│ 🗓️  BY EXPIRY:")
            
            for series in sorted(coin_risk.series_greeks.keys()):
                sg = coin_risk.series_greeks[series]
                print(
                    f"│   • {series:<12} │ "
                    f"Δ={sg.delta_coin:+10.4f} │ "
                    f"Γ={sg.gamma_coin:+12.6f} │ "
                    f"ν=${sg.vega_usd:+10.2f} │ "
                    f"θ=${sg.theta_usd:+10.2f}"
                )
        
        print(f"└" + "─" * 118)
    
    @staticmethod
    def print_portfolio_summary(portfolio: PortfolioRiskModel):
        """Display complete portfolio summary"""
        DisplayManager.print_header("PORTFOLIO RISK SUMMARY")
        
        # Margin metrics
        print(f"\n💰 MARGIN & ACCOUNT:")
        m = portfolio.margin
        
        health_emoji = {
            "HEALTHY": "🟢",
            "MODERATE": "🟡",
            "HIGH_RISK": "🔴",
            "UNKNOWN": "⚪"
        }.get(m.health_status, "⚪")
        
        print(f"   {health_emoji} Account Type: {m.account_type}")
        print(f"   • Total Equity:        ${m.total_equity:>15,.2f}")
        print(f"   • Available Balance:   ${m.available_balance:>15,.2f}")
        print(f"   • Used Margin:         ${m.used_margin:>15,.2f}")
        print(f"   • Maintenance Margin:  ${m.maintenance_margin:>15,.2f}")
        
        if m.margin_ratio is not None:
            print(f"   • Margin Utilization:  {m.margin_ratio:>15.2f}%")
        
        if m.unrealized_pnl != 0:
            pnl_emoji = "🟢" if m.unrealized_pnl > 0 else "🔴"
            print(f"   {pnl_emoji} Unrealized P&L:     ${m.unrealized_pnl:>15,.2f}")
        
        # Portfolio Greeks
        print(f"\n📊 PORTFOLIO GREEKS:")
        print(f"   • Total Vega:  ${portfolio.total_vega_usd:+15,.2f}")
        print(f"   • Total Theta: ${portfolio.total_theta_usd:+15,.2f}/day")
        
        # Vega interpretation
        if abs(portfolio.total_vega_usd) > 100:
            if portfolio.total_vega_usd > 0:
                print(
                    f"     → 🟢 Long Vega: You profit when IV increases"
                )
            else:
                print(
                    f"     → 🔴 Short Vega: You profit when IV decreases"
                )
        
        # Theta interpretation
        if abs(portfolio.total_theta_usd) > 10:
            if portfolio.total_theta_usd > 0:
                print(
                    f"     → 🟢 Positive Theta: Time decay works for you"
                )
            else:
                print(
                    f"     → 🔴 Negative Theta: Time decay works against you"
                )
        
        # Delta by coin (non-aggregatable)
        print(f"\n⚠️  DELTA EXPOSURE (by coin - DO NOT aggregate):")
        for coin in sorted(portfolio.coin_risks.keys()):
            delta = portfolio.coin_risks[coin].total_greeks.delta_coin
            
            delta_emoji = (
                "🟢" if delta > 0 else
                "🔴" if delta < 0 else
                "⚪"
            )
            
            print(f"   {delta_emoji} {coin:<8}: {delta:+18.4f} {coin}")
        
        # Warnings
        if portfolio.warnings:
            print(f"\n🚨 RISK WARNINGS:")
            for warning in portfolio.warnings:
                print(f"   {warning}")
        else:
            print(f"\n✅ No critical warnings")
        
        print("\n" + "=" * 120)
    
    @staticmethod
    def print_coin_risks(coin_risks: Dict[str, CoinRiskModel]):
        """Display detailed risk for each coin"""
        DisplayManager.print_header("RISK BY COIN")
        
        for coin in sorted(coin_risks.keys()):
            DisplayManager.print_subheader(coin)
            DisplayManager.print_coin_risk(coin_risks[coin])
        
        print("\n" + "=" * 120)
    
    @staticmethod
    def print_enhanced_position_details(positions: List[PositionModel]):
        """Display positions with enhanced metrics (IV, slippage, gamma rent)"""
        enhanced = [
            p for p in positions
            if p.iv_metrics or p.slippage or p.gamma_rent
        ]
        
        if not enhanced:
            return
        
        DisplayManager.print_header("ENHANCED POSITION METRICS")
        
        print(
            f"\n{'SYMBOL':<40} | {'IV vs ATM':<15} | "
            f"{'SPREAD %':<10} | {'GAMMA RENT':<15}"
        )
        print("─" * 90)
        
        for pos in enhanced:
            symbol = pos.symbol
            
            # IV metrics
            iv_str = "─"
            if pos.iv_metrics and pos.iv_metrics.iv_diff_pct is not None:
                diff = pos.iv_metrics.iv_diff_pct
                iv_emoji = "🔴" if diff > 10 else "🟢" if diff < -10 else "⚪"
                iv_str = f"{iv_emoji} {diff:+.2f}%"
            
            # Slippage
            spread_str = "─"
            if pos.slippage:
                risk = pos.slippage.slippage_risk
                risk_emoji = {
                    "LOW": "🟢",
                    "MEDIUM": "🟡",
                    "HIGH": "🔴"
                }.get(risk, "⚪")
                spread_str = f"{risk_emoji} {pos.slippage.spread_pct:.2f}%"
            
            # Gamma rent
            rent_str = "─"
            if pos.gamma_rent and pos.gamma_rent.gamma_rent is not None:
                rent = pos.gamma_rent.gamma_rent
                rent_emoji = "🟢" if rent > 0 else "🔴"
                rent_str = f"{rent_emoji} ${rent:,.0f}"
            
            print(
                f"{symbol:<40} | "
                f"{iv_str:<15} | "
                f"{spread_str:<10} | "
                f"{rent_str:<15}"
            )
        
        print("\n" + "=" * 90)
        
        # Legend
        print("\n💡 LEGEND:")
        print("   • IV vs ATM: % difference from At-The-Money IV")
        print("     🔴 >+10% (expensive), 🟢 <-10% (cheap)")
        print("   • Spread %: Liquidity risk (Ask-Bid)/Mark")
        print("     🟢 <0.5%, 🟡 0.5-2%, 🔴 >2%")
        print("   • Gamma Rent: Theta/Gamma ratio")
        print("     🟢 Positive (earning), 🔴 Negative (paying)")
        print("=" * 90)

    @staticmethod
    def save_report_to_markdown(
        positions: List[PositionModel],
        portfolio: PortfolioRiskModel,
        output_dir: str = "reports"
    ) -> str:
        """
        Генерирует Markdown-отчет для анализа ИИ-агентом.
        Сохраняет файл в папку reports/
        """
        # 1. Создаем папку, если нет
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 2. Генерируем имя файла (таймстемп + fixed name для удобства)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{output_dir}/risk_analysis_{timestamp}.md"
        latest_filename = f"{output_dir}/latest_analysis.md"

        with open(filename, "w", encoding="utf-8") as f:
            # === ЗАГОЛОВОК ===
            f.write(f"# 🛡️ Options Risk Report\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # === 1. PORTFOLIO SUMMARY ===
            f.write("## 1. Portfolio Summary\n\n")
            m = portfolio.margin
            f.write("| Metric | Value | Status |\n")
            f.write("| :--- | :--- | :--- |\n")
            f.write(f"| **Equity** | `${m.total_equity:,.2f}` | - |\n")
            f.write(f"| **Margin Utilization** | `{m.margin_ratio:.2f}%` | {'✅ Safe' if m.margin_ratio < 60 else '⚠️ High'} |\n")
            f.write(f"| **Portfolio Theta** | `${portfolio.total_theta_usd:+.2f}/day` | Cash Flow |\n")
            f.write(f"| **Portfolio Vega** | `${portfolio.total_vega_usd:+.2f}` | Volatility Risk |\n")
            f.write("\n")
            
            # === GREEKS BY COIN ===
            f.write("### Greeks by Asset\n\n")
            if portfolio.coin_risks:
                for coin, coin_risk in portfolio.coin_risks.items():
                    g = coin_risk.total_greeks
                    price_str = f" @ ${coin_risk.underlying_price:,.2f}" if coin_risk.underlying_price else ""
                    
                    f.write(f"**{coin}**{price_str}\n\n")
                    f.write("| Greek | Value |\n")
                    f.write("| :--- | :--- |\n")
                    f.write(f"| Delta | `{g.delta_coin:+.4f} {coin}` |\n")
                    f.write(f"| Gamma | `{g.gamma_coin:+.6f}` |\n")
                    f.write(f"| Vega | `${g.vega_usd:+.2f}` |\n")
                    f.write(f"| Theta | `${g.theta_usd:+.2f}/day` |\n")
                    f.write("\n")
            f.write("\n")

            # === PORTFOLIO HOLDINGS ===
            f.write("### Portfolio Holdings\n\n")
            if portfolio.margin and portfolio.margin.holdings:
                f.write("| Coin | Amount | USD Value | Equity | Unrealized P&L |\n")
                f.write("| :--- | :--- | :--- | :--- | :--- |\n")
                
                total_holdings_value = 0.0
                for holding in portfolio.margin.holdings:
                    pnl_color = "🟢" if holding.unrealized_pnl >= 0 else "🔴"
                    f.write(
                        f"| {holding.coin} | {holding.wallet_balance:.8f} | "
                        f"${holding.usd_value:,.2f} | ${holding.equity:,.2f} | "
                        f"{pnl_color} ${holding.unrealized_pnl:+,.2f} |\n"
                    )
                    total_holdings_value += holding.usd_value
                
                f.write(f"| **TOTAL** | | **${total_holdings_value:,.2f}** | | |\n")
            else:
                f.write("No holdings data available.\n")
            f.write("\n")

            # === 2. ALERTS & WARNINGS ===
            f.write("## 2. Risk Alerts\n\n")
            if portfolio.warnings:
                for w in portfolio.warnings:
                    f.write(f"- ⚠️ {w}\n")
            else:
                f.write("- ✅ No critical risk warnings detected.\n")
            f.write("\n")

            # === 3. POSITIONS TABLE ===
            f.write("## 3. Positions Details\n\n")
            f.write("| Symbol | Side | Size | Delta | Gamma | Vega | Theta |\n")
            f.write("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n")

            for p in positions:
                # Форматирование метрик
                g = p.greeks
                
                # Строка таблицы
                row = (
                    f"| `{p.symbol}` | {p.side.value} | {p.size} | "
                    f"`{g.delta_coin:+.4f}` | `{g.gamma_coin:+.6f}` | `{g.vega_usd:+.1f}` | `{g.theta_usd:+.1f}` |"
                )
                f.write(row + "\n")

            # === 4. POSITIONS P&L TABLE ===
            f.write("\n## 4. Unrealized P&L by Position\n\n")
            
            # Фильтруем позиции с данными P&L
            pnl_positions = [p for p in positions if p.unrealized_pnl is not None]
            if pnl_positions:
                f.write("| Symbol | Entry Price | Mark Value | Unrealized P&L | Return % |\n")
                f.write("| :--- | :--- | :--- | :--- | :--- |\n")
                
                total_pnl = 0.0
                for p in pnl_positions:
                    # Форматируем entry и mark
                    if p.entry_price:
                        entry_str = f"${p.entry_price:,.2f}"
                    else:
                        entry_str = "N/A"
                    
                    if p.mark_value:
                        mark_str = f"${p.mark_value:,.2f}"
                    else:
                        mark_str = "N/A"
                    
                    pnl = p.unrealized_pnl
                    
                    # Вычисляем процент возврата
                    if p.entry_price and p.entry_price != 0 and p.mark_value:
                        ret_pct = ((p.mark_value - p.entry_price) / p.entry_price * 100)
                        ret_str = f"{ret_pct:+.2f}%"
                    else:
                        ret_str = "N/A"
                    
                    pnl_color = "🟢" if pnl >= 0 else "🔴"
                    f.write(
                        f"| `{p.symbol}` | {entry_str} | {mark_str} | "
                        f"{pnl_color} ${pnl:+,.2f} | {ret_str} |\n"
                    )
                    total_pnl += pnl
                
                f.write(f"| **TOTAL** | | | **${total_pnl:+,.2f}** | |\n")
            else:
                f.write("No position P&L data available.\n")
            f.write("\n")

            # === 5. IV & SLIPPAGE METRICS ===
            f.write("## 5. IV & Liquidity Analysis\n\n")
            
            # IV информация
            iv_positions = [p for p in positions if p.iv_metrics and p.iv_metrics.position_iv is not None]
            if iv_positions:
                f.write("### Implied Volatility (IV)\n\n")
                f.write("| Symbol | Position IV | ATM IV | IV Diff | Status |\n")
                f.write("| :--- | :--- | :--- | :--- | :--- |\n")
                
                for p in iv_positions:
                    iv_m = p.iv_metrics
                    pos_iv = f"{iv_m.position_iv:.2%}" if iv_m.position_iv else "N/A"
                    atm_iv = f"{iv_m.atm_iv:.2%}" if iv_m.atm_iv else "N/A"
                    
                    if iv_m.iv_diff_pct is not None:
                        iv_diff = f"{iv_m.iv_diff_pct:+.2f}%"
                        status = "📈 Expensive" if iv_m.is_expensive else "📉 Cheap"
                    else:
                        iv_diff = "N/A"
                        status = "N/A"
                    
                    f.write(f"| `{p.symbol}` | {pos_iv} | {atm_iv} | {iv_diff} | {status} |\n")
            else:
                f.write("### Implied Volatility (IV)\nNo IV data available.\n\n")
            
            # Slippage информация
            slippage_positions = [p for p in positions if p.slippage]
            if slippage_positions:
                f.write("\n### Liquidity & Slippage\n\n")
                f.write("| Symbol | Bid-Ask Spread | Spread % | Liquidity Risk |\n")
                f.write("| :--- | :--- | :--- | :--- |\n")
                
                for p in slippage_positions:
                    sl = p.slippage
                    f.write(
                        f"| `{p.symbol}` | ${sl.spread_abs:,.2f} | {sl.spread_pct:.3f}% | "
                        f"{sl.slippage_risk} |\n"
                    )
            f.write("\n")

            # === 6. SCENARIO ANALYSIS (P&L at different price levels) ===
            f.write("## 6. Price Scenario Analysis\n\n")
            f.write("Portfolio P&L at different price levels by asset:\n\n")
            
            # Строим сценарии для каждого актива отдельно
            for coin, coin_risk in portfolio.coin_risks.items():
                if not coin_risk.underlying_price:
                    continue
                    
                main_price = coin_risk.underlying_price
                portfolio_delta = coin_risk.total_greeks.delta_coin
                portfolio_gamma = coin_risk.total_greeks.gamma_coin
                portfolio_theta = coin_risk.total_greeks.theta_usd
                
                f.write(f"### {coin} Scenarios\n\n")
                f.write(f"**Current Price**: ${main_price:,.2f}\n\n")
                f.write("| Price Change | New Price | Delta P&L | Gamma P&L | Theta Decay | Total P&L |\n")
                f.write("| :--- | :--- | :--- | :--- | :--- | :--- |\n")
                
                scenarios = [-10, -5, 0, 5, 10]
                for pct in scenarios:
                    price_change = main_price * pct / 100
                    new_price = main_price + price_change
                    
                    # Delta P&L: Δ × price_change
                    delta_pnl = portfolio_delta * price_change
                    
                    # Gamma P&L: 0.5 × Γ × price_change²
                    gamma_pnl = 0.5 * portfolio_gamma * (price_change ** 2)
                    
                    # Theta P&L: θ × 1 day (approximation)
                    theta_pnl = portfolio_theta
                    
                    total_pnl = delta_pnl + gamma_pnl + theta_pnl
                    
                    # Цветной индикатор
                    if pct == 0:
                        scenario_label = f"📍 Current"
                    else:
                        scenario_label = f"{pct:+d}%"
                    
                    f.write(
                        f"| {scenario_label} | ${new_price:,.2f} | "
                        f"${delta_pnl:+,.2f} | ${gamma_pnl:+,.2f} | "
                        f"${theta_pnl:+,.2f} | **${total_pnl:+,.2f}** |\n"
                    )
                
                f.write("\n")

            # === 7. STRATEGY CONTEXT ===
            f.write("## 7. Analysis Notes\n")
            f.write("> **For AI Agent Analysis:**\n")
            f.write("> - Review portfolio Greeks for risk exposure\n")
            f.write("> - Monitor margin utilization and delta exposure\n")
            f.write("> - Assess theta decay and vega sensitivity\n")
            f.write("> - Check unrealized P&L and position-level returns\n")
            f.write("> - Evaluate IV and liquidity conditions for each position\n")
            f.write("> - Review price scenarios to understand max profit/loss potential\n")

        # Создаем копию "latest", чтобы всегда открывать один файл
        shutil.copyfile(filename, latest_filename)
        
        return filename