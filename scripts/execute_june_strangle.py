#!/usr/bin/env python3
"""
Script to Execute "June Strangle" Strategy (Vega Hedge).
Default: Dry Run (No Orders Placed).
Use --live to execute.
"""

import asyncio
import json
import os
import sys
import argparse
from typing import Dict, Any

from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bybit_options.services.bybit_connector import BybitConnector

# --- CONFIGURATION ---
TARGET_EXPIRY = "26JUN26"
STRATEGY_LEGS = [
    {"strike": 100000, "type": "C", "size": 0.02},  # Buy Call
    {"strike": 80000, "type": "P", "size": 0.02},   # Buy Put
]
BASE_COIN = "BTC"
# ---------------------

async def fetch_ticker_data(connector: BybitConnector, symbol: str) -> Dict[str, float]:
    """Fetch current Best Bid and Ask."""
    tickers = await connector.get_tickers(category="option", symbol=symbol)
    if not tickers:
        raise ValueError(f"No ticker found for {symbol}")
    
    ticker = tickers[0]
    bid = float(ticker.get("bid1Price", 0))
    ask = float(ticker.get("ask1Price", 0))
    
    return {"bid": bid, "ask": ask}

async def execute_strategy(live_mode: bool):
    load_dotenv()
    api_key = os.getenv("BYBIT_API_KEY")
    api_secret = os.getenv("BYBIT_API_SECRET")
    
    TICK_SIZE = 5.0  # From instrument info
    
    if not api_key or not api_secret:
        print("[ERROR] Missing credentials in .env")
        return

    print(f"--- JUNE STRANGLE EXECUTOR ({'LIVE' if live_mode else 'DRY RUN'}) ---")
    print(f"Logic: MAKER (Best Bid + {TICK_SIZE} USD)")
    
    async with BybitConnector(api_key, api_secret) as connector:
        plan = {"legs": [], "total_cost": 0.0, "status": "Ready"}
        
        # 1. Prepare Plan
        for leg in STRATEGY_LEGS:
            symbol = f"{BASE_COIN}-{TARGET_EXPIRY}-{leg['strike']}-{leg['type']}-USDT"
            
            try:
                data = await fetch_ticker_data(connector, symbol)
                best_bid = data["bid"]
                best_ask = data["ask"]
                
                # Maker Logic: Best Bid + 1 Tick
                target_price = best_bid + TICK_SIZE
                
                # Sanity Check: Ensure we don't cross spread too much (should be < Ask)
                # If target >= Ask, we are Taker.
                is_taker = target_price >= best_ask
                
                cost = target_price * leg["size"]
                
                plan["legs"].append({
                    "symbol": symbol,
                    "action": "BUY",
                    "size": leg["size"],
                    "best_bid": best_bid,
                    "best_ask": best_ask,
                    "limit_price": target_price,
                    "is_taker": is_taker,
                    "est_cost": cost
                })
                plan["total_cost"] += cost
                
            except Exception as e:
                print(f"[ERROR] Failed to price {symbol}: {e}")
                return

        # 2. Review Plan
        print(json.dumps(plan, indent=2))
        
        if not live_mode:
            print("\n[INFO] Action Skipped (Dry Run). Use --live to execute.")
            return

        # 3. Execute (If Live)
        print("\n[WARN] EXECUTING ORDERS...")
        results = []
        for leg_plan in plan["legs"]:
            try:
                print(f"Placing LIMIT BUY for {leg_plan['symbol']} @ {leg_plan['limit_price']}...")
                order = await connector.place_order(
                    category="option",
                    symbol=leg_plan["symbol"],
                    side="Buy",
                    order_type="Limit",
                    qty=str(leg_plan["size"]),
                    price=str(leg_plan["limit_price"])
                )
                print(f"[SUCCESS] Order ID: {order.get('orderId')}")
                results.append(order)
            except Exception as e:
                print(f"[FAIL] Order failed: {e}")
        
        print("\nAll orders processed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Execute June Strangle Strategy")
    parser.add_argument("--live", action="store_true", help="Enable Real Execution")
    args = parser.parse_args()
    
    asyncio.run(execute_strategy(args.live))
