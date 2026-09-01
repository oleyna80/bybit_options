# Sigma-Fractal Trading Strategy v7.2

> **SSOT:** Полное описание торговой стратегии и логики Delta Hedger Bot.  
> **Last verified:** 2026-01-18  
> **Status:** ACTIVE  
> **Audit:** Completed (8 points reviewed)

---

## 1. Философия стратегии

### Принцип: "Идти за рынком"

Не предугадывать движение, а **реагировать** на подтверждённые сигналы рынка.

**Wait for Fixation** — строгое требование:
- Вход/сигнал ТОЛЬКО после закрытия свечи за уровнем
- Пробой внутри свечи → НЕ сигнал
- Свеча ЗАКРЫЛАСЬ за ключевым фракталом → Сигнал!

---

## 2. Индикаторы

| Индикатор | Параметры | Назначение |
|-----------|-----------|------------|
| **Bollinger Bands** | (20, 2.0) | Экстремальная зона (2σ) |
| **Bollinger Bands** | (20, 1.0) | Зона шума (1σ) |
| **Williams Fractals** | 5-bar | Структурные уровни |
| **Williams Alligator** | Jaw(13,8), Teeth(8,5), Lips(5,3) | Направление тренда |

---

## 3. Ключевой Фрактал (Key Fractal)

**Ключевой Фрактал** = Williams Fractal, удовлетворяющий **ДВУМ условиям**:

```
Условие 1 (Williams — относительно Alligator Teeth):
├─ Fractal UP:   fractal.high > alligator.teeth
└─ Fractal DOWN: fractal.low  < alligator.teeth

Условие 2 (Bollinger — зона значимости):
├─ Fractal UP:   bb.upper_1σ < fractal.high < bb.upper_2σ
└─ Fractal DOWN: bb.lower_2σ < fractal.low  < bb.lower_1σ
```

**Игнорируются:**
- Фракталы внутри 1σ = шум
- Фракталы за 2σ = выбросы (outliers)

---

## 4. Иерархия таймфреймов

| TF | Роль | Триггер | Действие |
|----|------|---------|----------|
| **D1** | Стратег | Закрепление за КФ | Roll IC / смена стратегии (глобальный тренд) |
| **H4** | Тактик | Закрепление за КФ | Опционная защита + закрытие фьючерса (локальный тренд) |
| **H1** | Хеджер | Закрепление за КФ | Фьючерсный хедж |

### Эскалация защиты (H1 → H4)

```
H1 пробой КФ:
└── Хеджируем ФЬЮЧЕРСОМ (быстро, просто)

H4 пробой КФ:
├── ЗАКРЫВАЕМ фьючерс полностью
├── ЖДЁМ консолидацию (inside bar / low volatility)
└── ПОКУПАЕМ опцион лимиткой
    ├── IV offset: -0.1 от текущего
    ├── Ladder: +0.1 IV каждые 5 минут
    └── Target delta после покупки: 0.008-0.012
```

---

## 5. Режимы Delta Hedger Bot

### Управление Target Delta

```
Target Delta — настраивается:
├─ Через DB config (hedger_config)
├─ Через Telegram: /set_target_delta 0.005
└─ Автоматически при пробое КФ (с подтверждением)

Трейдер контролирует target, бот держит delta около target.
```

### Пороги

| Параметр | Значение |
|----------|----------|
| **IC target delta** | 0.0 - 0.005 BTC |
| **Hedge threshold** | ±0.003 BTC |
| **Max order size** | 0.1 BTC |

---

## 6. Iron Condor Structure

### Параметры построения

| Параметр | Значение |
|----------|----------|
| **Short Strike Delta** | 0.18 - 0.22 (при высокой IV → 0.18) |
| **Spread Width** | 6000 pts (между long и short в крыле) |
| **DTE при открытии** | 20-35 дней |
| **Strike Selection** | По IV, Delta, Vega |

### Визуализация

```
         Long Put    Short Put         Short Call    Long Call
            │            │                  │            │
           80K          86K      ATM       98K          104K
            ▼            ▼       95K        ▼            ▼
            
         ◄──── 6000 ────►              ◄──── 6000 ────►
              (spread)                      (spread)
```

---

## 7. Защитные механизмы

### 7.1 Cat Ears (Gamma Protection)

