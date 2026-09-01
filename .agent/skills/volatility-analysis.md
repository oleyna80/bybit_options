---
description: Анализ волатильности — IV Rank, HV, Smile — для принятия торговых решений
---

# Skill: Volatility Analysis

## Назначение
Анализ режима волатильности для определения оптимальной опционной стратегии.

## Получение данных

### Полный контекст волатильности
```bash
GET /api/v1/volatility/context?symbol=BTC&include_smile=true&expiry=26JAN26
```

Ответ:
```json
{
  "symbol": "BTC",
  "iv_rank": 75.5,
  "iv_regime": "HIGH",
  "hv": {"hv_7d": 0.42, "hv_30d": 0.55, "hv_90d": 0.62},
  "iv_hv_ratio": 1.18,
  "signals": {"hv_signal": "SELL_PREMIUM", "overall": "SELL_PREMIUM"},
  "smile": {"atm_iv": 0.65, "put_skew": 0.05, "call_skew": -0.02}
}
```

### История IV Rank
```bash
GET /api/v1/volatility/iv-rank/history?symbol=BTC&days=365
```

## Interpretation Guide

### IV Rank

| Range | Regime | Action |
|-------|--------|--------|
| 0-20 | LOW | Buy premium, Long Vega |
| 20-50 | NORMAL | Neutral, standard spreads |
| 50-80 | ELEVATED | Sell premium, Short Vega |
| 80-100 | HIGH | Aggressive premium selling |

### IV/HV Ratio

| Ratio | Interpretation | Action |
|-------|----------------|--------|
| < 0.8 | IV underpriced | Buy options |
| 0.8-1.2 | Fair value | Standard sizing |
| > 1.2 | IV overpriced | Sell options |
| > 1.5 | Extreme premium | Max size selling |

### Volatility Smile

| Metric | Meaning | Implication |
|--------|---------|------------|
| `put_skew > 0` | Puts expensive (fear) | Consider selling puts |
| `call_skew > 0` | Calls expensive | Consider selling calls |
| `skew_slope` high | Steep smile | Favor ATM over wings |

## Analysis Workflow

### Step 1: Daily Check
```
1. GET /volatility/context
2. Записать IV Rank, IV/HV ratio
3. Определить режим: HIGH/NORMAL/LOW
```

### Step 2: Strategy Selection
```
IF iv_regime == "HIGH" AND iv_hv_ratio > 1.2:
    → Iron Condor / Strangle (Short Vega)
    
ELIF iv_regime == "LOW" AND iv_hv_ratio < 0.8:
    → Long Straddle / Butterfly (Long Vega)
    
ELSE:
    → Credit Spreads (directional bias)
```

### Step 3: Position Adjustment
```
IF short_vega AND iv_regime → LOW:
    → Close some short vega
    → Reduce target_iv in AMM
```

## Integration with AMM

После анализа используй `skills/amm-control.md` для команд:

```
Volatility Analysis → Decision → AMM Command
```

Пример:
1. Анализ: IV Rank = 85, IV/HV = 1.35
2. Решение: Aggressive selling mode
3. Команда: UPDATE_STRATEGY_PARAMS (target_iv -= 5%)
