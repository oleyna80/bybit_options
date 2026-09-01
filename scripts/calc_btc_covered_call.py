
import asyncio
import aiohttp
import logging
from datetime import datetime
import re
from typing import List, Dict, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
BASE_COIN = "BTC"
POSITION_SIZE = 0.1 # BTC

async def fetch_btc_price() -> float:
    url = "https://api.bybit.com/v5/market/tickers"
    params = {
        "category": "linear",
        "symbol": f"{BASE_COIN}USDT"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            data = await resp.json()
            if data['retCode'] == 0:
                return float(data['result']['list'][0]['lastPrice'])
            return 0.0

async def fetch_option_tickers() -> List[Dict]:
    """Fetch all BTC option tickers"""
    url = "https://api.bybit.com/v5/market/tickers"
    params = {
        "category": "option",
        "baseCoin": BASE_COIN,
        "limit": 1000 # Should cover most active series
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            data = await resp.json()
            if data['retCode'] == 0:
                return data['result']['list']
            logger.error(f"Error fetching options: {data}")
            return []

def parse_option_symbol(symbol: str):
    # Format: BTC-DDMMMYY-STRIKE-C-USDT or similar
    # Example: BTC-30JAN26-100000-C
    # Example: BTC-1FEB26-90500-C-USDT
    try:
        parts = symbol.split('-')
        
        # Depending on format, it might have 4 or 5 parts
        # If 5 parts and last is USDT, ignore it
        if len(parts) >= 4:
            coin = parts[0]
            date_str = parts[1]
            strike_str = parts[2]
            type_str = parts[3]
            
            if type_str != 'C': # We only want Calls
                return None
                
            strike = float(strike_str)
            expiry_date = datetime.strptime(date_str, "%d%b%y")
            
            return {
                "symbol": symbol,
                "expiry": expiry_date,
                "strike": strike
            }
        return None
    except Exception as e:
        # logger.warning(f"Failed to parse {symbol}: {e}")
        return None

async def main():
    logger.info(f"Fetching data for {BASE_COIN} Covered Call (Size: {POSITION_SIZE} {BASE_COIN})...")
    
    # 1. Get Spot Price
    spot_price = await fetch_btc_price()
    if spot_price == 0:
        logger.error("Failed to fetch spot price.")
        return
        
    logger.info(f"Current Spot Price: ${spot_price:,.2f}")
    
    # 2. Get Option Tickers
    tickers = await fetch_option_tickers()
    logger.info(f"Fetched {len(tickers)} option tickers.")
    
    # Process Tickers
    options = []
    now = datetime.now()
    
    for t in tickers:
        meta = parse_option_symbol(t['symbol'])
        if not meta:
            continue
            
        # Enrich with ticker data
        meta['bid1Price'] = float(t.get('bid1Price', 0)) # Buying price (if we sell)? No, if we sell we sell to the Bid.
        meta['ask1Price'] = float(t.get('ask1Price', 0))
        meta['markPrice'] = float(t.get('markPrice', 0))
        
        # Calculate Time to Expiry (days)
        delta = meta['expiry'] - now
        meta['days_to_expiry'] = delta.days + (delta.seconds / 86400)
        
        if meta['days_to_expiry'] < 0.5: # Ignore expiring today/very soon
            continue
            
        options.append(meta)
        
    # Group by relevant expiries
    # Target: ~7 days, ~14 days, ~30 days
    targets = [7, 14, 30]
    
    # Find unique expiry dates and sort them
    unique_dates = sorted(list(set([o['expiry'] for o in options])))
    
    selected_expiries = []
    
    for target in targets:
        # Find closest date
        closest_date = min(unique_dates, key=lambda d: abs(((d - now).days) - target))
        if closest_date not in selected_expiries:
            selected_expiries.append(closest_date)
            
    # Display Table
    print("\n" + "="*120)
    print(f"BTC COVERED CALL STRATEGY (Real Market Data) - Size: {POSITION_SIZE} BTC")
    print(f"Spot Price: ${spot_price:,.2f} | Position Value: ${spot_price * POSITION_SIZE:,.2f}")
    print("="*120)
    
    print(f"{'Expiry':<12} | {'Days':<5} | {'Strike':<10} | {'% OTM':<8} | {'Bid':<10} | {'Mark':<10} | {'Premium ($)':<12} | {'Yield':<8} | {'Ann. Yield':<10} | {'Max Profit':<12}")
    print("-" * 120)
    
    for expiry in selected_expiries:
        days = (expiry - now).days + 1 # Approximate
        
        # Filter options for this expiry
        expiry_options = [o for o in options if o['expiry'] == expiry]
        
        # Sort by strike
        expiry_options.sort(key=lambda x: x['strike'])
        
        # Find targets: +2%, +5%, +10% OTM, +20% OTM
        target_pcts = [1.02, 1.05, 1.10, 1.20]
        
        for pct in target_pcts:
            target_strike = spot_price * pct
            
            # Find closest strike
            closest = min(expiry_options, key=lambda x: abs(x['strike'] - target_strike))
            
            strike = closest['strike']
            real_otm = ((strike - spot_price) / spot_price) * 100
            
            # Use Bid price for conservative "Selling" estimate. 
            # If Bid is 0 (illiquid), fall back to Mark Price but flag it.
            price_to_use = closest['bid1Price']
            price_source = "Bid"
            if price_to_use == 0:
                price_to_use = closest['markPrice']
                price_source = "Mark"
                
            total_premium = price_to_use * POSITION_SIZE
            yield_pct = (price_to_use / spot_price) * 100
            ann_yield = yield_pct * (365 / days)
            
            max_profit_qty = (strike - spot_price) * POSITION_SIZE + total_premium
            max_profit_pct = (max_profit_qty / (spot_price * POSITION_SIZE)) * 100
            
            expiry_str = expiry.strftime("%d-%b")
            
            print(f"{expiry_str:<12} | {days:<5} | ${strike:<9.0f} | {real_otm:<7.1f}% | ${closest['bid1Price']:<9.2f} | ${closest['markPrice']:<9.2f} | ${total_premium:<11.2f} | {yield_pct:<7.2f}% | {ann_yield:<9.1f}% | ${max_profit_qty:<10.2f} ({max_profit_pct:.1f}%)")

if __name__ == "__main__":
    asyncio.run(main())
