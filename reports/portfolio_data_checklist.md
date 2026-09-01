
# Missing Data Checklist for Expert Analysis

To perform a "Full Expert Analysis" based on the new skills (`volatility-surface-skew.md`, `greeks-book-risk.md`, etc.), we need the following additional data points which are currently missing from `reports/latest_analysis.md`:

## 1. Volatility Surface Context
- [ ] **Term Structure:** Is the curve in Contango or Backwardation? (Needs ATM IVs for 7d, 30d, 90d, 180d).
- [ ] **Skew Metrics:** 25-delta Risk Reversal (Put IV - Call IV) for identifying downside fear vs upside FOMO.
- [ ] **IV/HV Ratio:** Current implied volatility vs realized volatility to judge "Expensive/Cheap" regimes.

## 2. Advanced Greeks (Second Order)
- [ ] **Vanna:** $\Delta$ sensitivity to Volatility (Critical for Skew risk).
- [ ] **Volga:** $\nu$ sensitivity to Volatility (Convexity of the Vega risk).
- [ ] **Charm:** $\Delta$ decay over time.

## 3. Margin & Liquidity Depth
- [ ] **Margin Utilization Trend:** Is margin usage increasing or stable?
- [ ] **Orderbook Depth:** Distance to liquidation price.

## 4. Event Risk
- [ ] Upcoming economic events (Fed, CPI, etc.) that match expiry dates.

## Action Plan
I will generate a supplementary report `reports/expert_context.md` (simulated or fetched) to fill these gaps before providing the final recommendation.
