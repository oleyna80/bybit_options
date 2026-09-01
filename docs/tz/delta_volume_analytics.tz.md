# Техническое Задание: Delta Volume Analytics v1.0

**Статус:** ✅ APPROVED  
**Дата:** 2026-01-19  
**Обновлено:** 2026-01-19  
**Автор:** Tech Lead  
**Приоритет:** 🟡 MEDIUM (Feature)  

---

## 📋 Согласованные решения

| Вопрос | Решение |
|--------|--------|
| **Threshold (порог)** | Конфигурируемый через ENV/DB (BTC=5, ETH=50) |
| **Инструменты** | BTC/ETH на первом этапе |
| **OI** | Только фьючерсы (BTCUSDT perpetual) |
| **FractalEnricher** | Асинхронное обогащение (cron каждые 5 мин) |
| **Telegram** | Минимальный → Расширенный → С графиком |
| **Telegram schedule** | Каждые 4 часа + при пробое фрактала |
| **Retention** | 180-360 дней для ML training |

---

## 1. 🎯 Цель

Создать систему **анализа объёмной дельты** для улучшения точности сигналов опционной стратегии на базе ключевых фракталов.

### 1.1 Бизнес-контекст

**Текущая стратегия:**
- Базис: Аллигатор (Билл Вильямс) + Полосы Болинджера (1σ)
- Сигнал входа: Пробой **ключевого фрактала** (за пределами BB)
- Таймфреймы: H4 (spot), D1 (опционы)
- **Проблема:** Недостаточно информации о силе движения → ложные пробои

**Решение:**
Добавить фильтр по **институциональному потоку** через анализ:
1. **Filtered Delta** — крупные сделки (> 5 BTC / > 50 ETH)
2. **Absorbed Liquidity** — как киты защищают уровни
3. **Open Interest Delta** — изменение позиций на фьючерсах

### 1.2 Success Metrics

| Метрика | Цель | Измерение |
|---------|------|-----------|
| Data Collection Uptime | > 99% | Мониторинг gaps в БД |
| Data Latency | < 15 секунд | От сделки на бирже до БД |
| Signal Accuracy Improvement | +15-20% | Backtest после 2 месяцев сбора |
| False Breakout Reduction | -30% | Сравнение с/без Delta фильтра |

---

## 2. 📊 Концепция Delta Метриков

### 2.1 Filtered Delta (Крупные сделки)

```
Filtered Delta = Buy Volume (>5 BTC) - Sell Volume (>5 BTC)

Положительная Delta = Институционалы покупают (бычий сигнал)
Отрицательная Delta = Институционалы продают (медвежий сигнал)
```

**Применение к фракталам:**
```
Сценарий 1: Ключевой фрактал ВВЕРХ + Filtered Delta > +50 BTC (1H)
→ СИЛЬНЫЙ сигнал, подтверждён крупными покупками

Сценарий 2: Ключевой фрактал ВВЕРХ + Filtered Delta < -30 BTC
→ СЛАБЫЙ сигнал, возможная ловушка (divergence)
```

### 2.2 Absorbed Liquidity

```
Уровень 95,000$ — bid wall 20 BTC
Прошла сделка 15 BTC sell → absorbed_bid_liquidity = 15 BTC

Если уровень НЕ пробит → СИЛЬНАЯ защита
Если уровень пробит → wall была ЛОЖНОЙ (spoofing)
```

### 2.3 Open Interest Delta

```
+OI + ↑Price = Новые лонги (бычий)
+OI + ↓Price = Новые шорты (медвежий)
-OI + ↑Price = Закрытие шортов (short squeeze!)
-OI + ↓Price = Закрытие лонгов (panic sell)
```

### 2.4 Паттерны для детекции

| Паттерн | Признаки | Интерпретация |
|---------|----------|---------------|
| **Hidden Accumulation** | Delta +, Price flat | Киты накапливают скрытно |
| **Iceberg Orders** | Volume >> visible wall | Скрытые лимитные ордера |
| **Spoofing** | Wall исчезает без исполнения | Манипуляция |
| **Divergence** | Fractal ↑ + Delta ↓ | Возможная ловушка |

---

## 3. 🏗 Архитектура

