
import asyncio
import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bybit_options.services.bybit_connector import BybitConnector
from bybit_options.orchestration.analysis_orchestrator import AnalysisOrchestrator

async def main():
    load_dotenv()
    api_key = os.getenv("BYBIT_API_KEY")
    api_secret = os.getenv("BYBIT_API_SECRET")
    
    async with BybitConnector(api_key, api_secret) as connector:
        orchestrator = AnalysisOrchestrator(connector)
        portfolio = await orchestrator.run_full_analysis()
        
        print("\n=== PORTFOLIO SNAPSHOT ===")
        print(f"Equity: ${portfolio.margin.total_equity:.2f}")
        print(f"Used Margin: ${portfolio.margin.used_margin:.2f} ({portfolio.margin.margin_ratio:.2f}%)")
        print(f"Available: ${portfolio.margin.available_balance:.2f}")
        
        print("\n--- GREEKS ---")
        for coin, risk in portfolio.coin_risks.items():
            g = risk.total_greeks
            print(f"[{coin}] Delta: {g.delta_coin:.4f} | Gamma: {g.gamma_coin:.6f}")
        
        print(f"Total Vega: ${portfolio.total_vega_usd:.2f}")
        print(f"Total Theta: ${portfolio.total_theta_usd:.2f}")
        
        print("\n--- POSITIONS ---")
        for coin, risk in portfolio.coin_risks.items():
            for pos in risk.positions:
                print(f"{pos.symbol}: Size={pos.size} {pos.side} | PnL={pos.unrealized_pnl:.2f}")

if __name__ == "__main__":
    asyncio.run(main())
