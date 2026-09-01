# Progress

What works, what remains, known issues, and decision history.

## Change Control

- last_checked_commit: <fill with commit hash>
- checked_at: <YYYY-MM-DD>

## Status

- Done:
  - **2026-01-20**: ✅ DELTA-002 — OrderbookCollector
    - Добавлен REST OrderbookCollector (polling=5s, limit=25 → top20) и расчет imbalance.
    - Исправлено сохранение orderbook_snapshots без `RETURNING id`, добавлен batch insert.
    - CLI: флаг `--orderbook`, поддержка совместного запуска с `--trades`.
    - Добавлены unit-тесты orderbook collector.
  - **2026-01-15**: 🔧 Устранена критическая утечка памяти cloudcode_cli (6ГБ → 0 процессов)
    - Процесс принудительно завершён: `pkill -9 cloudcode_cli`
    - Кэш очищен: `/home/dmitrii/.cache/cloud-code/` удалена
    - Cloud Code расширение отключено в `.config/Code/User/settings.json`
    - Добавлены исключения индексации в `.vscode/settings.json`: `node_modules`, `.git`, `dist`, `.cache`, `__pycache__`, `venv`
    - Результат: Доступная память вернулась с 3.5 ГБ → 5.0 ГБ ✓
  - **2026-01-16**: ✅ Validated Delta Models
    - Исправлена Pydantic валидация в `delta_models.py` (optional fields)
    - Добавлен тест `tests/test_delta_models.py`
  - **2026-01-17**: 🚀 **Delta Hedger Bot - Phase 1 (Core) Complete**
    - **HEDGER-001**: Создана структура сервиса и базовые модели (`HedgerMode`, `HedgeAction`).
    - **HEDGER-002**: Реализован `PositionMonitor` с агрегацией дельты (Futures+Options).
      - *Fix*: Внедрен `PositionFetchError` для предотвращения торговли при сбоях API (Critical).
    - **HEDGER-003**: Реализован `OrderExecutor` для лимитных ордеров (с retry logic).
    - **HEDGER-004**: Реализован `HedgerConfigLoader` (DB + Env support).
    - **HEDGER-005**: Созданы SQL миграции (`hedge_actions`, `hedger_config`).
    - **HEDGER-006**: Реализован основной класс `DeltaHedgerBot` (NEUTRAL mode logic).
    - **HEDGER-007**: Создан entry point скрипт `scripts/run_hedger.py` (supports `--dry-run`).
  - **2026-01-17**: 🧠 **Process Improvements**
    - Внедрен **Memory Bank Protocol** во всех 11 ролей агентов.
    - Создан workflow синхронизации контекста `.agent/workflows/memory-sync.md`.
  - **2026-01-24**: 🤖 **AMM Robot Production Ready (Stage 1-3)**
    - **FIX-001**: Dynamic Time-to-Expiry (T) calculation
    - **FIX-002**: Real-time spot price from linear tickers
    - **FIX-003**: Portfolio Greeks aggregation
    - **FIX-004**: Full reconciliation on startup
    - **FIX-005**: Unified trade log (`unified_trades` view)
    - **Stage 3**: Gatekeeper (Risk Director) — portfolio/leg gating + audit log
    - **GUI Backend**: Strategy CRUD, Portfolio Greeks, Risk Decisions, Engine Control APIs
  - **2026-01-24**: 📋 **AMM Architecture Decision**
    - **Decision**: AMM Robot = Executor, Trading Expert = Strategist
    - **Документы**: TZ-VOL-001, TZ-AMM-004 созданы и одобрены

- In progress:
  - **Volatility Intelligence Module** (TZ-VOL-001) — P0-P1
    - IVRankConnector, HVCalculator, SmileAnalyzer (SVI), ContextAPI
  - **AMM Dynamic Params + Agent Control** (TZ-AMM-004) — P1
    - Skew implementation, Agent Command API, Manual/Auto modes
  - **Delta Volume Analytics** — система анализа объёмной дельты для ML
    - DELTA-001: LargeTradeCollector (REST) — 🟡 Ready for execution

- Next:
  - DELTA-003: OpenInterestCollector
  - DELTA-005: DeltaAnalyzer
  - HEDGER-009: Integrate Signals into Bot
  - HEDGER-010: Implement Directional Mode

## 2026-01-19 23:20 — DELTA-004: TimescaleDB Migration

**Status:** ✅ Completed

**Summary:** Создана и применена миграция TimescaleDB для Delta Volume Analytics.

