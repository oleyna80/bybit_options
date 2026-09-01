---
name: Trend Analysis
description: Multi-timeframe trend analysis using Alligator and Fractals for directional trading
---

# Skill: Trend Analysis

## Description
Analyze market trends across W1/D1/H4 timeframes using Williams' Chaos Theory (Alligator + Fractals).

## Triggers
- "trend", "global trend", "W1", "weekly", "Alligator state", "fractal breakout"

---

## API Endpoints

### 1. Get Technical Context (Primary)
```bash
GET /api/v1/technical/context?symbol=BTC
```

**Response:**
```json
{
  "symbol": "BTC",
  "timestamp": "2026-01-24T18:00:00Z",
  "current_price": 98000.0,
  "global_trend": "BULLISH|BEARISH|NEUTRAL",
  "trend_signal": "BUY_DELTA|SELL_DELTA|NEUTRAL",
  "signal_confidence": 0.8,
  "alligator": {
    "W1": {"state": "EATING_UP", "jaw": 95000, "teeth": 96500, "lips": 97200},
    "D1": {"state": "EATING_UP", ...},
    "H4": {"state": "AWAKENING", ...}
  },
  "levels": {
    "nearest_resistance": {"price": 100000, "timeframe": "W1"},
    "nearest_support": {"price": 94000, "timeframe": "W1"}
  }
}
```

### 2. Get Alligator State
```bash
GET /api/v1/technical/alligator?symbol=BTC&timeframe=W1
```

### 3. Get Key Fractals
```bash
GET /api/v1/technical/fractals?symbol=BTC&timeframe=W1&limit=5
```

---

## Decision Framework

### Multi-Timeframe Hierarchy
```
W1 (Weekly)  → GLOBAL TREND (PRIMARY)
    │
    ├─ EATING_UP/DOWN → Strong trend → Follow it
    ├─ SLEEPING       → No trend → Sell premium (theta/vega)
    └─ SATED          → Trend exhaustion → Exit directional positions
    
D1 (Daily)   → CONFIRMATION / FALLBACK
    │
    └─ Confirms W1 or provides fallback if W1 is SLEEPING
    
H4 (4-hour)  → ENTRY TIMING
    │
    └─ Precise entry/exit timing
```

### Trading Signals

| W1 Alligator | D1 Alligator | H4 Alligator | Action |
|--------------|--------------|--------------|--------|
| **EATING_UP** | EATING_UP | EATING_UP | **BUY_DELTA** (long calls, confidence 0.9) |
| **EATING_UP** | Any | AWAKENING/UP | **BUY_DELTA** (long calls, confidence 0.7) |
| **EATING_DOWN** | EATING_DOWN | EATING_DOWN | **SELL_DELTA** (long puts, confidence 0.9) |
| **EATING_DOWN** | Any | AWAKENING/DOWN | **SELL_DELTA** (long puts, confidence 0.7) |
| **SLEEPING** | SLEEPING | Any | **NEUTRAL** (sell premium, theta/vega) |
| **SATED** | Any | Any | **EXIT** (take profit, reduce delta) |

---

## Integration with AMM Robot

### When `trend_signal = BUY_DELTA`
```bash
POST /api/v1/amm/agent/command
{
  "action": "UPDATE_STRATEGY_PARAMS",
  "strategy_id": 1,
  "params": {
    "skew_factor": -0.03  # Negative skew = cheaper calls, more expensive puts
  },
  "reason": "W1 EATING_UP: Adjusting skew to favor call selling"
}
```

### When `trend_signal = SELL_DELTA`
```bash
POST /api/v1/amm/agent/command
{
  "action": "UPDATE_STRATEGY_PARAMS",
  "strategy_id": 1,
  "params": {
    "skew_factor": 0.03  # Positive skew = cheaper puts, more expensive calls
  },
  "reason": "W1 EATING_DOWN: Adjusting skew to favor put selling"
}
```

### When `trend_signal = NEUTRAL`
```bash
POST /api/v1/amm/agent/command
{
  "action": "UPDATE_STRATEGY_PARAMS",
  "strategy_id": 1,
  "params": {
    "skew_factor": 0.0,  # No skew, symmetric pricing
    "target_iv": <current_iv + 0.02>  # Slightly higher IV to sell premium
  },
  "reason": "W1 SLEEPING: No trend, focusing on theta/vega"
}
```

---

## Golden Rules

1. **W1 is Truth**
   - НИКОГДА не торгуй против W1 Alligator
   - Если W1 EATING_UP → только лонги или нейтральные позиции
   - Если W1 EATING_DOWN → только шорты или нейтральные позиции

2. **Fractal Levels = Stop Loss Zones**
   - Используй W1 фракталы как ключевые уровни
   - При пробое W1 fractal UP → сильный бычий сигнал
   - При пробое W1 fractal DOWN → сильный медвежий сигнал

3. **SLEEPING = Theta Heaven**
   - Когда Alligator спит → продавай премию (стрэддлы, стрэнглы)
   - Избегай направленных позиций

4. **SATED = Exit Signal**
   - Alligator SATED → линии сходятся → тренд заканчивается
   - Закрывай направленные позиции, фиксируй прибыль

---

## Output Format

When analyzing trend, provide structured analysis:

```markdown
## Trend Analysis: BTC

### Multi-Timeframe Alligator
- **W1:** EATING_UP (spread 1.8%, jaw 95k, teeth 96.5k, lips 97.2k)
- **D1:** EATING_UP (spread 1.2%)
- **H4:** AWAKENING (spread 0.6%)

### Key Levels (W1 Fractals)
- **Resistance:** $100,000 (W1 UP fractal, +2.0% distance)
- **Support:** $94,000 (W1 DOWN fractal, -4.1% distance)

### Global Trend
**BULLISH** (W1 + D1 aligned)

### Signal
**BUY_DELTA** (Confidence: 0.8)

### Recommendation
1. Open long call positions (ITM or ATM)
2. Adjust AMM skew to -0.03 (favor call selling)
3. Stop-loss below W1 support at $94k
4. Target: W1 resistance at $100k
```
