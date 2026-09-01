# 🎯 Задача: DELTA-004 — TimescaleDB Migration

**Статус:** 🟡 READY FOR EXECUTION  
**Приоритет:** HIGH  
**Оценка времени:** 1-1.5 часа  
**Исполнитель:** Backend Developer  

---

## 📋 Контекст

Мы внедряем систему **Delta Volume Analytics** для сбора и анализа объёмной дельты крупных сделок. Это позволит улучшить точность сигналов опционной стратегии.

**Полное ТЗ проекта:** [delta_volume_analytics.tz.md](delta_volume_analytics.tz.md)

**Текущая задача:** Создать TimescaleDB hypertables и continuous aggregates для хранения данных.

---

## 🎯 Цель

Создать SQL миграцию для Delta Analytics с:
- 3 hypertables: `large_trades`, `orderbook_snapshots`, `open_interest`
- 3 continuous aggregates: `delta_metrics_1m`, `delta_metrics_5m`, `delta_metrics_1h`
- Retention policies
- Config table для конфигурируемых порогов

---

## ✅ Acceptance Criteria

- [ ] AC1: Файл `database_migrations/008_create_delta_hypertables.sql` создан
- [ ] AC2: Таблица `large_trades` — hypertable с chunk_interval 1 day
- [ ] AC3: Таблица `orderbook_snapshots` — hypertable с chunk_interval 1 day
- [ ] AC4: Таблица `open_interest` — hypertable с chunk_interval 7 days
- [ ] AC5: Таблица `delta_config` для конфигурируемых порогов (BTC=5, ETH=50)
- [ ] AC6: Continuous aggregate `delta_metrics_1m` (refresh каждые 30 сек)
- [ ] AC7: Continuous aggregate `delta_metrics_5m` (refresh каждую минуту)
- [ ] AC8: Continuous aggregate `delta_metrics_1h` (refresh каждые 5 минут)
- [ ] AC9: Retention policies: large_trades=180 days, orderbook=30 days, open_interest=365 days
- [ ] AC10: Миграция применяется без ошибок: `psql -f 008_create_delta_hypertables.sql`

---

## 📁 Файлы

### Создать:

```
database_migrations/008_create_delta_hypertables.sql
```

---

## 🗄️ Database Schema

### Environment

```
Host: localhost
Port: 5432
Database: trading_platform
User: trading_user
Password: (см. .env файл)
TimescaleDB version: 2.24.0 ✅ уже установлен
```

### Таблица: large_trades

```sql
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
```

### Таблица: orderbook_snapshots

```sql
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
```

### Таблица: open_interest

```sql
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
```

### Таблица: delta_config (для конфигурируемых порогов)

```sql
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

### Continuous Aggregate: delta_metrics_1m

```sql
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
```

### Continuous Aggregate: delta_metrics_5m

```sql
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
```

### Continuous Aggregate: delta_metrics_1h

```sql
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
```

### Retention Policies

```sql
SELECT add_retention_policy('large_trades', INTERVAL '180 days', if_not_exists => TRUE);
SELECT add_retention_policy('orderbook_snapshots', INTERVAL '30 days', if_not_exists => TRUE);
SELECT add_retention_policy('open_interest', INTERVAL '365 days', if_not_exists => TRUE);
```

---

## 🧪 Validation

После применения миграции проверить:

```bash
# Подключиться к БД
PGPASSWORD=<SET_IN_LOCAL_ENV> psql -h localhost -U trading_user -d trading_platform

# Проверить hypertables
SELECT * FROM timescaledb_information.hypertables;
# Ожидаемый результат: large_trades, orderbook_snapshots, open_interest

# Проверить continuous aggregates
SELECT * FROM timescaledb_information.continuous_aggregates;
# Ожидаемый результат: delta_metrics_1m, delta_metrics_5m, delta_metrics_1h

# Проверить policies (retention + refresh)
SELECT hypertable_name, policy_name, config FROM timescaledb_information.jobs WHERE hypertable_name IS NOT NULL;
# Ожидаемый результат: 6 записей (3 retention + 3 refresh)

# Проверить delta_config
SELECT * FROM delta_config;
# Ожидаемый результат: BTCUSDT=5.0, ETHUSDT=50.0
```

---

## ⚠️ Важно

1. **НЕ удаляй существующие таблицы** — используй `IF NOT EXISTS`
2. **Используй `if_not_exists` для policies** — чтобы миграция была idempotent
3. **Проверь что TimescaleDB extension включен** — уже должен быть

---

## 📝 Шаблон миграции

```sql
-- ============================================================================
-- Migration: 008_create_delta_hypertables.sql
-- Description: Create TimescaleDB hypertables for Delta Volume Analytics
-- Author: [agent name]
-- Date: 2026-01-19
-- ============================================================================

-- Ensure TimescaleDB extension is enabled
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- ============================================================================
-- TABLE: large_trades
-- ============================================================================
-- [вставить код из схемы выше]

-- ============================================================================
-- TABLE: orderbook_snapshots  
-- ============================================================================
-- [вставить код из схемы выше]

-- ... и т.д.
```

---

## 🚀 Следующий шаг (после выполнения)

После успешного выполнения этой задачи → перейти к **DELTA-001** (LargeTradeCollector).

---

## Checklist перед сдачей

- [ ] Файл миграции создан
- [ ] Миграция применена без ошибок
- [ ] Все 3 hypertables созданы
- [ ] Все 3 continuous aggregates созданы
- [ ] Retention policies настроены
- [ ] delta_config содержит дефолты
- [ ] Validation queries прошли
