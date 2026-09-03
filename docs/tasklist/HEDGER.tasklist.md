# Delta Hedger Bot Tasklist

Status: TASKLIST_READY
Source: docs/tz/delta_hedger_bot.tz.md (APPROVED)
Created: 2026-01-16

---

## Overview

Декомпозиция ТЗ Delta Hedger Bot v1.0 на атомарные задачи.

**Phases:**
- Phase 1: Core (MVP) — HEDGER-001 to HEDGER-007
- Phase 2: Signal Detection — HEDGER-008 to HEDGER-011
- Phase 3: Defensive Mode — HEDGER-012 to HEDGER-015
- Phase 4: Production Ready — HEDGER-016 to HEDGER-020

---

## Phase 1: Core (MVP)

### HEDGER-001: Создать структуру директорий и базовые модели ✅ DONE

**Status:** ✅ Completed 2026-01-17

**Description:**
Создать директорию `bybit_options/services/hedger/` со всеми необходимыми файлами и Pydantic моделями.

**Acceptance Criteria:**
- AC1: Директория `bybit_options/services/hedger/` создана
- AC2: Файл `__init__.py` экспортирует: `DeltaHedgerBot`, `HedgerConfig`, `HedgerMode`
- AC3: Файл `models.py` содержит Pydantic модели: `HedgerMode`, `HedgerConfig`, `FractalSignal`, `OrderResult`, `HedgeAction`
- AC4: Все модели проходят валидацию: `python -c "from bybit_options.services.hedger import HedgerConfig"`

**Files to create:**
```
bybit_options/services/hedger/
├── __init__.py
├── models.py
├── config.py
```

---

### HEDGER-002: Реализовать PositionMonitor ✅ DONE

**Status:** ✅ Completed 2026-01-17

**Description:**
Создать класс `PositionMonitor` для получения текущей дельты портфеля (опционы + фьючерсы).

**Acceptance Criteria:**
- AC1: Файл `position_monitor.py` создан в `bybit_options/services/hedger/`
- AC2: Класс `PositionMonitor` имеет метод `async get_portfolio_delta() -> float`
- AC3: Метод агрегирует дельту опционов и фьючерсов
- AC4: Unit-тест с mocked connector проходит: `pytest tests/test_hedger/test_position_monitor.py`

**Files to create:**
```
bybit_options/services/hedger/position_monitor.py
tests/test_hedger/__init__.py
tests/test_hedger/test_position_monitor.py
```

---

### HEDGER-003: Реализовать OrderExecutor ✅ DONE

**Status:** ✅ Completed 2026-01-17

**Description:**
Создать класс `OrderExecutor` для размещения лимитных ордеров с retry логикой.

**Acceptance Criteria:**
- AC1: Файл `order_executor.py` создан в `bybit_options/services/hedger/`
- AC2: Класс `OrderExecutor` имеет метод `async place_limit_order(symbol, side, size, price) -> OrderResult`
- AC3: Реализован exponential backoff при rate limit (max 3 retries)
- AC4: Unit-тест с mocked connector проходит: `pytest tests/test_hedger/test_order_executor.py`

**Files to create:**
```
bybit_options/services/hedger/order_executor.py
tests/test_hedger/test_order_executor.py
```

---

### HEDGER-004: Реализовать HedgerConfig loader ✅ DONE

**Status:** ✅ Completed 2026-01-17 (implemented in HEDGER-001)

**Description:**
Создать загрузчик конфигурации из БД и/или .env файла.

**Acceptance Criteria:**
- AC1: Файл `config.py` содержит класс `HedgerConfigLoader`
- AC2: Метод `async load_from_db(pool) -> HedgerConfig` читает из таблицы `hedger_config`
- AC3: Метод `load_from_env() -> HedgerConfig` читает из переменных окружения с fallback на defaults
- AC4: Конфигурация включает: `threshold=0.003`, `directional_bias_long=0.01`, `directional_bias_short=-0.01`

---

### HEDGER-005: Создать SQL миграции для hedger ✅ DONE

**Depends on:** none

**Description:**
Создать SQL миграции для таблиц `hedge_actions` и `hedger_config`.

