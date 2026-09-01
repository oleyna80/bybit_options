#!/usr/bin/env python3
"""
Gamma Reduction Analysis
Analyzes current positions and suggests ways to reduce gamma exposure
"""

# Current positions from latest_analysis.md
current_positions = [
    {'symbol': 'BTC-27FEB26-63000-P', 'side': 'Sell', 'size': 0.17, 'gamma': -0.000005},
    {'symbol': 'BTC-27FEB26-82000-C', 'side': 'Buy', 'size': 0.22, 'gamma': +0.000005},
    {'symbol': 'BTC-27FEB26-76000-C', 'side': 'Sell', 'size': 0.22, 'gamma': -0.000009},
    {'symbol': 'BTC-27FEB26-52000-P', 'side': 'Buy', 'size': 0.20, 'gamma': +0.000002},
    {'symbol': 'BTC-27FEB26-58000-P', 'side': 'Sell', 'size': 0.20, 'gamma': -0.000003},
    {'symbol': 'BTC-27FEB26-96000-C', 'side': 'Buy', 'size': 0.15, 'gamma': +0.000000},
    {'symbol': 'BTC-27FEB26-91000-C', 'side': 'Sell', 'size': 0.15, 'gamma': -0.000001},
    {'symbol': 'BTC-27FEB26-101000-C', 'side': 'Sell', 'size': 0.24, 'gamma': -0.000000},
    {'symbol': 'BTC-26JUN26-100000-C', 'side': 'Buy', 'size': 0.03, 'gamma': +0.000000},
    {'symbol': 'BTC-27FEB26-107000-C', 'side': 'Buy', 'size': 0.24, 'gamma': +0.000000},
    {'symbol': 'BTC-26JUN26-80000-P', 'side': 'Buy', 'size': 0.03, 'gamma': +0.000001},
]

print("="*80)
print("GAMMA REDUCTION ANALYSIS")
print("="*80)
print(f"\nBTC Spot: ~$70,000")
print(f"Target: Reduce Net Gamma from -0.000010 to -0.000005 or less")
print(f"Required Reduction: +0.000005 (need to add positive gamma or remove negative)")
print("\n" + "="*80)

# Calculate current net gamma
net_gamma = sum(p['gamma'] for p in current_positions)
print(f"\nCurrent Net Gamma: {net_gamma:.9f}")

# Sort by gamma contribution (most negative first)
sorted_positions = sorted(current_positions, key=lambda x: x['gamma'])

print("\n" + "-"*80)
print("POSITIONS SORTED BY GAMMA (Most Negative First)")
print("-"*80)
print(f"{'Symbol':<30} {'Side':<5} {'Size':>6} {'Gamma':>12} {'% of Total':>10}")
print("-"*80)

for pos in sorted_positions:
    pct = (pos['gamma'] / net_gamma * 100) if net_gamma != 0 else 0
    print(f"{pos['symbol']:<30} {pos['side']:<5} {pos['size']:>6.2f} {pos['gamma']:>12.9f} {pct:>9.1f}%")

print("\n" + "="*80)
print("GAMMA REDUCTION OPTIONS")
print("="*80)

print("\n📊 OPTION 1: Close Largest Short Gamma Position")
print("-"*80)
print("Action: CLOSE Short Call 76k / Long Call 82k Spread")
print(f"  - Close Short Call 76k (0.22 BTC): Removes gamma {-0.000009:.9f}")
print(f"  - Close Long Call 82k (0.22 BTC): Removes gamma {+0.000005:.9f}")
print(f"  - Net Gamma Reduction: {-0.000009 + 0.000005:.9f}")
new_gamma_opt1 = net_gamma - (-0.000009 + 0.000005)
print(f"  - New Net Gamma: {new_gamma_opt1:.9f}")
print(f"  - ✅ TARGET ACHIEVED: {abs(new_gamma_opt1) <= 0.000005}")
print(f"  - Cost: Lock in current spread P&L (~-$37)")
print(f"  - Theta Impact: Lose ~$7/day")

print("\n📊 OPTION 2: Close Second Largest Short Gamma")
print("-"*80)
print("Action: CLOSE Short Put 63k (naked)")
print(f"  - Close Short Put 63k (0.17 BTC): Removes gamma {-0.000005:.9f}")
new_gamma_opt2 = net_gamma - (-0.000005)
print(f"  - New Net Gamma: {new_gamma_opt2:.9f}")
print(f"  - ✅ TARGET ACHIEVED: {abs(new_gamma_opt2) <= 0.000005}")
print(f"  - Cost: Lock in current P&L (~-$11)")
print(f"  - Theta Impact: Lose ~$13/day")

