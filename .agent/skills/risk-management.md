---
name: Risk Management
description: Управление рисками, позиционирование, hedging
---

# Skill: Risk Management

## Description
Контроль рисков: position sizing, stop-loss, margin management, hedging.

## Triggers
- "risk", "stop-loss", "hedge", "margin", "position size"

## Risk Protocols

### Position Sizing
```
Risk per trade = Account * Risk %
Position Size = Risk per trade / (Entry - Stop)

Example:
Account: $10,000
Risk: 2% = $200
Entry: $100, Stop: $95
Size = $200 / $5 = 40 units
```

### Capital Allocation
| Zone | Allocation | Purpose |
|------|------------|---------|
| 0-30% | Liquid | Margin buffer |
| 30-50% | Active positions | Working capital |
| 50-70% | Reserve | Drawdown management |
| 70-100% | FORBIDDEN | Never use |

### Stop-Loss Rules
1. **Technical Stop**: Below key S/R level
2. **Volatility Stop**: 2x ATR from entry
3. **Premium Stop** (options): 2x credit received
4. **Time Stop**: Close if thesis invalidated by X days

## Hedging Strategies

### Delta Hedging
| Portfolio Δ | Action |
|-------------|--------|
| Too positive | Sell futures / buy puts |
| Too negative | Buy futures / buy calls |

### Tail Risk Hedging
- **Put Spread**: Cheap protection
- **Collar**: Zero-cost hedge
- **VIX calls**: Volatility spike protection

## Risk Metrics Dashboard
```markdown
## Risk Report

### Account Health
- Total Equity: $XX,XXX
- Used Margin: XX%
- Available Margin: $XX,XXX
- Margin Utilization: < 40% ✓

### Portfolio Greeks
| Greek | Current | Threshold | Status |
|-------|---------|-----------|--------|
| Delta | -0.2 BTC | ±0.5 | ✓ OK |
| Gamma | $XXX | — | Monitor |
| Vega | -$XXX | — | Short vol |

### Position-Level Risk
| Position | P&L | Risk Status |
|----------|-----|-------------|
| BTC IC | +$XX | ✓ Healthy |
| ETH Spread | -$XX | ⚠️ Monitor |
```

## Circuit Breakers
🚨 **STOP TRADING** if:
- Daily loss > 5%
- Margin utilization > 50%
- 3 consecutive losing trades
- High-impact news in next 1h
