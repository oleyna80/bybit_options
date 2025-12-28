import asyncio
import os
from dotenv import load_dotenv
from bybit_connector import BybitConnector

async def test_btc_price():
    load_dotenv()
    api_key = os.getenv("BYBIT_API_KEY")
    api_secret = os.getenv("BYBIT_API_SECRET")
    
    print(f"API Key: {api_key[:5]}...")
    print(f"BYBIT_TESTNET: {os.getenv('BYBIT_TESTNET', 'not set')}")
    
    async with BybitConnector(api_key, api_secret, testnet=False) as connector:
        # Get BTC spot price
        tickers = await connector.get_tickers(category="spot", symbol="BTCUSDT")
        if tickers:
            ticker = tickers[0]
            print(f"BTCUSDT ticker:")
            print(f"  Last price: ${ticker.get('lastPrice')}")
            print(f"  Bid: ${ticker.get('bid1Price')}")
            print(f"  Ask: ${ticker.get('ask1Price')}")
            print(f"  Volume: {ticker.get('volume24h')}")
            print(f"  Timestamp: {ticker.get('timestamp')}")
        else:
            print("No ticker data")
        
        # Also test with testnet=True to compare
        print("\n--- Testing with testnet=True (for comparison) ---")
        async with BybitConnector(api_key, api_secret, testnet=True) as connector_testnet:
            tickers_test = await connector_testnet.get_tickers(category="spot", symbol="BTCUSDT")
            if tickers_test:
                ticker_test = tickers_test[0]
                print(f"Testnet BTCUSDT last price: ${ticker_test.get('lastPrice')}")

if __name__ == "__main__":
    asyncio.run(test_btc_price())