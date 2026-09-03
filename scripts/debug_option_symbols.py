
import asyncio
import aiohttp

async def main():
    url = "https://api.bybit.com/v5/market/tickers"
    params = {
        "category": "option",
        "baseCoin": "BTC",
        "limit": 10
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            data = await resp.json()
            if data['retCode'] == 0:
                print("First 10 tickers:")
                for item in data['result']['list']:
                    print(item['symbol'])
            else:
                print(f"Error: {data}")

if __name__ == "__main__":
    asyncio.run(main())
