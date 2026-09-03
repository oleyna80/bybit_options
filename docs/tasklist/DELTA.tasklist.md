# DELTA Volume Analytics - Tasklist

Status: TASKLIST_READY

## Summary

Система анализа объёмной дельты для улучшения точности сигналов опционной стратегии.

**TZ:** [delta_volume_analytics.tz.md](../tz/delta_volume_analytics.tz.md)  
**Estimated:** 14-20 часов (3-4 дня)  
**Priority:** 🟡 MEDIUM  
**Status:** ✅ APPROVED

---

## Phase 1: Foundation (Data Collection)

### DELTA-001: REST-based LargeTradeCollector
**Status:** ✅ DONE (2026-01-19)  
**Depends on:** none  
**Estimate:** 2-3 часа

Переписать сбор крупных сделок с WebSocket на REST polling.

**Acceptance Criteria:**
- [x] Класс `LargeTradeCollector` использует `/v5/market/recent-trade`
- [x] Polling каждые 10 секунд
- [x] Фильтрация: BTC >= 5, ETH >= 50
- [x] Deduplication по `trade_id`
- [x] Graceful shutdown (SIGTERM)
- [x] Logging с прогрессом (trades/min)
- [x] CLI: `python scripts/run_delta_collector.py --trades`

**Files:**
- ✅ Created: `bybit_options/services/delta/collectors/__init__.py`
- ✅ Created: `bybit_options/services/delta/collectors/base_collector.py`
- ✅ Created: `bybit_options/services/delta/collectors/large_trade_collector.py`
- ✅ Created: `scripts/run_delta_collector.py`
- ✅ Created: `tests/test_delta/test_large_trade_collector.py`

---

### DELTA-002: REST-based OrderbookCollector
**Status:** ✅ DONE (2026-01-20)  
**Depends on:** DELTA-001  
**Estimate:** 2 часа

Сбор orderbook snapshots через REST.

**Acceptance Criteria:**
- [x] Класс `OrderbookCollector` использует `/v5/market/orderbook`
- [x] Polling каждые 5 секунд
- [x] Top 20 levels, хранение в JSONB
- [x] Расчёт imbalance: (bid - ask) / (bid + ask)
- [x] CLI: `python scripts/run_delta_collector.py --orderbook`
- [x] AC10: Совместный запуск `--trades --orderbook`

**Files:**
- ✅ Created: `bybit_options/services/delta/collectors/orderbook_collector.py`
- ✅ Created: `tests/test_delta/test_orderbook_collector.py`

---

### DELTA-003: OpenInterestCollector
**Status:** ✅ DONE (2026-01-20)  
**Depends on:** DELTA-001  
**Estimate:** 1-2 часа

Сбор Open Interest для perpetual.

**Acceptance Criteria:**
- [x] Класс `OpenInterestCollector` использует `/v5/market/open-interest`
- [x] Polling каждую минуту
- [x] AC8: Совместный запуск `--trades --orderbook --oi`
- [x] CLI: `python scripts/run_delta_collector.py --oi`

**Files:**
- ✅ Created: `bybit_options/services/delta/collectors/open_interest_collector.py`
- ✅ Created: `tests/test_delta/test_open_interest_collector.py`

**Files:**
- Create: `bybit_options/services/delta/collectors/oi_collector.py`
- Create: `tests/test_delta/test_oi_collector.py`

---

### DELTA-004: TimescaleDB Migration
**Status:** ✅ DONE (2026-01-19)  
**Depends on:** none  
**Estimate:** 1 час

Создать hypertables и continuous aggregates.

**Acceptance Criteria:**
- [x] Миграция `008_create_delta_hypertables.sql`
- [x] Hypertables: `large_trades`, `orderbook_snapshots`, `open_interest`
- [x] Continuous aggregates: `delta_metrics_1m`, `_5m`, `_1h`
- [x] Retention policies настроены
- [x] Verify script проходит

