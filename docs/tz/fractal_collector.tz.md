# Техническое Задание: Fractal Collector v1.0

**Статус:** 📝 DRAFT  
**Дата:** 2026-01-18  
**Автор:** Tech Lead  
**Приоритет:** 🔴 HIGH  

---

## 1. 🎯 Цель

Создать модуль `FractalCollector`, который:
- Загружает исторические свечи (klines) с Bybit API
- Рассчитывает Bollinger Bands (1σ, 2σ)
- Детектирует Williams Fractals
- Фильтрует "ключевые" фракталы (между 1σ и 2σ)
- Записывает результаты в таблицу `fractals_cache`

---

## 2. 📊 Архитектура

### 2.1 Компоненты

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      FRACTAL COLLECTOR                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. KlineLoader                                                         │
│     └─ Bybit API: GET /v5/market/kline                                  │
│     └─ Загружает H1, H4, D1 свечи для BTCUSDT                           │
│                                                                         │
│  2. BollingerCalculator (существующий)                                  │
│     └─ strategy/indicators/bollinger.py                                 │
│     └─ BB(20, 1.0) и BB(20, 2.0)                                        │
│                                                                         │
│  3. AlligatorIndicator (НОВЫЙ)                                          │
│     └─ strategy/indicators/alligator.py                                 │
│     └─ Jaw: SMMA(13), сдвиг 8                                           │
│     └─ Teeth: SMMA(8), сдвиг 5 (используется для КФ)                    │
│     └─ Lips: SMMA(5), сдвиг 3                                           │
│                                                                         │
│  4. FractalDetector (существующий)                                      │
│     └─ strategy/indicators/fractals.py                                  │
│     └─ Williams Fractals (5-bar)                                        │
│                                                                         │
│  5. KeyFractalFilter (НОВЫЙ, обновлённый)                               │
│     └─ Гибридный фильтр:                                                │
│        ├─ Условие 1: Fractal выше/ниже Alligator Teeth                  │
│        └─ Условие 2: Fractal между 1σ и 2σ BB                           │
│                                                                         │
│  6. FractalStorage                                                      │
│     └─ Записывает в fractals_cache                                      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Поток данных

```
Bybit API (klines H1/H4/D1)
       │
       ▼
┌─────────────────┐
│  KlineLoader    │ ─── candles (OHLCV)
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌────────────┐
│   BB   │ │ Alligator  │
│ 1σ/2σ  │ │  (Teeth)   │
└───┬────┘ └─────┬──────┘
    │            │
    └──────┬─────┘
           ▼
┌─────────────────┐
│ FractalDetector │ ─── all fractals (up/down)
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│         KeyFractalFilter                │
│  ├─ Fractal > Teeth (UP) или < Teeth   │
│  └─ 1σ < Fractal < 2σ                  │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│ fractals_cache  │ ─── PostgreSQL table
└─────────────────┘
```

### 2.3 Key Fractal Definition

Ключевой Фрактал должен удовлетворять **ДВУМ условиям**:

```
Условие 1 (Williams - относительно Alligator Teeth):
├─ Fractal UP: fractal.high > alligator.teeth
└─ Fractal DOWN: fractal.low < alligator.teeth

Условие 2 (Bollinger - зона значимости):
├─ Fractal UP: bb.upper_1sigma < fractal.high < bb.upper_2sigma
└─ Fractal DOWN: bb.lower_2sigma < fractal.low < bb.lower_1sigma
```

---

## 3. 📋 Acceptance Criteria

### FRAC-001: KlineLoader

- [x] AC1: Загружает последние 200 свечей для указанного таймфрейма
- [x] AC2: Поддерживает таймфреймы: H1 (60), H4 (240)
- [x] AC3: Возвращает список `[{time, open, high, low, close, volume}]`
- [x] AC4: Обрабатывает ошибки API (retry, logging)

> ✅ Реализовано: `strategy/data/kline_loader.py`

### FRAC-005: AlligatorIndicator (НОВЫЙ)

- [ ] AC1: Реализует Smoothed Moving Average (SMMA)
- [ ] AC2: Рассчитывает 3 линии:
  - Jaw (челюсть): SMMA(13), сдвиг 8 баров вперёд
  - Teeth (зубы): SMMA(8), сдвиг 5 баров вперёд — **используется для КФ**
  - Lips (губы): SMMA(5), сдвиг 3 баров вперёд