**Триггер:** Portfolio Gamma > dynamic threshold

```python
# Динамический Gamma Threshold
gamma_threshold = delta_threshold / expected_move

# expected_move = price × IV × √(hedge_interval / 8760)
# При IV=40%, Price=95K, interval=1h: threshold ≈ 0.000007
```

**Структура Cat Ears:**

```
IC:        Buy 80K, Sell 86K — Sell 98K, Buy 104K

Cat Ears (добавляются с ОБЕИХ сторон):
├─ PUT:  Buy 88K (или 90K), Sell 86K
└─ CALL: Buy 96K (или 94K), Sell 98K

Выбор Long Strike:
├─ Не обязательно соседний — может быть через 1-2 страйка  
├─ Критерии: греки (достаточно gamma) + bid-ask spread
└─ Размер: 10% от IC позиции
```

### 7.2 Squeeze Defense

**Триггер:** BB Width < 25 перцентиль

**Определение направления тренда:**
```
D1 пробой КФ → Глобальный тренд (приоритет)
H4 пробой КФ → Локальный тренд
Нет пробоев → Защитить обе стороны
```

**Логика при Squeeze:**
1. Проверить Gamma → если высокая → Cat Ears
2. Проверить Delta → если не нейтральная → докупить опционы
3. Защита в сторону тренда

### 7.3 DTE Roll

**Триггер:** Проверка каждый час

**Логика:**
- По мере снижения DTE → уменьшается 1σ expected move
- Сжать расстояние между крыльями (ориентир = новая 1σ по IV)
- Или сдвинуть весь IC если цена ушла

```python
one_sigma = current_price * iv * sqrt(dte / 365)
```

### 7.4 D1 Breakout Handler

**Триггер:** D1 свеча закрылась за ключевым фракталом

**Decision:**
```
Проверить: расстояние до short strike vs IV-based 1-2D move

Safe (distance > expected move):
└── CONTINUE: Защита опционами + фьючерсами

Danger (distance < expected move):
└── ROLL: Сдвинуть short strike к delta 0.18-0.20
```

---

## 8. Position Transformation (вместо закрытия с убытком)

### Правила трансформации

| Сценарий | Действие |
|----------|----------|
| Опцион в убытке + Range | Ratio: продать OTM до покрытия убытка |
| Опцион в убытке + Trend за нас | Держать опцион + hedge фьючерсом |
| Ratio пошёл против | Превратить в спред (ограничить риск) |
| DTE < 5 + риск ITM | Выйти из IC в спред |

### Методы защиты IC

```
1. Rolling — сдвиг на новый страйк/экспирацию
2. Delta Hedging — хедж фьючерсом
3. Convert to Spread — закрыть угрожаемый short
```

### DTE < 5 Decision

```
Если short strike внутри 1σ И тренд к страйку:
└── EXIT IC → оставить как spread (закрыть short)

Если безопасно:
└── Держать (theta decay)
```

---

## 9. IC Exit Strategy

### Exit Rules

| Правило | Условие | Действие |
|---------|---------|----------|
| **Profit Target** | P/L ≥ 50% max profit | Закрыть IC |
| **DTE Threshold** | DTE ≤ 7 дней | Закрыть IC |
| **Price in Center** | Цена застряла в центре + DTE < 3 | Можно оставить на экспирацию |

### IV Protection

```
Инструмент: Strangle на квартальных опционах
Цель: нейтрализовать vega exposure
Отдельная позиция от IC
```

---

## 10. Position Markup (Гибридный подход)

### Phase 1: Авто-детекция

Бот анализирует текущие позиции и предполагает структуру:
```
Detected: IC 80K/86K — 98K/104K
Expiry: 2026-01-30
```

### Phase 2: Подтверждение

Пользователь видит предположение и может:
- ✅ Подтвердить
- ✏️ Скорректировать
- ❌ Отклонить

---

## 11. Execution Phases

| Функция | Phase 1 | Phase 2 |
|---------|---------|---------|
| **Delta Hedge (futures)** | Auto | Auto |
| **H4 Options Buy** | Auto (with ladder) | Auto |
| **Cat Ears** | Alert → Manual | Auto (confirm) |
| **DTE Roll** | Alert → Manual | Auto (confirm) |
| **D1 Roll** | Alert → Manual | Auto (confirm) |
| **IC Exit** | Alert → Manual | Auto (confirm) |

