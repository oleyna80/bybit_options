#!/usr/bin/env python3
"""
Fetch March Option Chain for Alternative Strategies
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bybit_options.services.bybit_connector import BybitConnector

async def main():
    load_dotenv()
    api_key = os.getenv("BYBIT_API_KEY")
    api_secret = os.getenv("BYBIT_API_SECRET")
    
    async with BybitConnector(api_key, api_secret) as connector:
        # Looking for March 27 2026 expiries (27MAR26 or similar? No, standard is usually last Friday)
        # Check available expiries first or guess. 
        # User has positions in 26JUN26.
        # Let's list expiries or just search for BTC options.
        
        # We want to Hedge Feb 27 (21 DTE). Next monthly is likely March 27 (49 DTE).
        # We need strikes around 60k-65k.
        
        print("Fetching tickers...")
        tickers = await connector.get_tickers(category="option", base_coin="BTC")
        
        march_puts = []
        feb_lower_puts = []
        
        for t in tickers:
            symbol = t['symbol']
            # Parse symbol: BTC-27MAR26-63000-P
            parts = symbol.split('-')
            if len(parts) < 4: continue
            
            expiry = parts[1]
            strike = float(parts[2])
            kind = parts[3] # C or P
            
            # Filter
            if kind == 'P':
                # March Candidate (Hedge)
                if "MAR26" in expiry and 55000 <= strike <= 65000:
                    march_puts.append(t)
                # Feb Roll Candidates (Roll Down)
                if "FEB26" in expiry and 55000 <= strike <= 60000:
                    feb_lower_puts.append(t)

        print(f"\n--- MARCH 26 PUTS (Calendar Candidates) ---")
        for t in sorted(march_puts, key=lambda x: float(x['symbol'].split('-')[2])):
            print(f"{t['symbol']:<25} Bid:{t['bid1Price']} Ask:{t['ask1Price']} Mark:{t['markPrice']} Delta:{t.get('delta', 'N/A')}")

        print(f"\n--- FEB 26 LOWER PUTS (Roll Down Candidates) ---")
        for t in sorted(feb_lower_puts, key=lambda x: float(x['symbol'].split('-')[2])):
            print(f"{t['symbol']:<25} Bid:{t['bid1Price']} Ask:{t['ask1Price']} Mark:{t['markPrice']} Delta:{t.get('delta', 'N/A')}")

if __name__ == "__main__":
    asyncio.run(main())