**Acceptance Criteria:**
- [x] AC1: Файл `database_migrations/003_create_hedger_tables.sql` создан
- [x] AC2: Таблица `hedge_actions` создаётся с индексами (4 индекса: time, mode, status, trigger)
- [x] AC3: Таблица `hedger_config` создаётся с начальными значениями (12 конфигурационных параметров)
- [x] AC4: Миграция выполняется без ошибок: `psql -f database_migrations/003_create_hedger_tables.sql`

**Completed:** 2026-01-17

**Files created:**
```
database_migrations/003_create_hedger_tables.sql
```

---

### HEDGER-006: Реализовать DeltaHedgerBot (NEUTRAL mode only) ✅ DONE

**Status:** ✅ Completed 2026-01-17

**Depends on:** HEDGER-002, HEDGER-003, HEDGER-004, HEDGER-005 (all ✅)

**Description:**
Создать основной класс `DeltaHedgerBot` с поддержкой только NEUTRAL режима.

**Acceptance Criteria:**
- [x] AC1: Файл `bot.py` создан в `bybit_options/services/hedger/`
- [x] AC2: Класс `DeltaHedgerBot` имеет методы: `start()`, `stop()`, `check_and_hedge()`
- [x] AC3: В NEUTRAL режиме target_delta = 0.0
- [x] AC4: При deviation > threshold размещается limit order через OrderExecutor
- [x] AC5: Действия логируются в таблицу `hedge_actions`
- [x] AC6: Бот работает в бесконечном цикле с check_interval_seconds

**Files created:**
```
bybit_options/services/hedger/bot.py
tests/test_hedger/test_bot.py
```

---

### HEDGER-007: Создать entry point скрипт ✅ DONE

**Status:** ✅ Completed 2026-01-17

**Depends on:** HEDGER-006

**Description:**
Создать `scripts/run_hedger.py` для запуска бота.

**Acceptance Criteria:**
- [x] AC1: Файл `scripts/run_hedger.py` создан
- [x] AC2: Скрипт инициализирует `BybitConnector`, `db_pool`, `HedgerConfig`
- [x] AC3: Запускает бота через `bot.start()`
- [x] AC4: Обрабатывает gracefully shutdown (SIGINT/SIGTERM)

**Files created:**
```
scripts/run_hedger.py
```

---

## Phase 2: Signal Detection (H1/H4 Fractals)

### HEDGER-008: Реализовать SignalDetector ✅ DONE

**Status:** ✅ Completed 2026-01-17

**Depends on:** HEDGER-001

**Description:**
Создать класс `SignalDetector` для обнаружения пробоев ключевых фракталов H1/H4.
*Implemented migration for fractals_cache table (004).*

**Acceptance Criteria:**
- [x] AC1: Файл `signal_detector.py` создан в `bybit_options/services/hedger/`
- [x] AC2: Класс имеет метод `async detect() -> Optional[FractalSignal]`
- [x] AC3: Проверяет H4 с более высоким приоритетом чем H1
- [x] AC4: Читает из таблиц `fractals_cache` и `perpetual_ohlcv`
- [x] AC5: Unit-тест с тестовыми данными проходит

**Files created:**
```
bybit_options/services/hedger/signal_detector.py
tests/test_hedger/test_signal_detector.py
database_migrations/004_create_fractals_tables.sql
```

---

### HEDGER-009: Интегрировать SignalDetector в DeltaHedgerBot ✅ DONE

**Status:** ✅ Completed 2026-01-17

**Depends on:** HEDGER-006, HEDGER-008

**Description:**
Добавить вызов SignalDetector в основной цикл бота.

**Acceptance Criteria:**
- [x] AC1: Метод `check_and_hedge()` вызывает `signal_detector.detect()`
- [x] AC2: Метод `_determine_mode()` возвращает корректный режим на основе сигнала
- [x] AC3: При отсутствии сигнала режим = NEUTRAL

---

### HEDGER-010: Добавить DIRECTIONAL режим ✅ DONE

**Status:** ✅ Completed 2026-01-17

**Depends on:** HEDGER-009

**Description:**
Реализовать переключение в DIRECTIONAL режим при пробое H1 фрактала.

