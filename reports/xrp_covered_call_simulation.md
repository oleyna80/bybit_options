
# XRP Covered Call Strategy Simulation

**Date:** 2026-01-30
**Asset:** XRPUSDT
**Current Price:** $1.7550
**Reference Volatility (HV30):** ~70%

> [!NOTE]
> Bybit does not currently offer XRP Options. This simulation uses the **Black-Scholes model** based on real-time Spot prices and Historical Volatility (HV) to estimate theoretical premiums and returns.

## 1. Market Conditions
- **Spot Price:** $1.7550
- **30-Day Historical Volatility:** 69.88%
- **7-Day Historical Volatility:** 55.90%
- **Implied Volatility Assumption:** Conservative (Equal to HV30, ~70%)

High volatility environments (~70%) are generally favorable for selling options (Covered Calls) as premiums are expensive.

## 2. Strategy Performance (Conservative Scenario)

The following table shows the estimated returns for selling Call Options at different expiries and strike prices.

| Expiry | Strike (+% OTM) | Strike Price | Est. Premium | Yield (Flat) | Ann. Yield | Max Profit | Breakeven |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **7 Days** | +2% | $1.7901 | $0.0530 | **3.02%** | 157.38% | 5.02% | $1.7020 (-3.0%) |
| **7 Days** | +5% | $1.8427 | $0.0347 | **1.98%** | 103.08% | 6.98% | $1.7203 (-2.0%) |
| **14 Days** | +5% | $1.8427 | $0.0616 | **3.51%** | 91.53% | 8.51% | $1.6934 (-3.5%) |
| **30 Days** | +5% | $1.8427 | $0.1067 | **6.08%** | 73.95% | 11.08% | $1.6483 (-6.1%) |
| **30 Days** | +10% | $1.9305 | $0.0778 | **4.43%** | 53.94% | 14.43% | $1.6772 (-4.4%) |

### Key Takeaways
*   **Weekly Income:** Selling weekly 5% OTM calls generates ~2% per week.
*   **Monthly Income:** A monthly 5% OTM call generates ~6% upfront.
*   **Downside Protection:** The premium collects provides a buffer. For the 30-day 5% OTM strategy, your breakeven is **$1.6483**, providing ~6% downside protection.

## 3. Deep Dive: 30-Day | +5% OTM Strategy

**Strategy:** Buy 1 XRP @ $1.7550, Sell 1 Call @ $1.8427 (Exp: 30 Days)
**Upfront Credit:** $0.1067 (6.08%)

### Payoff Matrix at Expiry

| Price at Expiry | Strategy Value | PnL ($) | PnL (%) | Outcome |
| :--- | :--- | :--- | :--- | :--- |
| **$1.4040** (-20%) | $1.5107 | $-0.2443 | -13.92% | Loss mitigated by premium |
| **$1.5795** (-10%) | $1.6862 | $-0.0688 | -3.92% | Small Loss |
| **$1.6483** (-6.1%) | $1.7550 | $0.0000 | **0.00%** | **Breakeven** |
| **$1.7550** (Flat) | $1.8617 | $0.1067 | **+6.08%** | Profit from Premium |
| **$1.8427** (+5%) | $1.9494 | $0.1944 | **+11.08%** | **Max Profit** achieved |
| **$1.9305** (+10%) | $1.9494 | $0.1944 | **+11.08%** | Capped upside |
| **$2.1060** (+20%) | $1.9494 | $0.1944 | **+11.08%** | Capped upside |

### Visualization
The strategy outperforms holding raw XRP if the price at expiry is below **$1.9494** (Strike + Premium).
If XRP surges >11% in 30 days, simply holding XRP would have been more profitable, but you still lock in an 11% gain.

## 4. Risks & Considerations
1.  **Capped Upside:** You sell away potential gains above $1.84. If XRP goes to $3.00, you only make 11%.
2.  **Downside Risk:** You still own the underlying XRP. If XRP drops to $1.00, you lose money (though less than holding spot alone).
3.  **Execution:** Since Bybit lacks XRP options, this must be executed on a platform that supports them (e.g., Deribit, if available, or OTC) OR structured synthetically if you have access to such tools.
4.  **Volatility Risk:** If realized volatility is much higher than 70%, the options might be "underpriced" by this model, meaning you should have received more premium.

## 5. Scripts
A simulation script has been created at `scripts/simulate_xrp_covered_call.py` which you can run anytime to get updated numbers based on the latest market data.

```bash
python3 scripts/simulate_xrp_covered_call.py
```
