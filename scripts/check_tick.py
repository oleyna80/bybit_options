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
        # Check for the Call option
        symbol = "BTC-26JUN26-100000-C-USDT"
        infos = await connector.get_instruments_info(category="option", symbol=symbol)
        
        if not infos:
            print(f"No info found for {symbol}")
            return

        info = infos[0]
        print(json.dumps(info, indent=2))
        
        price_filter = info.get("priceFilter", {})
        print(f"\nTick Size: {price_filter.get('tickSize')}")
        print(f"Min Price: {price_filter.get('minPrice')}")

if __name__ == "__main__":
    asyncio.run(main())
