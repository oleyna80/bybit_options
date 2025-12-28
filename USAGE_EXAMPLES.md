# 🚀 Option Quotes - Usage Examples

Real-world scenarios for using the option quotes tools.

## 1. HEDGE POSITIONING (Protective Put)

**Scenario:** You hold 0.2 BTC short from spot. You want to buy puts to protect against a rally.

```bash
# Check current put prices
python get_option_quotes.py BTC-19DEC25-82000-P BTC-19DEC25-84000-P BTC-19DEC25-86000-P

# Or single strike
python get_option_quotes.py BTC-19DEC25-82000-P
```

**Expected Output:**
```
| Option | Expiry | Mark | Bid | Ask | Spread | IV | Delta |
| P $82000 | 19DEC25 | $446 | $445 | $455 | $10 (2.24%) | 55.34% | -0.1761 |
```

**Decision Logic:**
- ✅ IV 55% is reasonable (not too expensive)
- ✅ Spread 2.24% acceptable (means ~$9 slippage per contract)
- ✅ Delta -0.18 = "costs $446 to protect against drops"
- ⏰ 4 days to expiry (watch for sharp time decay)

**Action:** Entry at Bid $445 for 0.2 contracts = $89 cost

---

## 2. CALL SELLING (Premium Collection)

**Scenario:** You want to sell calls against your position, collect premium.

```bash
# Check call prices
python get_option_quotes.py BTC-19DEC25-87000-C BTC-19DEC25-89000-C BTC-19DEC25-91000-C
```

**Analysis:**
- 87k call: Higher premium ($624) but more likely to expire ITM
- 89k call: Best balance (good premium + OTM)
- 91k call: Safe but less income

**Decision:** Sell 0.1 at Ask $565 = $56.50 income

---

## 3. BEFORE ENTERING A POSITION

```bash
# Get latest quote before clicking BUY
python get_option_quotes.py BTC-19DEC25-82000-P

# Check:
# 1. Mark price matches expected ✓
# 2. Bid-Ask spread <2% ✓  
# 3. Open Interest >20 ✓
# 4. IV not spiking ✓
```

---

## 4. DAILY MONITORING

```bash
# Morning routine
python get_option_quotes.py BTC-19DEC25-82000-P BTC-19DEC25-84000-P

# Track how prices move throughout day
```

---

## 5. EXPIRY MANAGEMENT (19DEC expires in 4 days)

```bash
# Check all 19DEC positions for urgent action
python get_option_quotes.py \
  BTC-19DEC25-76000-P \
  BTC-19DEC25-78000-P \
  BTC-19DEC25-82000-P
```

**Rules:**
- If <2 days left and OTM: Close position
- If <1 day left: Always close
- If ITM: Decide to exercise or roll

---

## 6. EXPORT FOR ANALYSIS

```bash
# Save quotes to JSON for programmatic analysis
python get_option_quotes_json.py BTC-19DEC25-82000-P > quotes.json

# Track over time
python get_option_quotes_json.py BTC-19DEC25-82000-P >> historical_quotes.json
```

---

## 📌 QUICK REFERENCE

| Use Case | Command | Key Metric |
|----------|---------|-----------|
| **Hedge** | `get_option_quotes.py [PUTS]` | Bid-Ask <2% |
| **Premium** | `get_option_quotes.py [CALLS]` | IV >50% |
| **Before Trade** | `get_option_quotes.py [SYMBOL]` | OI >20 |
| **Analysis** | `get_option_quotes_json.py [...]` | Export JSON |

See [OPTION_QUOTES_README.md](OPTION_QUOTES_README.md) for full documentation.