- [ ] AC3: Возвращает `{jaw, teeth, lips}` для текущего бара
- [ ] AC4: Обрабатывает недостаточное кол-во данных

### FRAC-002: KeyFractalFilter (обновлённый)

- [ ] AC1: Принимает: фракталы + BB значения + **Alligator Teeth**
- [ ] AC2: Фильтрует по **ДВУМ условиям**:
  - Условие 1 (Williams): Fractal UP > Teeth, Fractal DOWN < Teeth
  - Условие 2 (BB): `1σ < fractal.price < 2σ`
- [ ] AC3: Возвращает только фракталы, удовлетворяющие ОБА условия
- [ ] AC4: Логирует причину фильтрации

### FRAC-003: FractalStorage

- [ ] AC1: Записывает в `fractals_cache` с полями:
  - `symbol` (BTCUSDT)
  - `timeframe` (H1/H4/D1)
  - `fractal_type` (UP/DOWN)
  - `price` (fractal level)
  - `candle_time` (время свечи фрактала)
  - `bb_upper_1sigma`, `bb_lower_1sigma`
  - `bb_upper_2sigma`, `bb_lower_2sigma`
  - `alligator_teeth` (значение Teeth на момент фрактала)
  - `is_key_fractal` (true если прошёл оба фильтра)
  - `created_at`
- [ ] AC2: UPSERT логика (не дублировать)
- [ ] AC3: Хранить последние 100 фракталов

### FRAC-004: CollectorLoop

- [ ] AC1: Запускается как фоновый процесс
- [ ] AC2: Обновляет H1 каждые 5 минут
- [ ] AC3: Обновляет H4 каждые 15 минут
- [ ] AC4: Логирует новые ключевые фракталы
- [ ] AC5: Отправляет Telegram alert при новом ключевом фрактале

---

## 4. 📁 Файловая структура

```
strategy/
├── data/
│   ├── fractal_collector.py    # NEW: Main collector
│   ├── kline_loader.py         # NEW: Bybit klines fetcher
│   └── ...
├── indicators/
│   ├── bollinger.py            # EXISTS
│   ├── fractals.py             # EXISTS
│   └── key_fractal_filter.py   # NEW: 1σ-2σ filter
└── ...

scripts/
└── run_fractal_collector.py    # NEW: Entry point
```

---

## 5. 🗄️ Database Schema Update

```sql
-- Обновление fractals_cache (если нужно)
ALTER TABLE fractals_cache ADD COLUMN IF NOT EXISTS is_key_fractal BOOLEAN DEFAULT FALSE;
ALTER TABLE fractals_cache ADD COLUMN IF NOT EXISTS bb_upper_1sigma FLOAT;
ALTER TABLE fractals_cache ADD COLUMN IF NOT EXISTS bb_lower_1sigma FLOAT;
ALTER TABLE fractals_cache ADD COLUMN IF NOT EXISTS bb_upper_2sigma FLOAT;
ALTER TABLE fractals_cache ADD COLUMN IF NOT EXISTS bb_lower_2sigma FLOAT;
```

---

## 6. 🔗 Интеграция с SignalDetector

После реализации `FractalCollector`:

1. `SignalDetector` читает из `fractals_cache`
2. Проверяет: текущая цена пробила `is_key_fractal=true`?
3. Если да → генерирует `FractalSignal`
4. `DeltaHedgerBot` переключает режим

---

## 7. ⏱️ Оценка времени

| Задача | Оценка |
|--------|--------|
| FRAC-001: KlineLoader | 1 час |
| FRAC-002: KeyFractalFilter | 0.5 часа |
| FRAC-003: FractalStorage | 1 час |
| FRAC-004: CollectorLoop | 1 час |
| Интеграция + тесты | 1 час |
| **Итого** | **4-5 часов** |

---

## 8. 🚀 Запуск

```bash
# Standalone
python scripts/run_fractal_collector.py

# Или вместе с hedger
python scripts/run_hedger.py --with-fractal-collector
```

---

## Next Steps

```
Start FRAC-001 (KlineLoader)
```
