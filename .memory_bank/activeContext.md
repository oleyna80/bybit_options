# Active Context

- **Active Task**: None (DELTA-002 completed)
- **Role**: Orchestrator / Planner
- **Goal**: Установить следующую задачу после DELTA-002 (вероятно, опционные стратегии или HEDGER-017).
- **Recent Accomplishments**:
    - Реализован `OrderbookCollector` с polling=5s, limit=25 и обрезкой до 20 уровней.
    - Добавлено batch-сохранение orderbook snapshots без `RETURNING id`.
    - Добавлен CLI флаг `--orderbook` и совместный запуск с `--trades`.
    - Добавлены unit-тесты для orderbook collector.
    - Тикет DELTA-002 полностью проверен и закрыт.
**Last updated:** 2026-03-16 15:30

**Recent decisions:**
- Implemented `OptionSolver` helper for selecting hedging options.
- `OrderExecutor` used for placing option orders.
- Defensive mode buys options once upon entry.
- Uses `unittest.IsolatedAsyncioTestCase` for new tests.
- **Phase 2 Complete:** Signal Detector (H1/H4) integration successful.
- **Directional Logic:** H1 Breakout long/short shifts target delta by ±0.01.
- **Defensive Logic:** H4 Breakout triggers DEFENSIVE strategy (Options Buying - Pending implementation).
- Memory Bank Protocol is fully active.

**Open questions:**
- Phase 3 requires `OptionsOrderExecutor` (buying options at specific strikes).
- Need to calculate "Nearest Strike to Short Leg" for Iron Condor protection (as per TZ). Do we have Iron Condor logic? No, we are building standalone Hedger. Assumes monitoring existing portfolio.
- **Dependency:** Does `PositionMonitor` provide Greek exposure breakdown per leg? Yes.