**Files:**
- ✅ Created: `database_migrations/008_create_delta_hypertables.sql`

---

## Phase 2: Analytics

### DELTA-005: DeltaAnalyzer
**Status:** ✅ DONE (2026-01-20)  
**Depends on:** DELTA-004  
**Estimate:** 2-3 часа

Сервис для расчёта Delta метрик.

**Acceptance Criteria:**
- [x] Метод `get_hourly_delta(symbol, hours=1)` → dict
- [x] Метод `get_daily_delta(symbol, date=today)` → dict
- [x] Метод `get_cumulative_delta(symbol, days=7)` → dict
- [x] Метод `detect_divergence(symbol, fractal_direction)` → bool
- [x] Метод `get_orderbook_imbalance(symbol, minutes=5)` → dict
- [x] Метод `get_oi_change(symbol, hours=24)` → dict
- [x] Unit tests с mock данными (10 passed)

**Files:**
- ✅ Created: `bybit_options/services/delta/analyzer.py`
- ✅ Created: `tests/test_delta/test_analyzer.py`

---

### DELTA-006: FractalEnricher (Async)
**Status:** ✅ DONE (2026-01-20)  
**Depends on:** DELTA-005  
**Estimate:** 2-3 часа

**Асинхронное** обогащение ключевых фракталов Delta-данными (cron каждые 5 минут).

**Architecture:**
```
[Fractal Collector] → Save basic fractal → Telegram (basic)
                              ↓
[FractalEnricher cron] → Query fractals without delta
                       → Enrich with Delta metrics
                       → Update DB
```

**Acceptance Criteria:**
- [x] Cron-сервис запускается каждые 5 минут
- [x] Query: `SELECT * FROM fractals_cache WHERE delta_1h IS NULL`
- [x] Добавление полей: `delta_1h`, `delta_4h`, `delta_24h`, `oi_delta`, `confidence_score`
- [x] `confidence_score` = простые правила для MVP
- [x] Systemd timer: `bybit-fractal-enricher.timer`
- [x] Unit tests (6 passed)

**Files:**
- ✅ Created: `bybit_options/services/delta/enricher.py`
- ✅ Created: `scripts/run_fractal_enricher.py`
- ✅ Created: `scripts/systemd/bybit-fractal-enricher.service`
- ✅ Created: `scripts/systemd/bybit-fractal-enricher.timer`
- ✅ Created: `database_migrations/009_extend_fractals_delta.sql`
- ✅ Created: `tests/test_delta/test_enricher.py`

---

## Phase 3: Reporting & API

### DELTA-007: Telegram Reports
**Status:** TODO  
**Depends on:** DELTA-005  
**Estimate:** 1-2 часа

Отчёты в Telegram — периодические и по событиям.

**Schedule:**
- Каждые 4 часа (00:00, 04:00, 08:00, 12:00, 16:00, 20:00 UTC)
- При пробое ключевого фрактала

**Phased Format:**
- Phase 1 (MVP): Минимальный текст
- Phase 2: Расширенный (top trades, alerts)
- Phase 3: С графиком (matplotlib)

**Acceptance Criteria:**
- [ ] Использовать существующий `TelegramAlerter`
- [ ] Формат MVP (минимальный)
- [ ] Systemd timer: каждые 4 часа
- [ ] Триггер при пробое фрактала (интеграция с Fractal Collector)
- [ ] CLI: `python scripts/send_delta_report.py --now`

**Files:**
- Create: `bybit_options/services/delta/reporter.py`
- Create: `scripts/send_delta_report.py`
- Create: `scripts/systemd/bybit-delta-report.timer`

---

### DELTA-008: API Endpoints
**Status:** ✅ DONE (2026-01-20)  
**Depends on:** DELTA-005  
**Estimate:** 1-2 часа

REST API для фронтенда и интеграций.