### 3.1 High-Level Design

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DELTA VOLUME ANALYTICS SYSTEM                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  LAYER 1: DATA COLLECTION                                               │
│  ┌────────────────────┐  ┌────────────────────┐  ┌──────────────────┐  │
│  │ LargeTradeCollector│  │ OrderbookCollector │  │ OpenInterest     │  │
│  │ (REST, every 10s)  │  │ (REST, every 5s)   │  │ Collector (1min) │  │
│  └─────────┬──────────┘  └─────────┬──────────┘  └────────┬─────────┘  │
│            │                       │                      │             │
│            └───────────────────────┼──────────────────────┘             │
│                                    ↓                                    │
│  LAYER 2: STORAGE (TimescaleDB)                                         │
│  ┌────────────────────┐  ┌────────────────────┐  ┌──────────────────┐  │
│  │ large_trades       │  │ orderbook_snapshots│  │ open_interest    │  │
│  │ (hypertable)       │  │ (hypertable)       │  │ (hypertable)     │  │
│  └─────────┬──────────┘  └─────────┬──────────┘  └────────┬─────────┘  │
│            │                       │                      │             │
│            └───────────────────────┼──────────────────────┘             │
│                                    ↓                                    │
│  LAYER 3: AGGREGATION (Continuous Aggregates)                           │
│  ┌────────────────────┐  ┌────────────────────┐  ┌──────────────────┐  │
│  │ delta_metrics_1m   │  │ delta_metrics_5m   │  │ delta_metrics_1h │  │
│  │ (auto-refresh 30s) │  │ (auto-refresh 1m)  │  │ (auto-refresh 5m)│  │
│  └─────────┬──────────┘  └─────────┬──────────┘  └────────┬─────────┘  │
│            │                       │                      │             │
│            └───────────────────────┼──────────────────────┘             │
│                                    ↓                                    │
│  LAYER 4: ANALYTICS & REPORTING                                         │
│  ┌────────────────────┐  ┌────────────────────┐  ┌──────────────────┐  │
│  │ DeltaAnalyzer      │  │ FractalEnricher    │  │ TelegramReporter │  │
│  │ (metrics calc)     │  │ (add delta to fx)  │  │ (daily summary)  │  │
│  └────────────────────┘  └────────────────────┘  └──────────────────┘  │
│                                                                         │
│  LAYER 5: API & ML FEATURES                                             │
│  ┌────────────────────┐  ┌────────────────────┐                        │
│  │ API Endpoints      │  │ ML Feature Export  │                        │
│  │ /api/delta/*       │  │ (for training)     │                        │
│  └────────────────────┘  └────────────────────┘                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Data Flow

```
[Bybit REST API]
    │
    ├── /v5/market/recent-trade ──► LargeTradeCollector ──► large_trades
    │                                       │
    ├── /v5/market/orderbook ─────► OrderbookCollector ──► orderbook_snapshots
    │                                       │
    └── /v5/market/open-interest ──► OICollector ────────► open_interest
                                            │
                                            ↓
                              [TimescaleDB Continuous Aggregates]
                              (delta_metrics_1m, _5m, _1h)
                                            │
                                            ↓
                              ┌─────────────┴─────────────┐
                              │                           │
                    [DeltaAnalyzer]              [FractalEnricher]
                              │                           │
                              ↓                           ↓
                    [TelegramReporter]          [KeyFractal + Delta]
                    (Daily Summary)              (Enhanced Signal)
```

---

## 4. 🗄️ Database Schema

### 4.1 Tables Overview

| Table | Type | Purpose | Retention |
|-------|------|---------|-----------|
| `large_trades` | Hypertable | Сделки > 5 BTC | **180 days** |
| `orderbook_snapshots` | Hypertable | Стакан каждые 5s | 30 days |
| `open_interest` | Hypertable | OI каждую минуту | **365 days** |
| `delta_metrics_1m` | Cont. Aggregate | 1-минутные агрегаты | Auto |
| `delta_metrics_5m` | Cont. Aggregate | 5-минутные агрегаты | Auto |
| `delta_metrics_1h` | Cont. Aggregate | Часовые агрегаты | Auto |

### 4.2 Delta Config Table

```sql
-- Configurable thresholds for large trade filtering
CREATE TABLE IF NOT EXISTS delta_config (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL UNIQUE,
    threshold_qty NUMERIC(20, 8) NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Default values
INSERT INTO delta_config (symbol, threshold_qty) VALUES
    ('BTCUSDT', 5.0),
    ('ETHUSDT', 50.0)
ON CONFLICT (symbol) DO NOTHING;
```

### 4.2 Migration: 008_create_delta_hypertables.sql

```sql
-- Enable TimescaleDB extension (already enabled)
-- CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ============================================================================
-- TABLE: large_trades (whale trades >= 5 BTC)
-- ============================================================================

CREATE TABLE IF NOT EXISTS large_trades (
    timestamp TIMESTAMPTZ NOT NULL,
    exchange VARCHAR(20) NOT NULL CHECK (exchange IN ('bybit', 'deribit', 'binance')),
    market_type VARCHAR(20) NOT NULL CHECK (market_type IN ('spot', 'perpetual', 'futures')),
    symbol VARCHAR(50) NOT NULL,
    trade_id VARCHAR(100) NOT NULL,
    price NUMERIC(20, 8) NOT NULL CHECK (price > 0),
    quantity NUMERIC(20, 8) NOT NULL CHECK (quantity > 0),
    side VARCHAR(10) NOT NULL CHECK (side IN ('Buy', 'Sell')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT pk_large_trades PRIMARY KEY (timestamp, exchange, trade_id)
);

-- Convert to hypertable
SELECT create_hypertable(
    'large_trades',
    'timestamp',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_large_trades_symbol_time 
ON large_trades (symbol, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_large_trades_side_time 
ON large_trades (side, timestamp DESC);

-- ============================================================================
-- TABLE: orderbook_snapshots (top 20 levels)
-- ============================================================================

CREATE TABLE IF NOT EXISTS orderbook_snapshots (
    timestamp TIMESTAMPTZ NOT NULL,
    exchange VARCHAR(20) NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    bids JSONB NOT NULL,
    asks JSONB NOT NULL,
    bid_volume_total NUMERIC(20, 8) NOT NULL,
    ask_volume_total NUMERIC(20, 8) NOT NULL,
    imbalance NUMERIC(5, 4) NOT NULL CHECK (imbalance >= -1 AND imbalance <= 1),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT pk_orderbook_snapshots PRIMARY KEY (timestamp, exchange, symbol)
);

SELECT create_hypertable(
    'orderbook_snapshots',
    'timestamp',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

CREATE INDEX IF NOT EXISTS idx_orderbook_symbol_time 
ON orderbook_snapshots (symbol, timestamp DESC);

-- ============================================================================
-- TABLE: open_interest (for perpetuals)
-- ============================================================================

CREATE TABLE IF NOT EXISTS open_interest (
    timestamp TIMESTAMPTZ NOT NULL,
    exchange VARCHAR(20) NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    open_interest NUMERIC(20, 8) NOT NULL,
    open_interest_value NUMERIC(20, 2), -- in USD
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT pk_open_interest PRIMARY KEY (timestamp, exchange, symbol)
);

SELECT create_hypertable(
    'open_interest',
    'timestamp',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE
);

CREATE INDEX IF NOT EXISTS idx_oi_symbol_time 
ON open_interest (symbol, timestamp DESC);

-- ============================================================================
-- CONTINUOUS AGGREGATE: delta_metrics_1m
-- ============================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS delta_metrics_1m
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 minute', timestamp) AS bucket,
    exchange,
    symbol,
    SUM(CASE WHEN side = 'Buy' THEN quantity ELSE 0 END) AS buy_volume,
    SUM(CASE WHEN side = 'Sell' THEN quantity ELSE 0 END) AS sell_volume,
    SUM(CASE WHEN side = 'Buy' THEN quantity ELSE -quantity END) AS filtered_delta,
    COUNT(*) AS trade_count,
    AVG(price) AS avg_price,
    MIN(price) AS min_price,
    MAX(price) AS max_price
FROM large_trades
GROUP BY bucket, exchange, symbol
WITH NO DATA;

SELECT add_continuous_aggregate_policy('delta_metrics_1m',
    start_offset => INTERVAL '2 hours',
    end_offset => INTERVAL '10 seconds',
    schedule_interval => INTERVAL '30 seconds',
    if_not_exists => TRUE
);

-- ============================================================================
-- CONTINUOUS AGGREGATE: delta_metrics_5m
-- ============================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS delta_metrics_5m
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('5 minutes', timestamp) AS bucket,
    exchange,
    symbol,
    SUM(CASE WHEN side = 'Buy' THEN quantity ELSE 0 END) AS buy_volume,
    SUM(CASE WHEN side = 'Sell' THEN quantity ELSE 0 END) AS sell_volume,
    SUM(CASE WHEN side = 'Buy' THEN quantity ELSE -quantity END) AS filtered_delta,
    COUNT(*) AS trade_count,
    AVG(price) AS avg_price
FROM large_trades
GROUP BY bucket, exchange, symbol
WITH NO DATA;

SELECT add_continuous_aggregate_policy('delta_metrics_5m',
    start_offset => INTERVAL '6 hours',
    end_offset => INTERVAL '1 minute',
    schedule_interval => INTERVAL '1 minute',
    if_not_exists => TRUE
);

-- ============================================================================
-- CONTINUOUS AGGREGATE: delta_metrics_1h
-- ============================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS delta_metrics_1h
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 hour', timestamp) AS bucket,
    exchange,
    symbol,
    SUM(CASE WHEN side = 'Buy' THEN quantity ELSE 0 END) AS buy_volume,
    SUM(CASE WHEN side = 'Sell' THEN quantity ELSE 0 END) AS sell_volume,
    SUM(CASE WHEN side = 'Buy' THEN quantity ELSE -quantity END) AS filtered_delta,
    COUNT(*) AS trade_count,
    AVG(price) AS avg_price
FROM large_trades
GROUP BY bucket, exchange, symbol
WITH NO DATA;

SELECT add_continuous_aggregate_policy('delta_metrics_1h',
    start_offset => INTERVAL '1 day',
    end_offset => INTERVAL '5 minutes',
    schedule_interval => INTERVAL '5 minutes',
    if_not_exists => TRUE
);

-- ============================================================================
-- RETENTION POLICIES
-- ============================================================================

SELECT add_retention_policy('large_trades', INTERVAL '180 days', if_not_exists => TRUE);
SELECT add_retention_policy('orderbook_snapshots', INTERVAL '30 days', if_not_exists => TRUE);
SELECT add_retention_policy('open_interest', INTERVAL '365 days', if_not_exists => TRUE);

-- ============================================================================
-- VERIFY
-- ============================================================================

-- Check hypertables:
-- SELECT * FROM timescaledb_information.hypertables;

-- Check continuous aggregates:
-- SELECT * FROM timescaledb_information.continuous_aggregates;

-- Check policies:
-- SELECT * FROM timescaledb_information.jobs;
```

---

## 5. 📋 Acceptance Criteria (по задачам)

### DELTA-001: REST-based LargeTradeCollector

**Scope:** Переписать сбор крупных сделок с WebSocket на REST polling.

- [ ] AC1: Класс `LargeTradeCollector` использует `/v5/market/recent-trade`
- [ ] AC2: Polling каждые 10 секунд
- [ ] AC3: Фильтрация: BTC >= 5, ETH >= 50
- [ ] AC4: Deduplication по `trade_id`
- [ ] AC5: Graceful shutdown (SIGTERM)
- [ ] AC6: Logging с прогрессом (trades/min)
- [ ] AC7: CLI: `python scripts/run_delta_collector.py --trades`

**Files:**
- `bybit_options/services/delta/collectors/large_trade_collector.py`
- `scripts/run_delta_collector.py`

---

### DELTA-002: REST-based OrderbookCollector

**Scope:** Сбор orderbook snapshots через REST.

- [ ] AC1: Класс `OrderbookCollector` использует `/v5/market/orderbook`
- [ ] AC2: Polling каждые 5 секунд
- [ ] AC3: Top 20 levels, хранение в JSONB
- [ ] AC4: Расчёт imbalance: (bid - ask) / (bid + ask)
- [ ] AC5: CLI: `python scripts/run_delta_collector.py --orderbook`

**Files:**
- `bybit_options/services/delta/collectors/orderbook_collector.py`

---

### DELTA-003: OpenInterestCollector

**Scope:** Сбор Open Interest для perpetual.

- [ ] AC1: Класс `OpenInterestCollector` использует `/v5/market/open-interest`
- [ ] AC2: Polling каждую минуту
- [ ] AC3: Расчёт OI Delta: `current_oi - previous_oi`
- [ ] AC4: CLI: `python scripts/run_delta_collector.py --oi`

**Files:**
- `bybit_options/services/delta/collectors/oi_collector.py`

---

### DELTA-004: TimescaleDB Migration

**Scope:** Создать hypertables и continuous aggregates.

- [ ] AC1: Миграция `008_create_delta_hypertables.sql`
- [ ] AC2: Hypertables: `large_trades`, `orderbook_snapshots`, `open_interest`
- [ ] AC3: Continuous aggregates: `delta_metrics_1m`, `_5m`, `_1h`
- [ ] AC4: Retention policies настроены
- [ ] AC5: Verify script проходит

---

### DELTA-005: DeltaAnalyzer

**Scope:** Сервис для расчёта метрик.

- [ ] AC1: Метод `get_hourly_delta(symbol, hours=1)` → dict
- [ ] AC2: Метод `get_daily_delta(symbol, date=today)` → dict
- [ ] AC3: Метод `get_cumulative_delta(symbol, days=7)` → dict
- [ ] AC4: Метод `detect_divergence(symbol, fractal_direction)` → bool
- [ ] AC5: Unit tests с mock данными

**Files:**
- `bybit_options/services/delta/analyzer.py`
- `tests/test_delta_analyzer.py`

---

### DELTA-006: FractalEnricher (Async)

**Scope:** Асинхронное обогащение ключевых фракталов Delta-данными.

**Architecture:** Cron-задача каждые 5 минут (не блокирует Fractal Collector)

```
[Fractal Collector] → Save basic fractal → Telegram (basic)
                              ↓
[FractalEnricher cron] → Query fractals without delta
                       → Enrich with Delta metrics
                       → Update DB
```

- [ ] AC1: Cron-сервис запускается каждые 5 минут
- [ ] AC2: Query: `SELECT * FROM fractals_cache WHERE delta_1h IS NULL`
- [ ] AC3: Для каждого фрактала → запрос Delta metrics за `timestamp - 1h/4h`
- [ ] AC4: Добавление полей: `delta_1h`, `delta_4h`, `oi_delta`, `confidence_score`
- [ ] AC5: `confidence_score` = f(delta alignment, fractal strength) — простые правила для MVP
- [ ] AC6: Systemd timer: `bybit-fractal-enricher.timer`

**Files:**
- `bybit_options/services/delta/enricher.py`
- `scripts/run_fractal_enricher.py`
- `scripts/systemd/bybit-fractal-enricher.service`
- `scripts/systemd/bybit-fractal-enricher.timer`
- `database_migrations/009_extend_fractals_delta.sql`

---

### DELTA-007: Telegram Reports

**Scope:** Отчёты в Telegram — периодические и по событиям.

**Schedule:**
- Каждые 4 часа (00:00, 04:00, 08:00, 12:00, 16:00, 20:00 UTC)
- При тестировании/пробое ключевого фрактала

**Phased Format:**

**Phase 1 (MVP) — Минимальный:**
```
📊 BTCUSDT Delta Report
━━━━━━━━━━━━━━━━━━━━━
📅 2026-01-19 | 12:00 UTC

🟢 Покупки: 350.5 BTC
🔴 Продажи: 280.3 BTC
📈 Delta: +70.2 BTC

📊 7d Cumulative: +150.3 BTC
📉 OI Change: +1,500 contracts
```

**Phase 2 — Расширенный:** (добавить top trades, alerts)
**Phase 3 — С графиком:** (matplotlib → image)

**Acceptance Criteria:**
- [ ] AC1: Использовать существующий `TelegramAlerter`
- [ ] AC2: Формат MVP (минимальный)
- [ ] AC3: Systemd timer: каждые 4 часа
- [ ] AC4: Триггер при пробое фрактала (интеграция с Fractal Collector)
- [ ] AC5: CLI: `python scripts/send_delta_report.py --now`

**Files:**
- `bybit_options/services/delta/reporter.py`
- `scripts/send_delta_report.py`
- `scripts/systemd/bybit-delta-report.timer`

---

### DELTA-008: API Endpoints

**Scope:** REST API для фронтенда.

- [ ] AC1: `GET /api/delta/metrics?symbol=BTCUSDT&interval=1h&limit=24`
- [ ] AC2: `GET /api/delta/summary?symbol=BTCUSDT` (daily stats)
- [ ] AC3: `GET /api/delta/divergence?symbol=BTCUSDT` (current divergence)
- [ ] AC4: Response includes `filtered_delta`, `oi_delta`, `imbalance`

**Files:**
- `bybit_options/api/routes/delta.py`

---

### DELTA-009: Collector Orchestrator + Systemd

**Scope:** Автозапуск collectors.

- [ ] AC1: `DeltaCollectorOrchestrator` управляет всеми collectors
- [ ] AC2: Systemd unit: `bybit-delta-collector.service`
- [ ] AC3: Запуск при старте WSL (интеграция с `wsl_startup.sh`)
- [ ] AC4: Health check endpoint или файл

**Files:**
- `bybit_options/services/delta/orchestrator.py`
- `scripts/systemd/bybit-delta-collector.service`

---

## 6. 📁 Файловая структура

```
bybit_options/
├── models/
│   └── delta_models.py              # ✅ Уже есть (доработать)
├── services/
│   └── delta/
│       ├── __init__.py              # ✅ Уже есть (обновить exports)
│       ├── database_config.py       # ✅ Уже есть
│       ├── storage_service.py       # ✅ Уже есть (доработать для OI)
│       ├── collectors/              # 🆕 NEW
│       │   ├── __init__.py
│       │   ├── base_collector.py    # Abstract base
│       │   ├── large_trade_collector.py
│       │   ├── orderbook_collector.py
│       │   └── oi_collector.py
│       ├── analyzer.py              # 🆕 NEW (DELTA-005)
│       ├── enricher.py              # 🆕 NEW (DELTA-006)
│       ├── reporter.py              # 🆕 NEW (DELTA-007)
│       └── orchestrator.py          # 🆕 NEW (DELTA-009)
├── api/
│   └── routes/
│       └── delta.py                 # 🆕 NEW (DELTA-008)

database_migrations/
└── 008_create_delta_hypertables.sql # 🆕 NEW (DELTA-004)

scripts/
├── run_delta_collector.py           # 🆕 NEW (DELTA-001)
├── send_delta_report.py             # 🆕 NEW (DELTA-007)
└── systemd/
    └── bybit-delta-collector.service # 🆕 NEW (DELTA-009)
```

---

## 7. ⏱️ Оценка времени

| Задача | Оценка | Зависимости |
|--------|--------|-------------|
| DELTA-001: LargeTradeCollector (REST) | 2-3 часа | — |
| DELTA-002: OrderbookCollector (REST) | 2 часа | DELTA-001 |
| DELTA-003: OICollector | 1-2 часа | DELTA-001 |
| DELTA-004: TimescaleDB Migration | 1 час | — |
| DELTA-005: DeltaAnalyzer | 2-3 часа | DELTA-004 |
| DELTA-006: FractalEnricher | 2-3 часа | DELTA-005 |
| DELTA-007: Telegram Report | 1-2 часа | DELTA-005 |
| DELTA-008: API Endpoints | 1-2 часа | DELTA-005 |
| DELTA-009: Orchestrator + Systemd | 1-2 часа | DELTA-001..003 |
| **Итого** | **14-20 часов** | 3-4 дня работы |

---

## 8. 🚀 Порядок выполнения

```
Phase 1 (Foundation): DELTA-004 → DELTA-001 → DELTA-002 → DELTA-003
Phase 2 (Analytics): DELTA-005 → DELTA-006
Phase 3 (Reporting): DELTA-007 → DELTA-008 → DELTA-009
```

---

## 9. 🔮 Future Enhancements (Phase 4+)

| Feature | Description | Priority |
|---------|-------------|----------|
| **ML Feature Export** | Export для training XGBoost/LightGBM | 🟡 |
| **Grafana Dashboard** | Real-time visualization | 🟢 |
| **Multi-exchange** | Deribit, Binance OI | 🟢 |
| **Absorbed Liquidity** | Расчёт absorbed bid/ask walls | 🟡 |
| **Spoofing Detection** | Детекция ложных стен | 🔴 |

---

## 10. Appendix

### A. Bybit API Reference

```
GET /v5/market/recent-trade
- category: spot | linear
- symbol: BTCUSDT
- limit: 1-1000 (default 500)

GET /v5/market/orderbook
- category: spot | linear
- symbol: BTCUSDT
- limit: 1-500 (default 25)

GET /v5/market/open-interest
- category: linear
- symbol: BTCUSDT
- intervalTime: 5min | 15min | 30min | 1h | 4h | 1d
```

### B. ML Feature Vector

```python
# При формировании ключевого фрактала:
features = {
    # Fractal features
    'fractal_type': 'up',           # up | down
    'distance_to_bb': 0.015,        # % за пределами BB
    'alligator_trend': 'bullish',   # Lips > Teeth > Jaw
    
    # Delta features (🆕 NEW)
    'filtered_delta_1h': +35.5,     # BTC
    'filtered_delta_4h': +120.3,    # BTC
    'cumulative_delta_7d': +450.0,  # BTC
    'oi_delta_1h': +1500,           # contracts
    'oi_delta_4h': +5000,           # contracts
    'orderbook_imbalance': +0.65,   # [-1, 1]
    
    # Target
    'price_change_4h': +2.5         # % change in 4 hours
}
```

---

## Next Steps

```
Start DELTA-004 (TimescaleDB Migration)
```
