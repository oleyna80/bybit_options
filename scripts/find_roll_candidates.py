
import asyncio
import aiohttp
import logging
from datetime import datetime

# Current Position Details
CURRENT_SYMBOL = "BTC-27FEB26-82000-P-USDT"
SIZE = 0.24

async def fetch_ticker(session, symbol):
    url = "https://api.bybit.com/v5/market/tickers"
    params = {"category": "option", "symbol": symbol}
    async with session.get(url, params=params) as resp:
        data = await resp.json()
        if data['retCode'] == 0 and data['result']['list']:
            return data['result']['list'][0]
        return None

async def fetch_chain(session, base_coin="BTC"):
    url = "https://api.bybit.com/v5/market/tickers"
    params = {"category": "option", "baseCoin": base_coin}
    all_tickers = []
    
    # Simple pagination handling if needed, but usually tickers fits in one or few calls? 
    # Bybit API limits. Let's try fetching blindly first.
    # Actually, fetching *all* tickers might be heavy. Let's filter in logic or hope it fits.
    # API limit is usually 50-100? No, tickers endpoint returns many.
    
    async with session.get(url, params=params) as resp:
        data = await resp.json()
        if data['retCode'] == 0:
            return data['result']['list']
    return []

async def main():
    async with aiohttp.ClientSession() as session:
        # 1. Get Price of OLD Put (Buy to Close)
        old_ticker = await fetch_ticker(session, CURRENT_SYMBOL)
        if not old_ticker:
            print("Error fetching current position.")
            return
            
        # Using Ask price because we are Buying to Close
        btc_price = float(old_ticker.get('ask1Price', old_ticker.get('markPrice')))
        spot_price = float(old_ticker.get('underlyingPrice', 84000))
        
        print(f"Current Spot: ${spot_price:,.2f}")
        print(f"CLOSE OLD: {CURRENT_SYMBOL}")
        print(f"  Cost to Buy Back: ${btc_price:.2f} (Ask)")
        
        # 2. Find Candidates (Sell to Open)
        # Looking for Expiry > 27FEB26 (e.g., MAR/APR/JUN)
        # Using Bid price because we are Selling
        print("\nSearching for Roll Candidates (Expiry > Feb 27)...")
        print(f"{'Symbol':<30} | {'Strike':<8} | {'Bid Amount':<10} | {'Net Credit/Debit':<15} | {'Safety (OTM)':<10}")
        print("-" * 90)
        
        tickers = await fetch_chain(session)
        
        candidates = []
        for t in tickers:
            sym = t['symbol']
            # Parse symbol BTC-DDMMMYY-STR-C
            try:
                parts = sym.split('-')
                if parts[-1] == 'USDT': # BTC-27MAR26-80000-P-USDT
                    date_str = parts[1]
                    strike = float(parts[2])
                    kind = parts[3]
                else:
                    continue # Ignore standard inverse for now if using USDT
                
                if kind != 'P': continue
                
                exp_date = datetime.strptime(date_str, "%d%b%y")
                curr_exp = datetime.strptime("27FEB26", "%d%b%y")
                
                if exp_date < curr_exp: continue # Must be same or later
                # We want to see Feb 27 candidates too now
                if strike >= 82000: continue # Must be lower strike (Roll Down)
                
                bid_price = float(t.get('bid1Price', 0))
                if bid_price == 0: continue # No liquidity
                
                net_diff = bid_price - btc_price
                otm_pct = (spot_price - strike) / spot_price * 100
                
                candidates.append({
                    "symbol": sym,
                    "strike": strike,
                    "bid": bid_price,
                    "net": net_diff,
                    "otm": otm_pct,
                    "expiry": date_str
                })
                
            except:
                continue
                
        # Sort by Net Credit (Highest first)
        candidates.sort(key=lambda x: x['net'], reverse=True)
        
        # Filter plausible ones (e.g. not too far OTM if premium is tiny)
        for c in candidates[:15]:
            # Net > -500 (Don't pay more than $500 debit)
            if c['net'] > -1000:
                credit_debit = f"+${c['net']:.2f}" if c['net'] >= 0 else f"-${abs(c['net']):.2f}"
                print(f"{c['symbol']:<30} | ${c['strike']:<7.0f} | ${c['bid']:<9.2f} | {credit_debit:<15} | {c['otm']:.1f}%")

if __name__ == "__main__":
    asyncio.run(main())