**What was done:**
- Создан `database_migrations/008_create_delta_hypertables.sql`
- Hypertables: `large_trades`, `orderbook_snapshots`, `open_interest`
- Continuous aggregates: `delta_metrics_1m`, `delta_metrics_5m`, `delta_metrics_1h`
- Config table: `delta_config` (BTCUSDT=5, ETHUSDT=50)
- Retention policies: 180d / 30d / 365d
- Роль `dmitrii` создана для peer auth

**Documentation created:**
- `docs/tz/delta_volume_analytics.tz.md` — полное ТЗ
- `docs/tasklist/DELTA.tasklist.md` — tasklist с 9 задачами
- `docs/tz/DELTA-004.task.md` — детальное ТЗ для агента
- `docs/tz/DELTA-001.task.md` — ТЗ для LargeTradeCollector

**Also fixed:**
- FIX-001: API startup не блокируется (Delta Services опциональны через `ENABLE_DELTA_SERVICES`)

## 2026-01-18 18:55 — Implementer: FRAC-003

**Status:** ✅ Completed

**Summary:** Реализован FractalStorage (UPSERT + retention) и расширена схема `fractals_cache`.
- Добавлена миграция с новыми полями (symbol, candle_time, fractal_type, BB 1σ/2σ, alligator_teeth) и индексами.
- Реализован `FractalStorage` с UPSERT по `(symbol, timeframe, fractal_type, candle_time)` и retention 100 записей.
- Добавлены unit-тесты на SQL-генерацию/adapter-level поведение (idempotency, update, retention).

**Files:**
- Created: `database_migrations/006_extend_fractals_cache.sql`
- Created: `strategy/storage/fractal_storage.py`
- Created: `tests/test_fractal_storage.py`

## 2026-01-18 20:51 — Implementer: HIST-001

**Status:** ✅ Completed

**Summary:** Расширен Bybit API клиент методами истории сделок и ордеров с cursor-пагинацией и retry при rate-limit.
- Добавлены Pydantic модели для execution/order history.
- Реализованы get_execution_history/get_order_history с обработкой retCode 10006 и HTTP 429.
- Добавлены unit-тесты для cursor, rate-limit retry и парсинга моделей.

**Files:**
- Created: `bybit_options/models/trade_history.py`
- Modified: `bybit_options/models/__init__.py`
    - Modified: `bybit_options/services/bybit_connector.py`
    - Created: `tests/test_trade_history_connector.py`

## 2026-01-19 18:33 — Implementer: HIST-003

**Status:** ✅ Completed

**Summary:** Реализован TradeHistoryLoader (backfill+sync) с окнами ≤7 дней, UPSERT storage boundary, CLI и unit-тесты.
- Расширены repository interfaces для UPSERT trades/orders и получения курсоров времени.
- Добавлены SQLAlchemy-адаптеры с ON CONFLICT UPSERT для trades/orders.
- Реализован `TradeHistoryLoader` с оконной нарезкой, cursor pagination, логированием прогресса.
- Добавлен CLI `scripts/sync_trades.py`.
- Добавлены unit-тесты на window slicing, cursor pagination, sync clamp.

**Files:**
- Created: `bybit_options/services/trade_history_loader.py`
- Created: `scripts/sync_trades.py`
- Created: `tests/test_trade_history_loader.py`
- Modified: `bybit_options/storage/repositories.py`
- Modified: `bybit_options/storage/adapters/database.py`
- Modified: `bybit_options/storage/adapters/__init__.py`
- Modified: `bybit_options/storage/__init__.py`
- Modified: `database.py`

## 2026-01-19 18:49 — Implementer: HIST-004

**Status:** ✅ Completed

**Summary:** Реализован PortfolioSyncer (hourly snapshots) с storage boundary, SQLAlchemy adapter, CLI и unit-тестами.
- Добавлен репозиторий и SQLAlchemy-адаптер для `portfolio_snapshots`.
- Реализован `PortfolioSyncer` с формированием snapshot row (positions+wallet+greeks).
- Добавлен CLI `scripts/sync_portfolio.py` (hourly loop + --once).
- Добавлены unit-тесты на структуру snapshot, сериализацию positions и вызов репозитория.

**Files:**
- Created: `bybit_options/services/portfolio_syncer.py`
- Created: `scripts/sync_portfolio.py`
- Created: `tests/test_portfolio_syncer.py`
- Modified: `bybit_options/storage/repositories.py`
- Modified: `bybit_options/storage/adapters/database.py`
- Modified: `bybit_options/storage/adapters/__init__.py`
- Modified: `bybit_options/storage/__init__.py`
- Modified: `database.py`

## 2026-01-19 19:25 — Implementer: HIST-006

**Status:** ✅ Completed

