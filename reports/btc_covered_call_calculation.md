
# BTC Covered Call Strategy Calculation

**Date:** 2026-01-30
**Asset:** BTC
**Current Spot Price:** ~$83,078
**Position Vol:** 0.1 BTC (Value: ~$8,308)

> [!IMPORTANT]
> These calculations use **REAL market data** from the Bybit Option Chain (Calls), unlike the theoretical XRP model. Premiums are based on the current **Bid Price** (conservative estimate for selling).

## 1. Strategy Overview
We are modeling selling Covered Calls on 0.1 BTC.
*   **Collateral:** 0.1 BTC held in account.
*   **Action:** Sell 0.1 BTC Call Option.
*   **Goal:** Collect premium (income) while capping upside.

## 2. Market Data Analysis

### Weekly & Bi-Weekly Income (Short Term)

| Expiry | Days | Strike | % OTM | Premium (0.1 BTC) | Yield (Flat) | Ann. Yield (APY) | Max Profit (0.1 BTC) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **06-Feb** | 7 | **$85,000** | +2.3% | **$91.00** | 1.10% | **57.1%** | $283.17 (3.4%) |
| **06-Feb** | 7 | **$87,000** | +4.7% | **$41.50** | 0.50% | **26.0%** | $433.67 (5.2%) |
| **13-Feb** | 14 | **$87,000** | +4.7% | **$102.00** | 1.23% | **32.0%** | $494.17 (5.9%) |
| **13-Feb** | 14 | **$91,000** | +9.5% | **$35.50** | 0.43% | **11.1%** | $827.67 (10.0%) |

### Monthly Income (Medium Term)

| Expiry | Days | Strike | % OTM | Premium (0.1 BTC) | Yield (Flat) | Ann. Yield (APY) | Max Profit (0.1 BTC) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **27-Feb** | 28 | **$88,000** | +5.9% | **$166.50** | 2.00% | **26.1%** | $658.67 (7.9%) |
| **27-Feb** | 28 | **$91,000** | +9.5% | **$96.50** | 1.16% | **15.1%** | $888.67 (10.7%) |

## 3. Recommended Strategy: 14-Day | +4.7% OTM ($87k)

**Rationale:**
*   **Yield:** Generates **$102** every 2 weeks ($204/month) on a $8.3k position.
*   **Annualized Return:** ~32% is a solid conservative yield for BTC.
*   **Safety:** Strike is $4k away ($87k vs $83k). BTC needs to move +4.7% in 2 weeks to breach.
*   **Upside:** If BTC rallies to $87,000, you make **$400** on price appreciation + **$102** premium = **$502** profit (6% in 2 weeks).

## 4. Execution Plan (0.1 BTC)
1.  **Buy/Hold:** Ensure you have **0.1 BTC** in your Unified Trading Account.
2.  **Select Symbol:** `BTC-13FEB26-87000-C` (Call Option).
3.  **Order:** Sell (Short) **0.1** Contracts.
4.  **Price:** Limit Order at **~$1,020** (current Bid) or try closer to Mark ($1,020).
5.  **Monitor:**
    *   If BTC < $87,000 at expiry: Keep 0.1 BTC + $102 premium. Repeat.
    *   If BTC > $87,000 at expiry: You are "called" away. You sell 0.1 BTC at $87,000. You keep the $102 premium. Total cash: $8,700 + $102 = $8,802.

## 5. Risk Warning
*   **Opportunity Cost:** If BTC rallies to $100k, you are capped at $87k.
*   **USD Value:** If BTC crashes to $60k, your 0.1 BTC loses value, though the $102 premium offsets a small part of that loss.

---
**Data Source:** Real-time Bybit Option Chain (Bid Prices).
**Script:** `scripts/calc_btc_covered_call.py`
