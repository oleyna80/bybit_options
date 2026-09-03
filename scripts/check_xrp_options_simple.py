
import aiohttp
import asyncio
import os
from dotenv import load_dotenv

async def main():
    load_dotenv()
    
    url = "https://api.bybit.com/v5/market/instruments-info"
    params = {"category": "option", "limit": 1000}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            data = await resp.json()
            if data['retCode'] == 0:
                instruments = data['result']['list']
                base_coins = set([i['baseCoin'] for i in instruments])
                print(f"Available Option Base Coins: {base_coins}")
                
                if 'XRP' in base_coins:
                    print("XRP Options FOUND.")
                else:
                    print("XRP Options NOT found.")
            else:
                print(f"Error fetching instruments: {data}")

if __name__ == "__main__":
    asyncio.run(main())