**Acceptance Criteria:**
- [x] AC1: При H1 breakout LONG → target_delta = +0.01 BTC
- [x] AC2: При H1 breakout SHORT → target_delta = -0.01 BTC
- [x] AC3: Режим логируется: "Mode switched from NEUTRAL to DIRECTIONAL"
- [x] AC4: Действия хеджирования учитывают новый target_delta

---

### HEDGER-011: Добавить тесты на исторических данных ✅ DONE

**Status:** ✅ Completed 2026-01-17

**Depends on:** HEDGER-010

**Description:**
Создать интеграционные тесты с реальными историческими данными из БД.

**Acceptance Criteria:**
- [x] AC1: Тест проверяет детектирование сигналов на данных за последние 7 дней (Simulated)
- [x] AC2: Тест проверяет переключение режимов
- [x] AC3: Тесты используют тестовую БД или fixtures (Mocked DB fixtures)

---

## Phase 3: Defensive Mode

### HEDGER-012: Implement Defensive Mode ✅ DONE

**Status:** ✅ Completed 2026-01-17

**Depends on:** HEDGER-009

**Description:**
Implement logic to switch to DEFENSIVE mode on H4 breakout and buy protective options.

**Acceptance Criteria:**
- [x] AC1: When H4 breakout signal -> Mode switches to DEFENSIVE
- [x] AC2: `_buy_protection_options` is called
- [x] AC3: Protective options are purchased (Call for Long, Put for Short)
- [x] AC4: Retry logic for order placement

**Files created:**
- `bybit_options/services/hedger/option_solver.py`
- `tests/test_hedger/test_defensive_mode.py`

### HEDGER-012a: Refactor Defensive Mode (Code Review Fixes) 🔧 ✅ DONE

**Status:** ✅ Completed 2026-01-17

**Depends on:** HEDGER-012

**Description:**
Refactoring based on code review: Locale fix, configurable params, logging, tick size.

---

### HEDGER-013: Implement Option Management ✅ DONE

**Status:** ✅ Completed 2026-01-17

**Depends on:** HEDGER-012a

**Description:**
Implement logic to manage and exit defensive option positions when they are no longer needed (i.e., when the bot switches out of DEFENSIVE mode).

**Acceptance Criteria:**
- [x] AC1: When switching OUT of DEFENSIVE mode, protective options are closed
- [x] AC2: Filter for `side=Buy` (Long) positions and place `Sell` Limit order
- [x] AC3: Unit test `test_exit_defensive_mode_closes_options` passing

---

### HEDGER-014: Full Cycle Integration Tests (Defensive -> Neutral) ✅ DONE

**Status:** ✅ Completed 2026-01-17

**Depends on:** HEDGER-013

**Description:**
Implement integration tests simulating the full lifecycle:
1. Signal detected (H4 Breakout) -> Mode switch to DEFENSIVE -> Option Bought.
2. Market stabilizes (No Signal) -> Mode switch to NEUTRAL -> Option Sold.
3. Validate DB logs (`hedge_actions` table) for correct sequence of events.

**Acceptance Criteria:**
- [x] AC1: Integration test verifies DB records for `OPTIONS_BUY` and `OPTIONS_CLOSE`
- [x] AC2: Test handling of partial fills or failures during close? (Optional for now)
- [x] AC3: Verify `target_delta` returns to 0.0 after sequence.

**Estimated effort:** 1-2 hours

---

### HEDGER-015: Telegram Alerts ✅ DONE

**Status:** ✅ Completed 2026-01-18

**Depends on:** HEDGER-014

**Description:**
Implement Telegram notifications for critical bot events.

**Acceptance Criteria:**
- [x] AC1: TelegramAlerter service implemented in `bybit_options/services/telegram_alerter.py`
- [x] AC2: Bot sends alerts on START/STOP
- [x] AC3: Bot sends alerts on MODE CHANGE
- [x] AC4: Bot sends alerts on ORDER execution
- [x] AC5: Rate limiting and graceful degradation implemented

---

## Next Steps

Phase 3 completed. Proceed to Phase 4 (Production Ready) in `PRODUCT.tasklist.md`.

