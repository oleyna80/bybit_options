---
name: Technical Indicators
description: Использование индикаторов для анализа и сигналов
---

# Skill: Technical Indicators

## Description
Применение технических индикаторов для подтверждения сигналов и фильтрации входов.

## Triggers
- "RSI", "MACD", "индикаторы", "divergence", "momentum", "Alligator", "fractals"

## Core Indicators

### Trend Indicators
| Indicator | Purpose | Settings |
|-----------|---------|----------|
| EMA 21/50/200 | Trend direction | Standard |
| Alligator | Trend + momentum | 13/8/5 |
| Ichimoku | Multi-purpose | 9/26/52 |

### Momentum
| Indicator | Purpose | Key Levels |
|-----------|---------|------------|
| RSI | Overbought/Oversold | 70/30, divergences |
| MACD | Momentum + crossovers | Signal line cross |
| Stochastic | Short-term momentum | 80/20 |

### Volatility
| Indicator | Purpose | Usage |
|-----------|---------|-------|
| Bollinger Bands | Volatility squeeze | Width contraction |
| ATR | Position sizing | Stop-loss distance |
| IV Rank | Options premium | >50 = sell vol |

## Williams' Chaos Theory (Primary System)

### Alligator
```
Jaw (Blue)   = SMMA(13), offset 8  — "челюсть", медленная
Teeth (Red)  = SMMA(8), offset 5   — "зубы", средняя
Lips (Green) = SMMA(5), offset 3   — "губы", быстрая
```

| State | Lines | Interpretation |
|-------|-------|----------------|
| **Sleeping** | Intertwined | No trend, avoid trading |
| **Awakening** | Starting to diverge | Prepare for entry |
| **Eating** | Fully spread | Trend active, ride it |
| **Sated** | Converging | Take profit, trend ending |

### Fractals
```
Fractal Up   = High[2] > High[0,1,3,4]  — потенциальное сопротивление
Fractal Down = Low[2] < Low[0,1,3,4]   — потенциальная поддержка
```

**Использование:**
- **Break above Fractal Up** + Alligator eating up → Long entry
- **Break below Fractal Down** + Alligator eating down → Short entry
- Fractals как уровни S/R для stop-loss
- НЕ торговать fractals когда Alligator спит

### Alligator + Fractals Strategy
```
Entry Rules:
1. Alligator awake (lines spread)
2. Price breaks fractal in trend direction
3. Entry on pullback to Lips (green line)

Exit Rules:
1. Price closes beyond Teeth (red) against trend
2. Opposite fractal forms
3. Lines start converging
```

## Divergences
- **Regular Bullish**: Price LL, RSI HL → reversal up
- **Regular Bearish**: Price HH, RSI LH → reversal down
- **Hidden Bullish**: Price HL, RSI LL → trend continuation
- **Hidden Bearish**: Price LH, RSI HH → trend continuation

## Signal Confluence
✅ Strong signal = 3+ confirmations:
1. HTF trend alignment
2. S/R level
3. Indicator confirmation (RSI, MACD)
4. Candlestick pattern

## Output
```markdown
## Indicator Analysis: <ASSET>

### Trend
- EMA Stack: Bullish/Bearish
- Alligator: Awake/Sleeping

### Momentum
- RSI(14): XX (Overbought/Neutral/Oversold)
- MACD: Above/Below signal line

### Volatility
- IV Rank: XX% (High/Low)
- ATR: $XXX

### Signal: <BUY/SELL/NEUTRAL>
Confluence: X/4
```