**Summary:** Добавлены API эндпоинты истории (trades/orders/portfolio) с keyset cursor-пагинацией.
- Новый router `/api/*` с фильтрами и пагинацией по времени + secondary key.
- Подключение router в FastAPI app.
- Добавлены Pydantic модели ответов и unit-тесты cursor encode/decode.

**Files:**
- Created: `bybit_options/api/routes/trade_history.py`
- Created: `tests/test_trade_history_cursor.py`
- Modified: `bybit_options/api/routes/__init__.py`
- Modified: `bybit_options/api/app.py`

## 2026-01-17 13:58 — Implementer: HEDGER-008

**Status:** ✅ Completed

**Summary:** Реализован `SignalDetector` и миграция для `fractals_cache`.
Класс проверяет пробои фракталов (H4 > H1) на основе данных из БД.

**Files:**
- Created: `bybit_options/services/hedger/signal_detector.py`
- Created: `tests/test_hedger/test_signal_detector.py`
- Created: `database_migrations/004_create_fractals_tables.sql`
- Modified: `bybit_options/services/hedger/models.py` (Fixed datetime.utcnow deprecation)

- Next:
  - HEDGER-010: Implement Directional Mode logic (target_delta update)
  - HEDGER-011: Historic Tests

## 2026-01-17 14:15 — Implementer: HEDGER-009

**Status:** ✅ Completed

**Summary:** Интегрировал `SignalDetector` в `DeltaHedgerBot`.
Бот теперь проверяет сигналы в каждом цикле и переключает режим (NEUTRAL <-> DIRECTIONAL/DEFENSIVE).
Конфигурация (режим) сохраняется в БД при изменении.

**Files:**
- Modified: `bybit_options/services/hedger/bot.py`
- Modified: `tests/test_hedger/test_bot.py`

- Next:
  - HEDGER-011: Historic Tests

## 2026-01-17 14:26 — Implementer: HEDGER-010

**Status:** ✅ Completed

**Summary:** Реализовал логику `DIRECTIONAL` режима.
Теперь при получении сигнала (H1 Breakout) бот не только переключает режим, но и обновляет `target_delta` (+0.01 для LONG, -0.01 для SHORT).
Это автоматически влияет на логику хеджирования в `check_and_hedge`.

**Files:**
- Modified: `bybit_options/services/hedger/bot.py`
- Modified: `tests/test_hedger/test_bot.py`

- Next:
  - [x] Phase 2: Signal Detection (HEDGER-008 to HEDGER-011) - **Completed 2026-01-17**
    - Implemented `SignalDetector`, `check_and_hedge` integration, Directional Mode, and Integration Tests.
    - Files: `signal_detector.py`, `bot.py`, `test_signal_detector.py`, `test_historical_integration.py`.
  - [ ] Phase 3: Defensive Mode (HEDGER-012 to HEDGER-015) - **In Progress**
    - [x] HEDGER-012: Implement Defensive Mode (Defensive logic, Option Buying) - **Completed 2026-01-17**
      - Files: `bot.py` (updated), `option_solver.py`, `test_defensive_mode.py`.

### Next Step
Proceed with HEDGER-013 (Option Management).

## 2026-01-17 14:38 — Implementer: Phase 2 Complete

**Status:** ✅ Completed

**Summary:** Реализована Phase 2 (Signal Detection & Directional Mode).
- **HEDGER-008**: Реализован `SignalDetector` (H1/H4 Fractal Breakouts).
- **HEDGER-009**: Интеграция `SignalDetector` в цикл бота.
- **HEDGER-010**: Реализована логика `DIRECTIONAL` режима (Target Delta shift).
- **HEDGER-011**: Написаны интеграционные тесты (`test_historical_integration.py`).

**Files:**
- `bybit_options/services/hedger/signal_detector.py`
- `bybit_options/services/hedger/bot.py`
- `tests/test_hedger/test_historical_integration.py`
- `database_migrations/004_create_fractals_tables.sql`

**Next:** Phase 3 (Defensive Mode)
- Known issues:

## 2026-01-17 14:50 — Implementer: HEDGER-012a

**Status:** ✅ Completed

**Summary:** Провел рефакторинг Defensive Mode по результатам Code Review.
- Исправлена проблема локали при парсинге дат экспирации.
- Реализована параметризация `base_coin` (поддержка ETH в будущем).
- Добавлено корректное округление цены опциона до `tickSize`.
- Вынесен price markup в конфигурацию (БД).
- Улучшено логирование.

