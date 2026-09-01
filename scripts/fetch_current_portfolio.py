#!/usr/bin/env python3
"""
Fetch and display current portfolio data from Bybit.
Uses AnalysisOrchestrator to get real-time positions and Greeks.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
from bybit_options.config.logging import configure_logging
from bybit_options.services.bybit_connector import BybitConnector
from bybit_options.orchestration.analysis_orchestrator import AnalysisOrchestrator
from bybit_options.models.portfolio import PortfolioRiskModel

async def main():
    load_dotenv()
    
    api_key = os.getenv("BYBIT_API_KEY")
    api_secret = os.getenv("BYBIT_API_SECRET")
    testnet = os.getenv("BYBIT_TESTNET", "true").lower() == "true"
    
    if not api_key:
        print("Error: BYBIT_API_KEY must be set in .env")
        return
        
    print(f"🔌 Connecting to Bybit ({'Testnet' if testnet else 'Mainnet'})...")

    # Configure logging to suppress debug noise
    # configure_logging() 
    # logging.getLogger("bybit_options").setLevel(logging.WARNING)
    
    connector = BybitConnector(
        api_key=api_key,
        api_secret=api_secret,
        testnet=testnet,
    )
    
    orchestrator = AnalysisOrchestrator(connector)
    
    print("⏳ Fetching portfolio data from Bybit...")
    
    try:
        async with connector:
            portfolio = await orchestrator.run_full_analysis()
            _print_report(portfolio)
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        import traceback
        traceback.print_exc()

def _print_report(portfolio: PortfolioRiskModel):
    print("\n" + "="*80)
    print(f"📊 PORTFOLIO REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # 1. Account Summary
    margin = portfolio.margin
    print(f"\n💰 ACCOUNT SUMMARY ({margin.account_type})")
    print(f"{'Total Equity':<20} ${margin.total_equity:,.2f}")
    print(f"{'Available Balance':<20} ${margin.available_balance:,.2f}")
    print(f"{'Used Margin':<20} ${margin.used_margin:,.2f}")
    
    ratio_str = f"{margin.margin_ratio}%" if margin.margin_ratio is not None else "N/A"
    print(f"{'Margin Ratio':<20} {ratio_str} ({margin.health_status})")
    print(f"{'Unrealized PnL':<20} ${margin.unrealized_pnl:,.2f}")
    
    # 2. Greeks Summary
    print("\n📐 GREEKS SUMMARY")
    print("-" * 60)
    
    if not portfolio.coin_risks:
        print("No risk data available.")
    
    for coin, risk in portfolio.coin_risks.items():
        price = risk.underlying_price or 0.0
        greeks = risk.total_greeks
        
        print(f"\nYielding risk for {coin} (Price: ${price:,.2f})")
        print("-" * 40)
        print(f"{'Delta':<15} {greeks.delta_coin:+.4f} {coin}")
        print(f"{'Gamma':<15} {greeks.gamma_coin:+.6f} {coin}")
        print(f"{'Vega':<15} ${greeks.vega_usd:+.2f}")
        print(f"{'Theta':<15} ${greeks.theta_usd:+.2f}")

    # 3. Positions
    print("\n📜 OPEN POSITIONS")
    print("-" * 120)
    print(f"{'Symbol':<32} {'Side':<6} {'Size':<8} {'Mark':<10} {'PnL':<12} {'Delta':<10} {'Gamma':<10} {'Vega':<10} {'Theta':<10}")
    print("-" * 120)
    
    has_positions = False
    for coin, risk in portfolio.coin_risks.items():
        for pos in risk.positions:
            has_positions = True
            side = pos.side
            size = float(pos.size)
            pnl = pos.unrealized_pnl or 0.0
            
            # Calculate Mark Price from Mark Value if available
            mark_price = 0.0
            if pos.mark_value and size > 0:
                mark_price = pos.mark_value / size
            elif pos.entry_price:
                # Fallback to entry if no mark (unlikely but safe)
                mark_price = pos.entry_price
            
            # Greeks
            delta = pos.greeks.delta_coin
            gamma = pos.greeks.gamma_coin
            vega = pos.greeks.vega_usd
            theta = pos.greeks.theta_usd
            
            print(f"{pos.symbol:<32} {side.value:<6} {size:<8.3f} ${mark_price:<9.2f} ${pnl:<11.2f} {delta:<10.4f} {gamma:<10.5f} {vega:<10.1f} {theta:<10.1f}")
            
    if not has_positions:
        print("No open positions found.")
            
    print("-" * 120)
    print("Done.\n")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCancelled.")