**Acceptance Criteria:**
- [x] `GET /api/delta/metrics?symbol=BTCUSDT&hours=24`
- [x] `GET /api/delta/summary?symbol=BTCUSDT` (daily stats)
- [x] `GET /api/delta/cvd?symbol=BTCUSDT&days=7` (CVD time series)
- [x] `GET /api/delta/divergence?symbol=BTCUSDT&fractal_direction=bullish`
- [x] `GET /api/delta/imbalance?symbol=BTCUSDT&minutes=5`
- [x] `GET /api/delta/oi-change?symbol=BTCUSDT&hours=24`
- [x] Pydantic response models
- [x] Router подключён к FastAPI app
- [x] Unit tests (8 passed)

**Files:**
- ✅ Created: `bybit_options/api/routes/delta.py`
- ✅ Modified: `bybit_options/api/routes/__init__.py`
- ✅ Modified: `bybit_options/api/app.py`
- ✅ Created: `tests/test_delta/test_api.py`

---

### DELTA-009: Collector Orchestrator + Systemd
**Status:** TODO  
**Depends on:** DELTA-001, DELTA-002, DELTA-003  
**Estimate:** 1-2 часа

Автозапуск collectors.

**Acceptance Criteria:**
- [ ] `DeltaCollectorOrchestrator` управляет всеми collectors
- [ ] Systemd unit: `bybit-delta-collector.service`
- [ ] Запуск при старте WSL (интеграция с `wsl_startup.sh`)
- [ ] Health check endpoint или файл

**Files:**
- Create: `bybit_options/services/delta/orchestrator.py`
- Create: `scripts/systemd/bybit-delta-collector.service`
- Modify: `scripts/wsl_startup.sh`

---

## Recommended Execution Order

```
         ┌─────────────┐
         │ DELTA-004   │ (TimescaleDB Migration)
         │    1h       │
         └──────┬──────┘
                │
    ┌───────────┼───────────┐
    │           │           │
┌───▼───┐  ┌────▼────┐  ┌───▼───┐
│DELTA  │  │ DELTA   │  │DELTA  │
│ -001  │  │  -002   │  │ -003  │
│ 2-3h  │  │   2h    │  │ 1-2h  │
└───┬───┘  └────┬────┘  └───┬───┘
    │           │           │
    └───────────┼───────────┘
                │
         ┌──────▼──────┐
         │  DELTA-009  │ (Orchestrator)
         │    1-2h     │
         └──────┬──────┘
                │
         ┌──────▼──────┐
         │  DELTA-005  │ (Analyzer)
         │    2-3h     │
         └──────┬──────┘
                │
    ┌───────────┼───────────┐
    │           │           │
┌───▼───┐  ┌────▼────┐  ┌───▼───┐
│DELTA  │  │ DELTA   │  │DELTA  │
│ -006  │  │  -007   │  │ -008  │
│ 2-3h  │  │  1-2h   │  │ 1-2h  │
└───────┘  └─────────┘  └───────┘
```

---

## Quick Fixes (Before Phase 1)

### FIX-001: Remove Delta Services from API Startup
**Status:** TODO  
**Estimate:** 30 min

Текущие WebSocket-based ingestors блокируют startup API.

**Solution:** Закомментировать или сделать опциональными в `app.py` (lines 143-155).

---

## Notes

- TimescaleDB 2.24.0 уже установлен ✅
- TelegramAlerter уже есть ✅
- Существующие Pydantic models в `delta_models.py` можно использовать
- Существующий `StorageService` нужно расширить для OI

## Согласованные решения

| Вопрос | Решение |
|--------|--------|
| Threshold | Конфигурируемый через ENV/DB (BTC=5, ETH=50) |
| Инструменты | BTC/ETH на первом этапе |
| OI | Только фьючерсы (BTCUSDT perpetual) |
| FractalEnricher | Асинхронное обогащение (cron каждые 5 мин) |
| Telegram | Минимальный → Расширенный → С графиком |
| Telegram schedule | Каждые 4 часа + при пробое фрактала |
| Retention | 180-360 дней для ML training |