**Files:**
- Modified: `bybit_options/services/hedger/option_solver.py`
- Modified: `bybit_options/services/hedger/bot.py`
- Modified: `bybit_options/services/hedger/models.py`
- Created: `database_migrations/005_add_option_config_fields.sql`
- Modified: `tests/test_hedger/test_defensive_mode.py`

**Next:** HEDGER-013 (Option Management)

## 2026-01-17 14:00 — Implementer: HEDGER-013

**Status:** ✅ Completed

**Summary:** Реализован механизм автоматического закрытия защитных опционов при выходе из Defensive режима (переходе в Neutral).
- Добавлен метод `_close_protection_options`
- Добавлен вызов при смене режима (`if previous_mode == DEFENSIVE and new_mode != DEFENSIVE`)
- Добавлен unit-тест `test_exit_defensive_mode_closes_options`

**Files:**
- `bybit_options/services/hedger/bot.py`
- `tests/test_hedger/test_defensive_mode.py`

**Next:** Phase 4 (Production Ready)

## 2026-01-17 15:00 — Implementer: HEDGER-014

**Status:** ✅ Completed

**Summary:** Реализованы интеграционные тесты полного цикла Defensive Mode.
- Протестирован сценарий: Neutral -> H4 Breakout -> Defensive (Buy Option) -> Stabilization -> Neutral (Sell Option).
- Подтверждена корректность записи логов в БД (`OPTIONS_BUY`, `OPTIONS_CLOSE`).
- Обновлены модели `HedgeAction` для валидации новых типов действий.

**Files:**
- `tests/test_hedger/test_defensive_integration.py`
- `bybit_options/services/hedger/models.py`

**Next:** Phase 4

## 2026-01-17 23:10 — Tech Lead: DOC-SYNC

**Status:** ✅ Completed

**Summary:** Синхронизация документации по результатам аудита. Устранены 6 противоречий между источниками истины.
- Создан `docs/ops/running.md` — единый файл runtime-конфигурации
- Создан `docs/architecture.md` — архитектура всей платформы
- Архивирован `.clinerules` → `docs/legacy/clinerules_december2025.md`
- Обновлён `.agent/conventions.md` — ссылка на running.md вместо hardcoded портов
- Обновлён `AGENTS.md` — добавлены новые документы в read order

**Files:**
- Created: `docs/ops/running.md`
- Created: `docs/architecture.md`
- Created: `docs/legacy/clinerules_december2025.md`
- Modified: `.agent/conventions.md`
- Modified: `AGENTS.md`

**Next:** HEDGER Phase 4 (Production Ready) или Frontend fixes

## 2026-01-31 00:08 — Trading Expert: Portfolio Analysis & Data Connection

**Status:** ✅ Completed

**Summary:**
- **Problem:** Initial analysis used stale/simulated data, showing a "Crisis" (Short Put $82k ITM).
- **Discovery:** Found `.env` keys were present. Switched to `main.py` for real data fetching.
- **Reality:** Actual portfolio is HEALTHY. Short Put is $76k (Safe). Total PnL +$66.
- **Protocol Update:** Updated `trading-expert` role to MANDATE `python3 main.py` execution before any analysis.

**Action:**
- Validated real positions via API.
- Confirmed no immediate roll needed.
- Updated `reports/latest_analysis.md` with live data.

**Risk:**
- **Low.** Portfolio is delta-neutral (+0.0025) and PnL positive.
- **Note:** Theta is slightly negative in report (-$0.05), needs monitoring.

## 2026-03-15 22:37 — Trading Expert: Portfolio Analysis & AI Hedger Integration

**Status:** ✅ Completed

**Summary:**
- **Problem:** Проведен анализ свежего состояния портфеля после интеграции `Bybit AI Trading Skill` и скрипта-генератора `ai_hedge_assistant.py`.
- **Discovery:** Текущая цена BTC выросла до $71,728. Equity: $996.43. Margin: 44.49% (Safe). Накопилась шорт-дельта (-0.02 BTC) из-за роста цены базового актива. Theta положительная (+$5.47/day).
- **Reality:** Скрипт `ai_hedge_assistant.py` успешно отработал и сгенерировал промпт для ИИ-ассистента на основе актуального `latest_analysis.md`.

**Action:**
- Данные обновлены через `python3 main.py`.
- Сгенерирован промпт для хеджирования через Bybit Skill.
- Предложено (опционально) выровнять дельту покупкой +0.02 BTC на фьюче, если требуется строгая нейтральность.
- Установлен мониторинг проданных колов на страйке $78k.

**Risk:**
- **Low-Medium.** Портфель слегка в шорт-дельте (-0.02 BTC), маржа в безопасной зоне (44.49%). Наблюдается рост положительной Веги.