---

## 12. Option Order Execution

### Лимитка с Ladder

```python
async def buy_option_with_ladder(strike):
    """
    Покупка опциона с постепенным повышением IV.
    """
    current_iv = get_current_iv(strike)
    limit_iv = current_iv - 0.1  # -0.1 IV point
    
    for attempt in range(5):  # max 5 attempts
        order = place_limit_order(iv=limit_iv)
        await sleep(300)  # 5 минут
        
        if order.filled:
            return
        
        cancel(order)
        limit_iv += 0.1  # +0.1 IV
    
    alert("Order not filled after 25 min")
```

### Консолидация перед покупкой (H4)

```python
def detect_consolidation(h1_candles):
    """
    Inside bar ИЛИ low volatility.
    """
    last = h1_candles[-1]
    prev = h1_candles[-2]
    
    is_inside = last.high < prev.high and last.low > prev.low
    
    avg_range = mean([c.high - c.low for c in h1_candles[-10:]])
    low_vol = (last.high - last.low) < avg_range * 0.5
    
    return is_inside or low_vol
```

---

## 13. Analytics (Dashboard)

### IV/HV Chart

```
Источник IV: ATM strike с биржи (Deribit reference)
Источник HV: Расчёт по klines (20d)
```

---

## 14. Configuration

Stored in `hedger_config` table:

| Key | Default | Description |
|-----|---------|-------------|
| `target_delta` | 0.0 | Target portfolio delta |
| `threshold` | 0.003 | Deviation threshold |
| `max_order_size` | 0.1 | Max order size BTC |
| `hedge_interval_hours` | 1.0 | Check frequency |
| `cat_ears_qty_ratio` | 0.10 | Cat Ears size (10%) |
| `squeeze_percentile` | 25 | BB Width squeeze |
| `profit_target_pct` | 0.50 | IC exit at 50% profit |
| `min_dte_exit` | 7 | Close IC when DTE ≤ 7 |

### Dynamic Calculations

```python
# Gamma Threshold (dynamic)
gamma_threshold = threshold / (price * iv * sqrt(hedge_interval / 8760))

# 1σ Expected Move
one_sigma = price * iv * sqrt(dte / 365)
```

---

## 15. Data Flow

```
Bybit API (klines H1/H4/D1)
       │
       ▼
┌─────────────────┐
│ FractalCollector│ → fractals_cache (DB)
│ ├─ BB 1σ/2σ     │
│ ├─ Alligator    │
│ └─ Key Fractals │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ SignalDetector  │ → Check: цена закрылась за КФ?
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ DeltaHedgerBot  │ → Mode switch + Execute
└─────────────────┘
```

---

## 16. Files Reference

| File | Purpose |
|------|---------|
| `strategy_trade.md` | Original strategy v7.0 |
| `docs/tz/delta_hedger_bot.tz.md` | Bot TZ |
| `docs/tz/fractal_collector.tz.md` | Data collector TZ |
| `strategy/indicators/bollinger.py` | BB calculator |
| `strategy/indicators/fractals.py` | Williams Fractals |
| `strategy/indicators/alligator.py` | Alligator (TODO) |
| `bybit_options/services/hedger/` | Bot implementation |

---

## Audit Summary (2026-01-18)

| # | Topic | Resolution |
|---|-------|------------|
| 1 | H1 vs H4 Priority | H4 = эскалация (close futures → buy options) |
| 2 | Exit Conditions | Transformation rules (ratio, hedge, spread) |
| 3 | Gamma Threshold | Dynamic: `threshold / expected_move` |
| 4 | Cat Ears Structure | Debit spreads, long closer to ATM by greeks + spread |
| 5 | Spread Width | 6000 pts fixed, strike by IV/delta |
| 6 | Directional Bias | Configurable target_delta via config/Telegram |
| 7 | Squeeze Trend | By last KF breakout (D1 > H4) |
| 8 | IC Exit | 50% profit OR DTE ≤ 7 |

---

## See Also

- [Delta Hedger Bot TZ](tz/delta_hedger_bot.tz.md)
- [Fractal Collector TZ](tz/fractal_collector.tz.md)
