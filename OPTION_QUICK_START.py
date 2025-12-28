#!/usr/bin/env python3
"""
QUICK START: BTC Options Market Data
Use this cheat sheet for fast access to option quotes

⚡ ONE-LINER COMMANDS:
"""

# Get current price of a put option
# python get_option_quotes.py BTC-19DEC25-82000-P

# Get current price of a call option  
# python get_option_quotes.py BTC-19DEC25-89000-C

# Compare multiple strikes (puts)
# python get_option_quotes.py BTC-19DEC25-80000-P BTC-19DEC25-82000-P BTC-19DEC25-84000-P

# Compare multiple strikes (calls)
# python get_option_quotes.py BTC-19DEC25-87000-C BTC-19DEC25-89000-C BTC-19DEC25-91000-C

# Get JSON output for analysis
# python get_option_quotes_json.py BTC-19DEC25-82000-P BTC-19DEC25-89000-C

# Save to file
# python get_option_quotes_json.py BTC-19DEC25-82000-P > my_quotes.json

"""
📊 HOW TO READ THE OUTPUT:

PRICES:
├─ Mark: Fair value (what you pay/get on average)
├─ Bid: Price you get if you SELL now
├─ Ask: Price you PAY if you BUY now  
└─ Spread: Difference = Your slippage cost

VOLATILITY (IV):
├─ Bid IV: IV at bid price
├─ Mark IV: IV at fair value ← USE THIS
└─ Ask IV: IV at ask price
   Higher IV = More expensive to buy, better to sell

GREEKS (Risk Metrics):
├─ Delta: How much price changes with $1 BTC move
│  Put: -1 to 0 (negative = protect against rises)
│  Call: 0 to 1 (positive = profit from rises)
├─ Gamma: How fast delta changes (0.00006 = changes a lot)
├─ Vega: Price change from IV +1% (+25 = +$25 if IV up 1%)
└─ Theta: Time decay per day (-175 = costs $175/day to hold)

LIQUIDITY:
├─ Bid Size / Ask Size: How many contracts available
├─ OI: Total open interest (higher = liquid)
├─ Spread %: <1% great, <5% ok, >5% risky
└─ Volume 24h: Daily trading activity

💡 TRADING INSIGHTS:

FOR BUYING PROTECTIVE PUTS (Hedge):
  1. Check Spread % (want <2%)
  2. Check IV (high = expensive, wait for pullback)
  3. Check Theta (high negative = decaying fast)
  4. Check OI (want >20 for liquidity)
  Example: python get_option_quotes.py BTC-19DEC25-82000-P

FOR SELLING CALLS (Premium):
  1. Check IV (high = good time to sell)
  2. Check OI (want >20)
  3. Check Bid Size (enough buyers?)
  4. Check Delta (how likely to expire ITM?)
  Example: python get_option_quotes.py BTC-19DEC25-89000-C

FOR COMPARING STRIKES:
  1. Put strikes (80k, 82k, 84k) - find best bang for buck
  2. Call strikes (87k, 89k, 91k) - compare premiums
  Example: python get_option_quotes.py BTC-19DEC25-82000-P BTC-19DEC25-84000-P

⚠️  CURRENT STATUS (15 DEC 2025):
  • 19DEC25 expires in 4 DAYS - URGENT positions!
  • 26DEC25 expires in 11 days
  • Current BTC ≈ $86,000
  • 82k put = at risk (8k below current)
  • 89k call = OTM safe (3k above current)

🚀 RECOMMENDED CHECKS:

Morning (Plan your day):
  python get_option_quotes.py BTC-19DEC25-82000-P BTC-19DEC25-84000-P

Before entering position:
  python get_option_quotes.py [YOUR_SYMBOL]

Monitor expiry dates:
  # Need to check 19DEC25 positions urgently!
  python get_option_quotes.py BTC-19DEC25-82000-P BTC-19DEC25-84000-P BTC-19DEC25-86000-P

Export for analysis:
  python get_option_quotes_json.py BTC-19DEC25-82000-P > analysis.json

═══════════════════════════════════════════════════════════════

SYMBOL FORMAT:
  BTC-DDMMMYY-STRIKE-TYPE[-USDT]
  
  Examples:
  ✓ BTC-19DEC25-82000-P      (19 Dec, Put, 82k strike)
  ✓ BTC-19DEC25-89000-C      (19 Dec, Call, 89k strike)
  ✓ BTC-26DEC25-75000-P      (26 Dec, Put, 75k strike)

═══════════════════════════════════════════════════════════════

QUICK REFERENCE - WHAT NUMBERS MEAN:

Delta: -0.18 (Put)
  → If BTC drops $100, option gains ~$18

Gamma: 0.000056
  → Delta changes by 0.0056 per $100 move (very small = stable)

Vega: +21.56
  → If IV goes from 55% to 56%, option gains $21.56

Theta: -175.27
  → Costs $175/day to hold (time decay)

IV: 55.34%
  → Annualized expected volatility (realized vs this = opportunity)

Spread: 1.11%
  → Your cost to enter/exit position (want <2%)

═══════════════════════════════════════════════════════════════
"""

# Quick calculator: What's my max loss on a put?
def put_max_loss(strike, premium_paid):
    """Max loss = Premium paid (option expires worthless)"""
    return premium_paid

def put_max_gain(strike, premium_paid):
    """Max gain = Strike - Premium (if BTC goes to 0)"""
    return strike - premium_paid

def call_max_loss(strike, premium_paid):
    """Max loss = Premium paid (if BTC stays below strike)"""
    return premium_paid

def call_max_gain(strike, premium_paid):
    """Max gain = Unlimited (theoretically)"""
    return "Unlimited"

# Example:
# Put 82k, you pay $445:
#   Max loss = $445 (if BTC bounces back above 82k)
#   Max gain = 82000 - 445 = $81,555 (if BTC crashes)
#
# Call 89k, you pay $560:
#   Max loss = $560 (if BTC stays below 89k)
#   Max gain = Unlimited (if BTC goes to moon)

print(__doc__)
