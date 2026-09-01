
import math

def norm_cdf(x):
    """CDF for standard normal distribution"""
    return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0

def norm_pdf(x):
    """PDF for standard normal distribution"""
    return math.exp(-0.5 * x**2) / math.sqrt(2.0 * math.pi)

def black_scholes_call(S, K, T, r, sigma):
    """Black-Scholes Call Price"""
    if T <= 0:
        return max(S - K, 0.0)
    
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    
    return S * norm_cdf(d1) - K * math.exp(-r * T) * norm_cdf(d2)

def implied_volatility(price, S, K, T, r):
    """Solve for IV given Option Price"""
    sigma = 0.5 # Initial guess
    for i in range(20):
        val = black_scholes_call(S, K, T, r, sigma)
        diff = price - val
        if abs(diff) < 1e-4:
            return sigma
        
        # Vega
        d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        vega = S * norm_pdf(d1) * math.sqrt(T)
        
        if vega == 0:
            break
            
        sigma = sigma + diff/vega
    return sigma

def main():
    # Initial Conditions (from previous step)
    spot_0 = 83078.3
    strike_0 = 87000.0
    days_0 = 14
    premium_0_total = 102.0 # for 0.1 BTC
    size = 0.1
    
    # Premium per 1 BTC for calculation
    premium_0 = premium_0_total / size # 1020
    
    r = 0.05
    T_0 = days_0 / 365.0
    
    # 1. Back-solve IV
    iv = implied_volatility(premium_0, spot_0, strike_0, T_0, r)
    print(f"Initial Setup:")
    print(f"Spot: ${spot_0:,.2f} | Strike: ${strike_0:,.0f} | Days: {days_0}")
    print(f"Premium Received: ${premium_0_total:.2f} (IV: {iv*100:.1f}%)")
    
    # 2. Scenario: Market Crashes 10% in 3 days
    drop_pct = 0.10
    spot_1 = spot_0 * (1 - drop_pct)
    days_passed = 3
    days_1 = days_0 - days_passed
    T_1 = days_1 / 365.0
    
    # Assume IV increases in crash (skew)
    iv_crash = iv * 1.2 
    
    print("\n" + "="*60)
    print(f"SCENARIO: Market Drops {drop_pct*100:.0f}% in {days_passed} days")
    print(f"New Spot: ${spot_1:,.2f} (IV spike to {iv_crash*100:.1f}%)")
    print("="*60)
    
    # Value of Old Call
    price_old_call = black_scholes_call(spot_1, strike_0, T_1, r, iv_crash)
    buyback_cost = price_old_call * size
    
    print(f"1. Close Old Call (Strike ${strike_0:,.0f})")
    print(f"   Value: ${price_old_call:.2f} per BTC")
    print(f"   Cost to Buy Back: -${buyback_cost:.2f}")
    print(f"   Realized Profit on Option: ${premium_0_total - buyback_cost:.2f}")
    
    # 3. Roll Down Strategy
    # Sell New Call at +5% OTM from NEW spot
    target_strike = spot_1 * 1.05
    # Round to nearest 500
    new_strike = round(target_strike / 500) * 500
    
    # New Expiry: Roll out back to 14 days (add time) or kept at 11 days?
    # Usually roll out in time to collect more premium. 
    # Let's say we roll to a new 14-day expiry (add 3 days back).
    days_new = 14
    T_new = days_new / 365.0
    
    price_new_call = black_scholes_call(spot_1, new_strike, T_new, r, iv_crash)
    new_credit = price_new_call * size
    
    print(f"\n2. Roll Down & Out")
    print(f"   Sell New Call: Strike ${new_strike:,.0f} (Exp: {days_new} days)")
    print(f"   New Premium: +${new_credit:.2f}")
    
    # Summary
    total_credit = (premium_0_total - buyback_cost) + new_credit
    spot_loss = (spot_0 - spot_1) * size
    
    print("\n" + "-"*60)
    print("NET RESULT OF ADJUSTMENT")
    print("-"*60)
    print(f"Total Option Credits Collected: ${total_credit:.2f}")
    print(f"Original Breakeven: ${spot_0 - premium_0_total/size:,.2f}")
    print(f"New Breakeven (Adjusted): ${spot_0 - total_credit/size:,.2f}")
    print("-" * 60)
    print(f"Unrealized Loss on BTC: -${spot_loss:.2f}")
    print(f"Net Position Value (vs holding BTC): +${total_credit:.2f} buffer")

if __name__ == "__main__":
    main()
