---
name: Trading Automation
description: Автоматизация трейдинга: Pine Script, боты, сигналы
---

# Skill: Trading Automation

## Description
Создание и поддержка автоматизированных торговых систем.

## Triggers
- "pine script", "бот", "автоматизация", "сигналы", "alert"

## Pine Script Development

### Template Structure
```pine
//@version=6
indicator("My Indicator", overlay=true)

// === INPUTS ===
length = input.int(14, "Length")

// === CALCULATIONS ===
value = ta.sma(close, length)

// === PLOTTING ===
plot(value, "SMA", color.blue)

// === ALERTS ===
alertcondition(ta.crossover(close, value), "Buy Signal")
```

### Best Practices
- Version 6 syntax
- Clear input labels
- Type declarations (`int`, `float`, `bool`)
- Modular functions
- `request.security` for MTF

## Bot Architecture
```
┌─────────────────┐
│  Signal Source  │ ← TradingView alerts / internal logic
└────────┬────────┘
         ▼
┌─────────────────┐
│  Decision Layer │ ← Filters, risk checks
└────────┬────────┘
         ▼
┌─────────────────┐
│  Execution      │ ← API calls, order management
└────────┬────────┘
         ▼
┌─────────────────┐
│  Logging/DB     │ ← Trade history, P&L tracking
└─────────────────┘
```

## Signal Types
| Type | Source | Format |
|------|--------|--------|
| Webhook | TradingView | JSON to endpoint |
| WebSocket | Exchange | Real-time stream |
| Polling | API | Periodic checks |

## Alert Payload Format
```json
{
  "action": "buy" | "sell" | "close",
  "symbol": "BTCUSDT",
  "price": 100000,
  "size": 0.1,
  "strategy": "iron_condor",
  "timestamp": "2025-01-23T21:00:00Z"
}
```

## Integration with Project
- **Entry point**: Webhook → FastAPI endpoint
- **Processing**: `strategy_manager.process_signal()`
- **Execution**: `order_executor.place_order()`
- **Logging**: `storage_service.log_trade()`

## Testing
1. **Backtest** — Pine Script strategy tester
2. **Paper trade** — Testnet API
3. **Shadow mode** — Live signals, no execution
4. **Live** — Production with position limits
