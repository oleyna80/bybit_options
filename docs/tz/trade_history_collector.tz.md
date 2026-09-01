# Техническое Задание: Trade History Collector v1.0

**Статус:** 📝 DRAFT  
**Дата:** 2026-01-18  
**Автор:** Tech Lead  
**Приоритет:** 🟡 MEDIUM  

---

## 1. 🎯 Цель

Создать систему для:
- Загрузки истории сделок и ордеров с Bybit (за 6 месяцев)
- Сохранения в PostgreSQL
- Автоматической синхронизации при запуске WSL
- Предоставления данных для фронтенда через API

---

## 2. 📊 Архитектура

### 2.1 Компоненты

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    TRADE HISTORY SYSTEM                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. Bybit API Extension (HIST-001)                                      │
│     ├─ get_execution_history() — /v5/execution/list                     │
│     └─ get_order_history() — /v5/order/history                          │
│                                                                         │
│  2. Database Schema (HIST-002)                                          │
│     ├─ trades — история исполнений                                      │
│     ├─ orders — история ордеров                                         │
│     └─ portfolio_snapshots — снимки портфеля                            │
│                                                                         │
│  3. TradeHistoryLoader (HIST-003)                                       │
│     ├─ Backfill: загрузка за 6 месяцев                                  │
│     └─ Sync: инкрементальное обновление                                │
│                                                                         │
│  4. PortfolioSyncer (HIST-004)                                          │
│     ├─ Snapshot: позиции + греки + equity                               │
│     └─ Schedule: каждый час                                             │
│                                                                         │
│  5. Systemd Service (HIST-005)                                          │
│     └─ Auto-start on WSL boot                                           │
│                                                                         │
│  6. API Endpoints (HIST-006)                                            │
│     ├─ GET /api/trades                                                  │
│     ├─ GET /api/orders                                                  │
│     └─ GET /api/portfolio/history                                       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Поток данных

```
Bybit API
    │
    ├─► /v5/execution/list ─► TradeHistoryLoader ─► trades (DB)
    │
    ├─► /v5/order/history ──► TradeHistoryLoader ─► orders (DB)
    │
    └─► get_positions() ────► PortfolioSyncer ───► portfolio_snapshots (DB)
                                    │
                                    └─► При каждом запуске + каждый час
```

---

## 3. 📋 Acceptance Criteria

### HIST-001: Bybit API Extension

- [ ] AC1: Метод `get_execution_history(category, start_time, end_time, limit, cursor)`
- [ ] AC2: Метод `get_order_history(category, start_time, end_time, limit, cursor)`
- [ ] AC3: Поддержка пагинации через cursor
- [ ] AC4: Retry при rate limit
- [ ] AC5: Парсинг в Pydantic модели

### HIST-002: Database Schema

- [ ] AC1: Таблица `trades` с полями:
  - `exec_id` (UNIQUE)
  - `order_id`, `symbol`, `category`, `side`
  - `qty`, `price`, `exec_fee`
  - `exec_time`, `created_at`
- [ ] AC2: Таблица `orders` с полями:
  - `order_id` (UNIQUE)
  - `symbol`, `category`, `side`, `order_type`
  - `qty`, `price`, `avg_price`, `status`
  - `created_time`, `updated_time`
- [ ] AC3: Таблица `portfolio_snapshots` с полями:
  - `snapshot_time` (индекс)
  - `equity`, `margin_used`
  - `total_delta`, `total_gamma`, `total_vega`, `total_theta`
  - `positions` (JSONB)
- [ ] AC4: Индексы для быстрых выборок

### HIST-003: TradeHistoryLoader

- [ ] AC1: Backfill: загрузка trades/orders за N дней (default 180)
- [ ] AC2: Sync: загрузка только новых записей (после последнего exec_time)
- [ ] AC3: UPSERT логика (идемпотентность)
- [ ] AC4: CLI: `python scripts/sync_trades.py --backfill --days 180`
- [ ] AC5: Logging прогресса

### HIST-004: PortfolioSyncer

- [ ] AC1: Snapshot: собрать позиции + wallet + греки
- [ ] AC2: Store: сохранить в `portfolio_snapshots`
- [ ] AC3: Schedule: запуск каждый час
- [ ] AC4: CLI: `python scripts/sync_portfolio.py`

### HIST-005: Auto-start Service

- [ ] AC1: Скрипт `scripts/wsl_startup.sh`
- [ ] AC2: Backfill при первом запуске (если trades пустая)
- [ ] AC3: Sync последних данных
- [ ] AC4: Запуск PortfolioSyncer
- [ ] AC5: Инструкция для добавления в WSL autostart

### HIST-006: API Endpoints

- [ ] AC1: `GET /api/trades?symbol=&category=&from=&to=&limit=`
- [ ] AC2: `GET /api/orders?symbol=&category=&status=&from=&to=&limit=`
- [ ] AC3: `GET /api/portfolio/history?from=&to=&limit=`
- [ ] AC4: `GET /api/portfolio/current` (live)
- [ ] AC5: Pagination support

