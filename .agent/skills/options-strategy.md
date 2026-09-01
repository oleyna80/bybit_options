---
name: Options Strategy
description: Проектирование и управление опционными стратегиями
---

# Skill: Options Strategy

## Description
Архитектор опционных стратегий: выбор структур, управление Greeks, morphing позиций.

## Triggers
- "iron condor", "spread", "greeks", "options strategy", "roll"

## Strategy Catalog

### 🟢 Basic
| Strategy | Profile | Best When |
|----------|---------|-----------|
| Long Call | Bullish, unlimited upside | Strong upward momentum |
| Long Put | Bearish, limited risk | Strong downward momentum |
| Covered Call | Income, capped upside | Neutral/slightly bullish |
| Cash-Secured Put | Income, own at lower price | Bullish, want to buy dip |
| Protective Put | Insurance for long stock | Protect existing position |

### 🟡 Intermediate

#### Credit Spreads (Income)
| Strategy | Bias | Max Profit |
|----------|------|------------|
| Bull Put Spread | Bullish | Net credit |
| Bear Call Spread | Bearish | Net credit |

#### Debit Spreads (Directional)
| Strategy | Bias | Max Profit |
|----------|------|------------|
| Bull Call Spread | Bullish | Width - debit |
| Bear Put Spread | Bearish | Width - debit |

#### Neutral Strategies
| Strategy | View | Best When |
|----------|------|-----------|
| Iron Condor | Range-bound | High IV, no trend |
| Iron Butterfly | Pin expected | High IV, pin to strike |
| Long Put Butterfly | Neutral | Low IV, expect pin |
| Long Call Butterfly | Neutral | Low IV, expect pin |

#### Calendar Spreads (Time/Vol)
| Strategy | View | Profit From |
|----------|------|-------------|
| Calendar Call Spread | Neutral/Bullish | IV expansion, time decay |
| Calendar Put Spread | Neutral/Bearish | IV expansion, time decay |
| Diagonal Call Spread | Bullish | Time + direction |
| Diagonal Put Spread | Bearish | Time + direction |

#### Other Intermediate
| Strategy | Use Case |
|----------|----------|
| Collar | Zero-cost hedge |
| Straddle | Expect big move, unknown direction |
| Strangle | Cheaper straddle, wider range |
| Inverse Iron Butterfly | Breakout expected |
| Inverse Iron Condor | Breakout expected |

### 🟠 Advanced

#### Naked (High Risk)
| Strategy | Risk | Margin Req |
|----------|------|------------|
| Short Put | Unlimited downside | High |
| Short Call | Unlimited upside | Very High |
| Short Straddle | Unlimited both ways | Very High |
| Short Strangle | Unlimited both ways | High |

#### Condors & Butterflies
| Strategy | View |
|----------|------|
| Long Call Condor | Neutral, wide range |
| Long Put Condor | Neutral, wide range |
| Short Call Condor | Breakout expected |
| Short Put Condor | Breakout expected |
| Short Put Butterfly | Breakout expected |
| Short Call Butterfly | Breakout expected |

#### Ratio Spreads
| Strategy | Bias | Risk |
|----------|------|------|
| Call Ratio Backspread | Strong bullish | Limited |
| Put Ratio Backspread | Strong bearish | Limited |
| Put Broken Wing | Bearish w/ hedge | Defined |
| Call Broken Wing | Bullish w/ hedge | Defined |
| Inverse Put Broken Wing | Bullish | Defined |
| Inverse Call Broken Wing | Bearish | Defined |

#### Income Advanced
| Strategy | Description |
|----------|-------------|
| Covered Short Straddle | Stock + short straddle |
| Covered Short Strangle | Stock + short strangle |

#### Ladders
| Strategy | Bias |
|----------|------|
| Bull Call Ladder | Moderately bullish |
| Bear Call Ladder | Bearish |
| Bull Put Ladder | Bullish |
| Bear Put Ladder | Moderately bearish |

#### Exotic
| Strategy | Use Case |
|----------|----------|
| Jade Lizard | Credit, no upside risk |
| Reverse Jade Lizard | Credit, no downside risk |

### 🔴 Expert

#### Ratio Spreads (Directional)
| Strategy | Bias | Risk Profile |
|----------|------|--------------|
| Call Ratio Spread | Moderately bullish | Unlimited upside risk |
| Put Ratio Spread | Moderately bearish | Large downside risk |

#### Synthetics
| Strategy | Replicates |
|----------|------------|
| Long Synthetic Future | Long stock |
| Short Synthetic Future | Short stock |
| Synthetic Put | Long put |

#### Arbitrage
| Strategy | Use |
|----------|-----|
| Long Combo | Synthetic long |
| Short Combo | Synthetic short |

#### Volatility Plays
| Strategy | View |
|----------|------|
| Strip | Bearish, big move |
| Strap | Bullish, big move |
| Guts | Expect extreme move |
| Short Guts | Expect no move |
| Double Diagonal | Multi-expiry neutral |

## Position Morphing (Repair Trades)

| Problem | Solution |
|---------|----------|
| Tested short put | Roll down OR convert to put spread |
| IV crush after entry | Close early OR roll to calendar |
| Directional move against | Add opposite wing to create IC |

## Greeks Management

### Delta (Δ) — Directional Risk
| Δ Range | Interpretation | Action |
|---------|----------------|--------|
| ±0.1 | Neutral | Hold |
| ±0.3 | Slight lean | Monitor |
| ±0.5+ | Significant | Hedge required |

### Gamma (Γ) — Delta Acceleration
- High Γ near expiry = dangerous
- Solution: Roll out to longer DTE

### Theta (θ) — Time Decay
- Positive θ = collecting premium
- Target: θ/Γ ratio > 1

### Vega (ν) — Volatility Sensitivity
- IV Rank > 50 → Sell Vega (short vol strategies)
- IV Rank < 30 → Buy Vega (long vol strategies)

## Output
```markdown
## Strategy Proposal: <TRADE>

### Structure
- Type: Iron Condor
- Strikes: Sell 95k/105k, Buy 93k/107k
- DTE: 14 days
- Premium: $XXX

### Greeks
| Greek | Value | Target |
|-------|-------|--------|
| Delta | -0.1 | ±0.2 |
| Theta | +$XX/day | Positive |
| Vega | -$XX | Short vol |

### Risk/Reward
- Max Profit: $XXX
- Max Loss: $XXX
- Breakevens: $XX / $XX

### Management Rules
- Take profit: 50% of premium
- Stop loss: 2x credit OR BOS
```
