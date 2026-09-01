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
        # Check Call
        call_symbol = "BTC-26JUN26-100000-C-USDT"
        orders_call = await connector.get_realtime_orders(category="option", symbol=call_symbol)
        
        # Check Put
        put_symbol = "BTC-26JUN26-80000-P-USDT"
        orders_put = await connector.get_realtime_orders(category="option", symbol=put_symbol)
        
        all_orders = orders_call + orders_put
        
        if not all_orders:
            print("No active orders found.")
        else:
            print(f"Found {len(all_orders)} active orders:")
            for o in all_orders:
                print(f"- [{o['orderId']}] {o['symbol']} {o['side']} {o['qty']} @ {o['price']} (Status: {o['orderStatus']})")

if __name__ == "__main__":
    asyncio.run(main())
