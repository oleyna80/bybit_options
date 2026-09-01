#!/usr/bin/env python3
"""
Verify Delta Impact of Iron Condor Scale Down
"""

# Current State
current_net_delta = -0.0038

# Positions to Close (50% scale down)
# 1. Short Put 63k (0.17 Total -> Close 0.085)
p63_delta_total = 0.0367
p63_close_size_pct = 0.5
delta_remove_put = p63_delta_total * p63_close_size_pct
# Closing Long Delta = Negative Impact on Portfolio
delta_impact_put = -delta_remove_put 

# 2. Call Spread (Short 76k / Long 82k)
# Short 76k (0.22 Total -> Close 0.11)
c76_delta_total = -0.0569
c76_close_size_pct = 0.5
delta_remove_short_call = c76_delta_total * c76_close_size_pct
# Closing Short Negative Delta = Positive Impact
delta_impact_short_call = -delta_remove_short_call

# Long 82k (0.22 Total -> Close 0.11)
c82_delta_total = 0.0198
c82_close_size_pct = 0.5
delta_remove_long_call = c82_delta_total * c82_close_size_pct
# Closing Long Positive Delta = Negative Impact
delta_impact_long_call = -delta_remove_long_call

# Net Call Side Impact
delta_impact_call_side = delta_impact_short_call + delta_impact_long_call

# Total Plan Impact
total_delta_change = delta_impact_put + delta_impact_call_side
new_net_delta = current_net_delta + total_delta_change

print("-" * 60)
print(f"📉 IRON CONDOR SCALE DOWN (50%) - DELTA CHECK")
print("-" * 60)
print(f"Current Net Delta: {current_net_delta:.4f}")
print("-" * 60)

print(f"STEP 1: Close 50% Short Put 63k")
print(f"  - Remove Delta: {delta_remove_put:.4f}")
print(f"  - Portfolio Impact: {delta_impact_put:.4f}")
print(f"  => Intermediate Delta: {current_net_delta + delta_impact_put:.4f} (User's Concern: NEGATIVE)")

print("-" * 60)

print(f"STEP 2: Close 50% Call Spread (Short 76k / Long 82k)")
print(f"  - Close Short Call 76k Impact: {delta_impact_short_call:+.4f}")
print(f"  - Close Long Call 82k Impact: {delta_impact_long_call:+.4f}")
print(f"  - Net Call Side Impact: {delta_impact_call_side:+.4f}")

print("-" * 60)

print(f"FINAL RESULT (Combined)")
print(f"  Put Side Impact:  {delta_impact_put:.4f}")
print(f"  Call Side Impact: {delta_impact_call_side:+.4f}")
print(f"  Net Change:       {total_delta_change:+.4f}")
print(f"  ---------------------------")
print(f"  NEW NET DELTA:    {new_net_delta:.4f}")
print("-" * 60)
if abs(new_net_delta) < 0.01:
    print("✅ PERFECTLY NEUTRAL")
else:
    print("⚠️  DELTA SHIFT")
