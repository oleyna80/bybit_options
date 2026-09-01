#!/usr/bin/env python3
"""
Gamma Solver
"""

# Current Portfolio Greeks
net_gamma = -0.000010
net_delta = -0.0038
net_theta = 23.36

# Position Data (from report)
# Format: Symbol, Side, Size, Delta, Gamma, Theta, Price (Approx)
positions = [
    # Short Put 63k
    {'id': 'put_63k', 'side': 'short', 'size': 0.17, 'delta': 0.0367, 'gamma': -0.000005, 'theta': 12.8, 'price': 1374},
    # Short Call 76k
    {'id': 'call_76k', 'side': 'short', 'size': 0.22, 'delta': -0.0569, 'gamma': -0.000009, 'theta': 13.9, 'price': 1100},
    # Long Call 82k (Hedge for 76k)
    {'id': 'call_82k', 'side': 'long',  'size': 0.22, 'delta': 0.0198,  'gamma': 0.000005,  'theta': -6.8, 'price': 396},
     # Short Put 58k (Reference for rolling)
    {'id': 'put_58k', 'side': 'short', 'size': 0.2, 'delta': 0.0234, 'gamma': -0.000003, 'theta': 11.5, 'price': 1335}
]

print(f"Current Net Gamma: {net_gamma:.6f}")
print(f"Target Net Gamma: > -0.000005")
print("-" * 60)

# SCENARIO 1: Close Short Put 63k (0.17)
# Impact: Remove 0.17 of Put 63k
p63 = positions[0]
s1_gamma_change = -p63['gamma'] # Removing negative gamma = adding positive
s1_delta_change = -p63['delta'] # Removing positive delta = adding negative
s1_theta_change = -p63['theta'] # Removing positive theta = adding negative (bad)
s1_cost = p63['size'] * p63['price']

print(f"SCENARIO 1: Close Short Put 63k")
print(f"  Gamma Change: {s1_gamma_change:+.6f} -> New Net: {net_gamma + s1_gamma_change:.6f} [{'✅' if (net_gamma + s1_gamma_change) > -0.000005 else '❌'}]")
print(f"  Delta Change: {s1_delta_change:+.4f} -> New Net: {net_delta + s1_delta_change:.4f}")
print(f"  Theta Change: {s1_theta_change:+.2f} -> New Net: {net_theta + s1_theta_change:.2f}")
print(f"  Cost: ${s1_cost:.2f}")

# SCENARIO 2: Close Call Spread (Short 76k + Long 82k)
# Impact: Remove 0.22 of Short 76k AND Remove 0.22 of Long 82k
c76 = positions[1]
c82 = positions[2]
s2_gamma_change = -c76['gamma'] - c82['gamma']
s2_delta_change = -c76['delta'] - c82['delta']
s2_theta_change = -c76['theta'] - c82['theta']
s2_cost_close_short = c76['size'] * c76['price']
s2_credit_close_long = c82['size'] * c82['price']
s2_net_cost = s2_cost_close_short - s2_credit_close_long

print(f"\nSCENARIO 2: Close Call Spread (76k/82k)")
print(f"  Gamma Change: {s2_gamma_change:+.6f} -> New Net: {net_gamma + s2_gamma_change:.6f} [{'✅' if (net_gamma + s2_gamma_change) > -0.000005 else '❌'}]")
print(f"  Delta Change: {s2_delta_change:+.4f} -> New Net: {net_delta + s2_delta_change:.4f}")
print(f"  Theta Change: {s2_theta_change:+.2f} -> New Net: {net_theta + s2_theta_change:.2f}")
print(f"  Cost: ${s2_net_cost:.2f}")

# SCENARIO 3: Calendar Roll (Close Put 63k, Sell Put 58k)
# Roll Put 63k (Gamma -0.000005/0.17 size = -2.9e-5 per 1.0) -> Put 58k (Gamma -0.000003/0.2 size = -1.5e-5 per 1.0)
# We assume unit gamma for 58k is roughly 0.000003 / 0.2 = 0.000015
# Actually we have the total gamma positions.
# Logic: Close 0.17 Short Put 63k. Open 0.17 Short Put 58k.
p58 = positions[3]
# Approximate unit stats for 58k
p58_unit_gamma = p58['gamma']
# Wait, p58['gamma'] in the list IS the total gamma for 0.2 size. 
# So unit gamma = -0.000003. Oh wait, previous report says "Gamma: -0.000003" for 0.2 size.
# Let's trust the 'gamma' value is the total contribution to portfolio.
# Close 63k: +0.000005
# Open 0.17 of 58k. 
# 0.20 size gives -0.000003. So 0.17 size gives (-0.000003 / 0.20) * 0.17 = -0.00000255.
s3_gamma_close = -p63['gamma'] # +0.000005
s3_gamma_open = (p58['gamma'] / 0.20) * 0.17 # approx -0.00000255
s3_net_gamma = s3_gamma_close + s3_gamma_open

s3_delta_close = -p63['delta'] # -0.0367
s3_delta_open = (p58['delta'] / 0.20) * 0.17 # +0.0234/0.2 * 0.17 = +0.0199
s3_net_delta = s3_delta_close + s3_delta_open

s3_theta_close = -p63['theta'] # -12.8
s3_theta_open = (p58['theta'] / 0.20) * 0.17 # +11.5/0.2 * 0.17 = +9.77
s3_net_theta = s3_theta_close + s3_theta_open

# Cost?
# Close 63k @ 1374. Open 58k? 
# 58k P price is 1335 for 0.2 size? NO. Mark price is per unit.
# Report: BTC-27FEB26-58000-P-USDT (K=58000) Mark 1335.
# Report: BTC-27FEB26-63000-P-USDT (K=63000) Mark 1374.
# Close 63k: Buy @ 1374. 
# Open 58k: Sell @ 1335.
# Debit: 1374 - 1335 = $39 per BTC.
# Total Debit: 39 * 0.17 = $6.63.
s3_cost = (p63['price'] - p58['price']) * 0.17

print(f"\nSCENARIO 3: Roll Put 63k Down to 58k")
print(f"  Gamma Change: {s3_net_gamma:+.6f} -> New Net: {net_gamma + s3_net_gamma:.6f} [{'✅' if (net_gamma + s3_net_gamma) > -0.000005 else '❌'}]")
print(f"  Delta Change: {s3_net_delta:+.4f} -> New Net: {net_delta + s3_net_delta:.4f}")
print(f"  Theta Change: {s3_net_theta:+.2f} -> New Net: {net_theta + s3_net_theta:.2f}")
print(f"  Cost: ${s3_cost:.2f}")

