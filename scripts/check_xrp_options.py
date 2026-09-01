
import asyncio
import os
from bybit_options.services.bybit_connector import BybitConnector
from dotenv import load_dotenv

async def main():
    load_dotenv()
    api_key = os.getenv("BYBIT_API_KEY")
    api_secret = os.getenv("BYBIT_API_SECRET")
    
    # Use public endpoints if no keys, but better to have them if possible.
    # If keys are missing, we can try with empty strings for public endpoints if the connector supports it
    # But connector usually requires keys.
    # Let's assume we can use public request without keys for get_instruments_info if we modify connector or just use raw aiohttp.
    # Actually, BybitConnector inherits from BaseConnector.
    
    if not api_key:
        print("No API keys found. Attempting to check with a raw request...")
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.bybit.com/v5/market/instruments-info?category=option") as resp:
                data = await resp.json()
                if data['retCode'] == 0:
                    list_data = data['result']['list']
                    base_coins = set([item['baseCoin'] for item in list_data])
                    print(f"Available Option Base Coins: {base_coins}")
                    if 'XRP' in base_coins:
                        print("XRP Options FOUND.")
                    else:
                        print("XRP Options NOT found.")
                else:
                    print(f"Error: {data}")
        return

    connector = BybitConnector(api_key, api_secret)
    try:
        instruments = await connector.get_instruments_info(category="option")
        base_coins = set([i['baseCoin'] for i in instruments])
        print(f"Available Option Base Coins: {base_coins}")
        
        if 'XRP' in base_coins:
            print("XRP Options FOUND.")
        else:
            print("XRP Options NOT found.")
            
    finally:
        await connector.close()

if __name__ == "__main__":
    asyncio.run(main())
