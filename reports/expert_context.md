
# Expert Market Context (Simulated)

**Date:** 2026-01-30
**Asset:** BTC

## 1. Volatility Surface & Skew
*   **Term Structure:** Contango (Normal).
    *   7d IV: 45%
    *   30d IV: 48%
    *   90d IV: 52%
    *   *Interpretation:* Market expects volatility to increase slightly over time, no immediate panic.
*   **Skew (25-Delta RR):** -2.5% (Put Skew).
    *   Puts trade ~2.5 vol points higher than Calls.
    *   *Interpretation:* Moderate demand for downside protection, but not extreme fear.
*   **IV/HV Ratio:** 1.15
    *   Implied Volatility is slightly overpriced relative to realized (HV ~40%).
    *   *Action:* Good environment to **Sell Premium** (Iron Condors, Covered Calls).

## 2. Advanced Greeks Exposure
*   **Vanna (dDelta/dVol):** Negative.
    *   If Vol spikes, our Delta becomes more negative (Short Puts become 'shorter', Short Calls become 'less short' delta?). Check signs.
    *   *Risk:* A volatility spike often accompanies a crash. If we have Short Puts, Delta becomes MORE positive as we go ITM? No, Delta approaches 1.
*   **Charm (dDelta/dTime):** Positive.
    *   As time passes, our OTM Short options lose Delta (decay towards 0), helping position stability.

## 3. Macro/Event Calendar
*   No major Tier-1 events in the next 7 days.
*   **FOMC Meeting:** In 14 days (Feb 13). Expect IV expansion leading up to it.

## 4. Derived Recommendations
1.  **Short Term:** Harvest Theta. Term structure is stable.
2.  **Medium Term (14d):** Be careful of FOMC IV ramp-up. Do not sell "too cheap" Vega now if it will expand later.
