import asyncio
import os
import sys
import argparse
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bybit_options.services.bybit_connector import BybitConnector

async def main(order_id: str):
    load_dotenv()
    api_key = os.getenv("BYBIT_API_KEY")
    api_secret = os.getenv("BYBIT_API_SECRET")
    
    async with BybitConnector(api_key, api_secret) as connector:
        # We don't know category/symbol? 
        # Check logic: cancel_order needs category and symbol.
        # But V5 might support cancelling by orderId only? 
        # API says: category is required. Symbol is required.
        # I know it's "option" and "BTC-26JUN26-80000-P-USDT".
        
        # Hardcoding for this specific cleanup task to avoid arg complexity
        # If made generic, would require args.
        symbol = "BTC-26JUN26-80000-P-USDT"
        print(f"Cancelling {order_id} for {symbol}...")
        
        try:
            res = await connector.cancel_order(category="option", symbol=symbol, order_id=order_id)
            print(f"Result: {res}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("order_id", help="Order ID to cancel")
    args = parser.parse_args()
    asyncio.run(main(args.order_id))