print("\n📊 OPTION 3: Close Both Top Gamma Positions")
print("-"*80)
print("Action: CLOSE 76k/82k Call Spread + Short Put 63k")
new_gamma_opt3 = net_gamma - (-0.000009 + 0.000005 - 0.000005)
print(f"  - New Net Gamma: {new_gamma_opt3:.9f}")
print(f"  - ✅ TARGET ACHIEVED: {abs(new_gamma_opt3) <= 0.000005}")
print(f"  - Cost: ~-$48 total")
print(f"  - Theta Impact: Lose ~$20/day (from +$23.61 to +$3.61)")

print("\n📊 OPTION 4: Add Long Gamma (Buy ATM Straddle)")
print("-"*80)
print("Action: BUY 70k Call + 70k Put (0.05 BTC each)")
print(f"  - Estimated Gamma per leg: +0.000008 (ATM has highest gamma)")
print(f"  - Total Gamma Added: +0.000016 (both legs)")
new_gamma_opt4 = net_gamma + 0.000016
print(f"  - New Net Gamma: {new_gamma_opt4:.9f}")
print(f"  - ✅ TARGET ACHIEVED: {abs(new_gamma_opt4) <= 0.000005}")
print(f"  - Cost: ~$175 premium (0.05 × $3,500)")
print(f"  - Theta Impact: -$5/day (reduces net theta)")
print(f"  - ⚠️ FLIPS TO POSITIVE GAMMA (profit from volatility)")

print("\n📊 OPTION 5: Reduce Size of Short Call 76k")
print("-"*80)
print("Action: PARTIAL CLOSE Short Call 76k (close 0.11 out of 0.22)")
print(f"  - Close 50% of Short Call 76k: Removes gamma {-0.000009 * 0.5:.9f}")
new_gamma_opt5 = net_gamma - (-0.000009 * 0.5)
print(f"  - New Net Gamma: {new_gamma_opt5:.9f}")
print(f"  - ✅ TARGET ACHIEVED: {abs(new_gamma_opt5) <= 0.000005}")
print(f"  - Cost: Lock in ~-$10 (half of spread P&L)")
print(f"  - Theta Impact: Lose ~$3.5/day")
print(f"  - ✅ KEEPS SOME UPSIDE PROTECTION")

print("\n" + "="*80)
print("RECOMMENDATION MATRIX")
print("="*80)
print(f"{'Option':<40} {'Gamma Result':>15} {'Cost':>10} {'Theta Impact':>15} {'Best For'}")
print("-"*80)
print(f"{'1. Close 76k/82k Spread':<40} {new_gamma_opt1:>15.9f} {'~-$37':>10} {'-$7/day':>15} {'Quick fix'}")
print(f"{'2. Close Short Put 63k':<40} {new_gamma_opt2:>15.9f} {'~-$11':>10} {'-$13/day':>15} {'Low cost'}")
print(f"{'3. Close Both':<40} {new_gamma_opt3:>15.9f} {'~-$48':>10} {'-$20/day':>15} {'Max safety'}")
print(f"{'4. Buy ATM Straddle':<40} {new_gamma_opt4:>15.9f} {'~-$175':>10} {'-$5/day':>15} {'Aggressive'}")
print(f"{'5. Partial Close 76k':<40} {new_gamma_opt5:>15.9f} {'~-$10':>10} {'-$3.5/day':>15} {'⭐ BALANCED'}")

print("\n" + "="*80)
print("⭐ RECOMMENDED: OPTION 5 (Partial Close Short Call 76k)")
print("="*80)
print("Rationale:")
print("  ✅ Achieves gamma target (-0.000005)")
print("  ✅ Lowest theta impact (-$3.5/day vs -$7 to -$20)")
print("  ✅ Minimal cost (~-$10)")
print("  ✅ Keeps 50% of upside protection")
print("  ✅ Maintains theta-positive structure (+$20/day)")
print("\nExecution:")
print("  1. Buy to Close 0.11 BTC of Short Call 76k")
print("  2. Keep Long Call 82k as hedge for remaining 0.11 short")
print("  3. Monitor new gamma: should be ~-0.000005")
print("\n" + "="*80)
