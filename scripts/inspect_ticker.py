import asyncio
import os
import sys
import json
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bybit_options.services.bybit_connector import BybitConnector

async def main():
    load_dotenv()
    api_key = os.getenv("BYBIT_API_KEY")
    api_secret = os.getenv("BYBIT_API_SECRET")
    
    async with BybitConnector(api_key, api_secret) as connector:
        symbol = "BTC-26JUN26-80000-P-USDT"
        tickers = await connector.get_tickers(category="option", symbol=symbol)
        if tickers:
            print(json.dumps(tickers[0], indent=2))
        else:
            print("No ticker found.")

if __name__ == "__main__":
    asyncio.run(main())