---

## 4. 📁 Файловая структура

```
bybit_options/
├── services/
│   ├── bybit_connector.py          # HIST-001: extend
│   ├── trade_history_loader.py     # HIST-003: NEW
│   └── portfolio_syncer.py         # HIST-004: NEW
├── models/
│   └── trade_models.py             # NEW: Pydantic models
├── api/
│   └── app.py                      # HIST-006: extend

database_migrations/
└── 007_create_trade_history.sql    # HIST-002: NEW

scripts/
├── sync_trades.py                  # HIST-003: CLI
├── sync_portfolio.py               # HIST-004: CLI
└── wsl_startup.sh                  # HIST-005: NEW
```

---

## 5. 🗄️ Database Schema

```sql
-- Migration 007

CREATE TABLE trades (
    id SERIAL PRIMARY KEY,
    exec_id VARCHAR(64) UNIQUE NOT NULL,
    order_id VARCHAR(64),
    symbol VARCHAR(50) NOT NULL,
    category VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    qty NUMERIC NOT NULL,
    price NUMERIC NOT NULL,
    exec_fee NUMERIC,
    exec_time TIMESTAMPTZ NOT NULL,
    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_trades_symbol_time ON trades (symbol, exec_time DESC);
CREATE INDEX idx_trades_category_time ON trades (category, exec_time DESC);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(64) UNIQUE NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    category VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    order_type VARCHAR(20),
    qty NUMERIC NOT NULL,
    price NUMERIC,
    avg_price NUMERIC,
    cum_exec_qty NUMERIC,
    cum_exec_fee NUMERIC,
    status VARCHAR(20) NOT NULL,
    created_time TIMESTAMPTZ NOT NULL,
    updated_time TIMESTAMPTZ,
    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_orders_symbol_time ON orders (symbol, created_time DESC);
CREATE INDEX idx_orders_status ON orders (status);

CREATE TABLE portfolio_snapshots (
    id SERIAL PRIMARY KEY,
    snapshot_time TIMESTAMPTZ NOT NULL,
    equity NUMERIC NOT NULL,
    available_balance NUMERIC,
    margin_used NUMERIC,
    total_delta NUMERIC,
    total_gamma NUMERIC,
    total_vega NUMERIC,
    total_theta NUMERIC,
    btc_price NUMERIC,
    positions JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_portfolio_time ON portfolio_snapshots (snapshot_time DESC);
```

---

## 6. 🔧 Bybit API Reference

### Execution List

```
GET /v5/execution/list

Params:
- category: option | linear | spot
- symbol: optional
- startTime: ms timestamp
- endTime: ms timestamp
- limit: 1-100 (default 50)
- cursor: for pagination

Response:
{
  "result": {
    "list": [
      {
        "execId": "...",
        "orderId": "...",
        "symbol": "BTC-30JAN26-100000-C",
        "side": "Buy",
        "execQty": "0.1",
        "execPrice": "1000.5",
        "execFee": "0.5",
        "execTime": "1705334400000"
      }
    ],
    "nextPageCursor": "..."
  }
}

Limit: 7 days per request for options
```

### Order History

```
GET /v5/order/history

Params:
- category: option | linear | spot
- symbol: optional
- startTime: ms timestamp
- endTime: ms timestamp  
- limit: 1-50 (default 20)
- cursor: for pagination

Response:
{
  "result": {
    "list": [
      {
        "orderId": "...",
        "symbol": "BTC-30JAN26-100000-C",
        "side": "Buy",
        "orderType": "Limit",
        "qty": "0.1",
        "price": "1000.0",
        "avgPrice": "1000.5",
        "cumExecQty": "0.1",
        "cumExecFee": "0.5",
        "orderStatus": "Filled",
        "createdTime": "1705334400000",
        "updatedTime": "1705334500000"
      }
    ],
    "nextPageCursor": "..."
  }
}
```

---

## 7. ⏱️ Оценка времени

| Задача | Оценка |
|--------|--------|
| HIST-001: Bybit API Extension | 1-2 часа |
| HIST-002: Database Schema | 0.5 часа |
| HIST-003: TradeHistoryLoader | 2-3 часа |
| HIST-004: PortfolioSyncer | 1-2 часа |
| HIST-005: WSL Autostart | 0.5 часа |
| HIST-006: API Endpoints | 1-2 часа |
| **Итого** | **6-10 часов** |

---

## 8. 🚀 Запуск

```bash
# Backfill (первый раз)
python scripts/sync_trades.py --backfill --days 180

# Инкрементальный sync
python scripts/sync_trades.py

# Portfolio snapshot
python scripts/sync_portfolio.py

# WSL autostart (добавить в ~/.bashrc или wsl.conf)
./scripts/wsl_startup.sh
```

---

## 9. Next Steps

```
Start HIST-001 (Bybit API Extension)
```
