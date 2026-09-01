#!/usr/bin/env python3
"""
Advanced Order Chasing Script (Vega-Capped).
Logic:
1. Start @ Best Bid + 1 Tick.
2. Loop every 30s check.
3. If unfilled > 5 mins -> Amend Price + 1 Tick.
4. Max Price Cap = Mark Price + (Vega * 0.2).
"""

import asyncio
import os
import sys
import time
import argparse
import uuid
from typing import Dict, Any, Optional

from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bybit_options.services.bybit_connector import BybitConnector

# --- CONFIGURATION ---
TARGET_EXPIRY = "26JUN26"
STRATEGY_LEGS = [
    {"strike": 100000, "type": "C", "size": 0.02},
    {"strike": 80000, "type": "P", "size": 0.02},
]
BASE_COIN = "BTC"
CHASE_INTERVAL_SEC = 300  # 5 minutes
CHECK_INTERVAL_SEC = 30   # 30 seconds loop
TICK_SIZE = 5.0
VEGA_CAP_RATIO = 0.2
# ---------------------

async def get_market_data(connector: BybitConnector, symbol: str):
    tickers = await connector.get_tickers(category="option", symbol=symbol)
    if not tickers:
        raise ValueError(f"No ticker for {symbol}")
    
    t = tickers[0]
    return {
        "bid": float(t.get("bid1Price", 0)),
        "ask": float(t.get("ask1Price", 0)),
        "mark": float(t.get("markPrice", 0)),
        "vega": float(t.get("vega", 0))
    }

async def manage_leg(connector: BybitConnector, leg: Dict, live_mode: bool):
    symbol = f"{BASE_COIN}-{TARGET_EXPIRY}-{leg['strike']}-{leg['type']}-USDT"
    print(f"\n[START] Managing {symbol} (Size: {leg['size']})")
    
    # 1. Initial Data
    data = await get_market_data(connector, symbol)
    
    # 2. Calculate Cap
    # "Max price + 0.2% from IV" -> interpreted as Price + (Vega * 0.2)
    # Vega is approx change in price per 1% (0.01) IV change? 
    # Actually, Bybit Vega is usually change per 100% vol.
    # WAIT. Step 752: Ask-Bid Spread $75. DeltaIV 0.0038 (0.38%).
    # So 1% IV = $197. Vega from API = 198.
    # So Vega from API IS "Price change per 1% IV".
    # Target: +0.1% IV => Price + (Vega * 0.1)
    
    current_iv_impact = data["vega"] * 0.2  # Cap at +0.2% IV
    max_price_cap = data["mark"] + current_iv_impact
    
    # 3. Initial Price
    # Logic: "Front-run by 0.1% IV"
    iv_premium = data["vega"] * 0.1  # 0.1% IV premium
    target_raw = data["bid"] + iv_premium
    
    # Round to Tick Size
    price = round(target_raw / TICK_SIZE) * TICK_SIZE
    
    # Ensure at least 1 tick above bid
    if price <= data["bid"]:
        price = data["bid"] + TICK_SIZE

    # Sanity: Cap at Ask
    if price > data["ask"]:
        price = data["ask"] - TICK_SIZE
        if price < data["bid"]:
             price = data["bid"]
        
    print(f"  Bid: {data['bid']} | Ask: {data['ask']} | Mark: {data['mark']}")
    print(f"  Vega: {data['vega']} | Max Cap (Mark + 0.2Vega): {max_price_cap:.2f}")
    print(f"  Initial Limit: {price}")
    
    if not live_mode:
        print("  [DRY RUN] Would place order here. Skipping.")
        return

    # 4. Place Initial Order
    try:
        link_id = f"JUNE-CHASE-{uuid.uuid4().hex[:8]}"
        order = await connector.place_order(
            category="option", symbol=symbol, side="Buy",
            order_type="Limit", qty=str(leg["size"]), price=str(price),
            order_link_id=link_id
        )
        order_id = order.get("orderId")
        if not order_id:
            # Fallback if only link_id works
            order_id = order.get("orderLinkId")
            
        print(f"  [ORDER] Placed {order_id} (Link: {link_id}) @ {price}")
    except Exception as e:
        print(f"  [ERROR] Placement failed: {e}")
        return

    # 5. Monitor Loop
    start_time = time.time()
    last_move_time = start_time
    
    while True:
        await asyncio.sleep(CHECK_INTERVAL_SEC)
        
        # Check Status
        orders = await connector.get_realtime_orders(category="option", symbol=symbol, order_id=order_id)
        if not orders:
            print(f"  [DONE] Order {order_id} filled or disappeared.")
            break
            
        status = orders[0]["orderStatus"]
        if status in ("Filled", "Cancelled", "Rejected"):
            print(f"  [DONE] Order {order_id} is {status}.")
            break
            
        # Check Time for Chase
        now = time.time()
        if now - last_move_time >= CHASE_INTERVAL_SEC:
            # Time to move up!
            new_price = price + TICK_SIZE
            
            # Check Cap
            if new_price > max_price_cap:
                print(f"  [HOLD] Reached Cap {max_price_cap:.2f}. Holding @ {price}.")
                # Don't update time, just check status
                continue
                
            print(f"  [CHASE] > 5 min passed. Moving to {new_price}...")
            try:
                await connector.amend_order(category="option", symbol=symbol, order_id=order_id, price=str(new_price))
                price = new_price
                last_move_time = now
                print(f"  [SUCCESS] Amended to {new_price}")
            except Exception as e:
                print(f"  [ERROR] Amend failed: {e}")
                break

async def main(live_mode: bool):
    load_dotenv()
    api_key = os.getenv("BYBIT_API_KEY")
    api_secret = os.getenv("BYBIT_API_SECRET")
    
    async with BybitConnector(api_key, api_secret) as connector:
        tasks = [manage_leg(connector, leg, live_mode) for leg in STRATEGY_LEGS]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="Execute Live")
    args = parser.parse_args()
    asyncio.run(main(args.live))
