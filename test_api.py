import asyncio
import os
from dotenv import load_dotenv
from bybit_options.services.bybit_connector import BybitConnector

async def test():
    load_dotenv()
    api_key = os.getenv("BYBIT_API_KEY")
    api_secret = os.getenv("BYBIT_API_SECRET")
    
    print(f"API Key: {api_key[:5]}...")
    print(f"Testnet: False")
    
    async with BybitConnector(api_key, api_secret, testnet=False) as connector:
        # Test instruments info
        print("Fetching instruments info...")
        instruments = await connector.get_instruments_info(category="option", base_coin="BTC")
        print(f"Found {len(instruments)} instruments")
        
        if instruments:
            for i, instr in enumerate(instruments[:3]):
                print(f"  {i+1}. {instr.get('symbol')}")
        
        # Test tickers
        print("\nFetching tickers...")
        tickers = await connector.get_tickers(category="option", base_coin="BTC")
        print(f"Found {len(tickers)} tickers")
        
        if tickers:
            for i, ticker in enumerate(tickers[:3]):
                print(f"  {i+1}. {ticker.get('symbol')}: bid={ticker.get('bid1Price')}, ask={ticker.get('ask1Price')}")

if __name__ == "__main__":
    asyncio.run(test())