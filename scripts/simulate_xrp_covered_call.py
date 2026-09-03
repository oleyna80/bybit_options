
import asyncio
import aiohttp
import math
import logging
from datetime import datetime, timedelta
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Black-Scholes Model ---
def norm_cdf(x):
    """Cumulative distribution function for the standard normal distribution"""
    return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0

def black_scholes_call(S, K, T, r, sigma):
    """
    Calculate Black-Scholes price for a Call Option.
    
    S: Current Stock Price
    K: Strike Price
    T: Time to Expiry (in years)
    r: Risk-free interest rate
    sigma: Volatility (annualized)
    """
    if T <= 0:
        return max(S - K, 0.0)
    
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    
    call_price = S * norm_cdf(d1) - K * math.exp(-r * T) * norm_cdf(d2)
    return call_price

def calculate_yield(premium, spot_price):
    return (premium / spot_price) * 100

def get_annualized_yield(yield_pct, days):
    return yield_pct * (365 / days)

# --- Data Fetching ---
async def fetch_kline_data(symbol="XRPUSDT", interval="D", limit=90):
    url = "https://api.bybit.com/v5/market/kline"
    params = {
        "category": "linear",
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            data = await resp.json()
            if data['retCode'] == 0:
                return data['result']['list']
            else:
                logger.error(f"Error fetching kline: {data}")
                return []

async def get_current_price(symbol="XRPUSDT"):
    url = "https://api.bybit.com/v5/market/tickers"
    params = {
        "category": "linear",
        "symbol": symbol
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            data = await resp.json()
            if data['retCode'] == 0:
                return float(data['result']['list'][0]['lastPrice'])
            else:
                logger.error(f"Error fetching ticker: {data}")
                return 0.0

# --- Volatility Calculation ---
def calculate_hv(klines, window=30):
    """
    Calculate annualized Historical Volatility.
    klines: List of [startTime, open, high, low, close, volume, ...]
    """
    # Extract closes (klines are usually returned in reverse chronological order, so we reverse them back)
    # Bybit: [time, open, high, low, close, ...]
    closes = [float(k[4]) for k in klines]
    closes = closes[::-1] # Reverse to chronological order (oldest first)
    
    if len(closes) < window + 1:
        logger.warning("Not enough data for HV")
        return 0.0
    
    # Use last `window` periods
    recent_closes = np.array(closes[-(window + 1):])
    
    # Log returns
    log_returns = np.log(recent_closes[1:] / recent_closes[:-1])
    
    # Standard deviation
    std = np.std(log_returns)
    
    # Annualize (Crypto 365 days)
    hv = std * math.sqrt(365)
    
    return hv

# --- Simulation ---
async def main():
    symbol = "XRPUSDT"
    logger.info(f"Starting Covered Call Simulation for {symbol}...")
    
    # 1. Get Data
    price = await get_current_price(symbol)
    klines = await fetch_kline_data(symbol, "D", 90)
    
    if price == 0 or not klines:
        logger.error("Failed to fetch necessary data.")
        return

    # 2. Calculate Volatility
    hv_30 = calculate_hv(klines, 30)
    hv_7 = calculate_hv(klines, 7)
    
    logger.info(f"Current Price: ${price:.4f}")
    logger.info(f"HV (30-day materialized): {hv_30*100:.2f}%")
    logger.info(f"HV (7-day materialized): {hv_7*100:.2f}%")
    
    # Use HV 30 as proxy for IV
    vol_scenarios = [
        ("Conservative (HV30)", hv_30),
        ("Optimistic (HV30 * 1.2)", hv_30 * 1.2)
    ]
    
    # Params
    risk_free_rate = 0.05 # 5% risk free rate estimate
    
    print("\n" + "="*80)
    print(f"XRP COVERED CALL STRATEGY MODEL")
    print(f"Spot Price: ${price:.4f}")
    print("="*80)
    
    selected_strategy = None # To store 30d 5% OTM for detail view

    for vol_name, vol in vol_scenarios:
        print(f"\n--- Scenario: {vol_name} (Vol: {vol*100:.2f}%) ---")
        print(f"{'Structure':<20} | {'Strike':<10} | {'Premium':<10} | {'Yield %':<10} | {'Ann. Yield %':<13} | {'Max Profit %':<13} | {'Breakeven':<10}")
        print("-" * 110)
        
        # Strategies: Weekly (7d), Bi-Weekly (14d), Monthly (30d)
        expiries = [7, 14, 30]
        strikes_pct = [1.02, 1.05, 1.10] # 2%, 5%, 10% OTM
        
        for days in expiries:
            T = days / 365.0
            for strike_mul in strikes_pct:
                strike = price * strike_mul
                
                # Calculate Option Price
                premium = black_scholes_call(price, strike, T, risk_free_rate, vol)
                
                # Metrics
                yield_pct = calculate_yield(premium, price)
                ann_yield = get_annualized_yield(yield_pct, days)
                
                # Max Profit = (Strike - Spot) + Premium
                max_profit_abs = (strike - price) + premium
                max_profit_pct = (max_profit_abs / price) * 100
                
                breakeven = price - premium
                
                structure_name = f"{days} Days / +{int((strike_mul-1)*100)}% OTM"
                
                # Store specific strategy for detailed analysis (using Conservative volatility)
                if days == 30 and abs(strike_mul - 1.05) < 0.01 and "Conservative" in vol_name:
                     selected_strategy = {
                         "days": days, "strike": strike, "premium": premium, 
                         "breakeven": breakeven, "spot": price
                     }

                print(f"{structure_name:<20} | ${strike:<9.4f} | ${premium:<9.4f} | {yield_pct:<9.2f}% | {ann_yield:<12.2f}% | {max_profit_pct:<12.2f}% | ${breakeven:<9.4f}")

    if selected_strategy:
        s = selected_strategy
        print(f"\n\n--- Detailed Payoff Matrix: {s['days']} Days / +5% OTM (Conservative Vol) ---")
        print(f"Strike: ${s['strike']:.4f} | Premium: ${s['premium']:.4f} | Breakeven: ${s['breakeven']:.4f}")
        print("-" * 75)
        print(f"{'Price at Expiry':<17} | {'Strategy Value':<17} | {'PnL ($)':<12} | {'PnL (%)':<10}")
        print("-" * 75)
        
        # Simulating price moves from -20% to +20%
        moves = [-0.20, -0.10, -0.05, 0.0, 0.02, 0.05, 0.10, 0.20]
        for move in moves:
            p_expiry = s['spot'] * (1 + move)
            
            # Value of stock leg
            stock_val = p_expiry
            
            # Covered Call Value at Expiry = min(Spot, Strike) + Premium (held as cash)
            # Strategy PnL = (Final Value) - (Initial Cost)
            # Initial Cost = Spot Price
            
            final_portfolio_val = min(p_expiry, s['strike']) + s['premium']
            pnl = final_portfolio_val - s['spot'] # Compare to holding stock which cost 'spot'
            pnl_pct = (pnl / s['spot']) * 100
            
            print(f"${p_expiry:<16.4f} | ${final_portfolio_val:<16.4f} | ${pnl:<11.4f} | {pnl_pct:<9.2f}%")

if __name__ == "__main__":
    asyncio.run(main())
