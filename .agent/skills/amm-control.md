---
description: Управление AMM Robot через API — изменение параметров, мониторинг, режимы работы
---

# Skill: AMM Robot Control

## Назначение
Этот skill даёт Trading Expert возможность управлять AMM Robot через REST API.

## Доступные действия

### 1. Получить статус AMM
```bash
GET /api/v1/amm/status
```

### 2. Получить список стратегий
```bash
GET /api/v1/amm/strategies
```

### 3. Обновить параметры стратегии
```bash
POST /api/v1/amm/agent/command
Content-Type: application/json

{
  "action": "UPDATE_STRATEGY_PARAMS",
  "strategy_id": 1,
  "params": {
    "target_iv": 0.58,
    "skew_factor": 0.02,
    "spread_bps": 60
  },
  "reason": "IV Rank = 85, switching to aggressive selling"
}
```

**Параметры:**

| Param | Type | Description | Range |
|-------|------|-------------|-------|
| `target_iv` | float | Base IV для ценообразования | 0.40 - 1.00 |
| `skew_factor` | float | Skew adjustment per delta | -0.05 to +0.05 |
| `spread_bps` | int | Bid-ask spread (basis points) | 20 - 100 |

### 4. Приостановить / Возобновить стратегию
```bash
# Pause
POST /api/v1/amm/agent/command
{"action": "PAUSE_STRATEGY", "strategy_id": 1, "reason": "Market too volatile"}

# Resume
POST /api/v1/amm/agent/command
{"action": "RESUME_STRATEGY", "strategy_id": 1}
```

### 5. Переключить режим работы
```bash
POST /api/v1/amm/mode
{"mode": "AUTO", "check_interval_minutes": 15}
```

**Режимы:**
- `MANUAL` — агент (человек) вручную отправляет команды
- `AUTO` — система автоматически проверяет рынок

## Decision Framework

### Когда менять target_iv?

| Условие | Действие |
|---------|----------|
| IV Rank > 80 | target_iv *= 0.95 (агрессивнее продаём) |
| IV Rank < 20 | target_iv *= 1.05 (осторожнее) |
| IV/HV > 1.3 | Увеличить spread (+20 bps) |
| IV/HV < 0.8 | Уменьшить spread (-20 bps) |

### Когда PAUSE?
- Extreme market move (>5% за час)
- Breaking news (FOMC, CPI, major hack)
- Technical issues (API failures)
- Margin utilization > 70%

## Example Workflow

```
1. GET /api/v1/volatility/context?symbol=BTC
   → IV Rank = 82, Signal = SELL_PREMIUM

2. Решение: снизить target_iv на 5%

3. POST /api/v1/amm/agent/command
   {"action": "UPDATE_STRATEGY_PARAMS", "strategy_id": 1,
    "params": {"target_iv": 0.62}, "reason": "IV Rank 82"}

4. GET /api/v1/amm/strategies — проверить
```

## Safety Notes

> [!CAUTION]
> Всегда указывайте `reason` — это создаёт audit trail.

> [!WARNING]
> Не меняйте target_iv более чем на ±10% за одну команду.
