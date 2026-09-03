
import asyncio
import aiohttp
import logging
from datetime import datetime

POSITIONS = {
    "FEB_SHORT": "BTC-27FEB26-82000-P-USDT", # Buy to Close
    "FEB_LONG": "BTC-27FEB26-76000-P-USDT",  # Sell to Close (Liquidity Source)
    
    # Candidates
    "MAR_SHORT": "BTC-27MAR26-78000-P-USDT",
    "MAR_LONG": "BTC-27MAR26-72000-P-USDT",
    
    "JUN_SHORT": "BTC-26JUN26-80000-P-USDT",
    "JUN_LONG": "BTC-26JUN26-70000-P-USDT"
}

async def fetch_ticker(session, symbol):
    url = "https://api.bybit.com/v5/market/tickers"
    params = {"category": "option", "symbol": symbol}
    async with session.get(url, params=params) as resp:
        data = await resp.json()
        if data['retCode'] == 0 and data['result']['list']:
            return data['result']['list'][0]
        return None

async def main():
    async with aiohttp.ClientSession() as session:
        print(f"Comparing Roll Scenarios (Size 0.24 BTC)...\n")
        
        # 1. Get Current Spread Liquidation Value
        short_ticker = await fetch_ticker(session, POSITIONS["FEB_SHORT"])
        long_ticker = await fetch_ticker(session, POSITIONS["FEB_LONG"])
        
        # Buy Close Short (Ask), Sell Close Long (Bid)
        close_cost = float(short_ticker['ask1Price'])
        close_credit = float(long_ticker['bid1Price'])
        net_close_cost = close_cost - close_credit
        
        print(f"CLOSE FEB SPREAD ($82k/$76k):")
        print(f"  Buy Back Short: -${close_cost:.2f}")
        print(f"  Sell Long:      +${close_credit:.2f}")
        print(f"  Net Cost:       -${net_close_cost:.2f}")
        print("-" * 60)

        # 2. Analyze March Candidate
        mar_short = await fetch_ticker(session, POSITIONS["MAR_SHORT"])
        mar_long = await fetch_ticker(session, POSITIONS["MAR_LONG"])
        
        if mar_short and mar_long:
            # Sell Short (Bid), Buy Long (Ask)
            open_credit = float(mar_short['bid1Price'])
            open_cost = float(mar_long['ask1Price'])
            net_open_credit = open_credit - open_cost
            
            # Greeks (Approx per unit)
            theta_short = float(mar_short.get('theta', 0))
            theta_long = float(mar_long.get('theta', 0))
            net_theta = theta_short - theta_long # Short - Long logic? 
            # We Sell Short (positive theta for us), Buy Long (negative theta for us)
            # API returns Greeks for the Option itself. 
            # Short Option Theta Contribution = -1 * OptionTheta (OptionTheta is usually negative, so -(-)=+)
            # Let's assume API Theta is negative for Long holders.
            # Our Theta = (-1 * Theta_Short) + (1 * Theta_Long) 
            # Wait, Shorting a negative theta option gives positive theta.
            portfolio_theta = (-1 * theta_short) + (1 * theta_long)
            
            print(f"OPTION A: ROLL TO MARCH SPREAD ($78k/$72k)")
            print(f"  Sell Short ($78k): +${open_credit:.2f}")
            print(f"  Buy Long ($72k):   -${open_cost:.2f}")
            print(f"  Net Credit:        +${net_open_credit:.2f}")
            print(f"  Total Roll Cost:   ${(net_open_credit - net_close_cost):.2f}")
            print(f"  Est. Daily Theta:  {portfolio_theta:.2f} (Income Speed)")
            print("-" * 60)

        # 3. Analyze June Candidate
        jun_short = await fetch_ticker(session, POSITIONS["JUN_SHORT"])
        jun_long = await fetch_ticker(session, POSITIONS["JUN_LONG"])
        
        if jun_short and jun_long:
            open_credit_j = float(jun_short['bid1Price'])
            open_cost_j = float(jun_long['ask1Price'])
            net_open_credit_j = open_credit_j - open_cost_j
            
            theta_short_j = float(jun_short.get('theta', 0))
            theta_long_j = float(jun_long.get('theta', 0))
            portfolio_theta_j = (-1 * theta_short_j) + (1 * theta_long_j)

            print(f"OPTION B: ROLL TO JUNE SPREAD ($80k/$70k)")
            print(f"  Sell Short ($80k): +${open_credit_j:.2f}")
            print(f"  Buy Long ($70k):   -${open_cost_j:.2f}")
            print(f"  Net Credit:        +${net_open_credit_j:.2f}")
            print(f"  Total Roll Cost:   ${(net_open_credit_j - net_close_cost):.2f}")
            print(f"  Est. Daily Theta:  {portfolio_theta_j:.2f} (Income Speed)")
            print("-" * 60)
            
if __name__ == "__main__":
    asyncio.run(main())
