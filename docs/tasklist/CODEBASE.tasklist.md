# CODEBASE Tasklist

Status: TASKLIST_READY

## Tasks

- CODEBASE-001: Create bybit_options package skeleton (dirs + __init__.py + config/logging stubs).
  Depends on: none
  Acceptance Criteria:
  - bybit_options/ exists with listed subpackages.
  - Imports resolve for bybit_options.config.logging.

- CODEBASE-002: Move Pydantic models from data_models.py into bybit_options.models.
  Depends on: CODEBASE-001
  Acceptance Criteria:
  - data_models.py re-exports models to avoid breaking imports.
  - All imports in core/services/orchestration updated to new paths.

- CODEBASE-003: Move RiskEngine into bybit_options.core.
  Depends on: CODEBASE-002
  Acceptance Criteria:
  - risk_engine.py becomes a shim importing bybit_options.core.risk_engine.
  - RiskEngine remains pure (no I/O) and tests still pass.

- CODEBASE-004: Move BybitConnector into bybit_options.services.
  Depends on: CODEBASE-001
  Acceptance Criteria:
  - bybit_connector.py is a shim importing new module.
  - All callers updated to bybit_options.services.bybit_connector.

- CODEBASE-005: Move MarketDataService into bybit_options.services.
  Depends on: CODEBASE-004, CODEBASE-002
  Acceptance Criteria:
  - market_data_service.py is a shim importing new module.
  - Caching stays inside MarketDataService.

- CODEBASE-006: Move AnalysisOrchestrator into bybit_options.orchestration.
  Depends on: CODEBASE-005, CODEBASE-003
  Acceptance Criteria:
  - analysis_orchestrator.py becomes a shim.
  - CLI/API use the new orchestration module.

- CODEBASE-007: Move DisplayManager into bybit_options.reports.
  Depends on: CODEBASE-006
  Acceptance Criteria:
  - display_manager.py becomes a shim.
  - Report output unchanged for same inputs.

- CODEBASE-008: Create bybit_options.api app and move api_example into apps/api.py.
  Depends on: CODEBASE-006, CODEBASE-002
  Acceptance Criteria:
  - New FastAPI app lives in bybit_options.api.app.
  - api_example.py becomes a thin shim or is moved to apps/api.py.

- CODEBASE-009: Create bybit_options.cli.main and move main.py to apps/cli.py.
  Depends on: CODEBASE-006, CODEBASE-007
  Acceptance Criteria:
  - root main.py becomes a thin shim.
  - CLI still runs full analysis with same output.

- CODEBASE-010: Introduce storage interfaces + adapter for current database modules.
  Depends on: CODEBASE-001
  Acceptance Criteria:
  - bybit_options.storage.repositories defines Protocol/ABC interfaces.
  - database.py or trade_history.py uses an adapter implementing the interface.

- CODEBASE-011: Update scripts to import from bybit_options.*
  Depends on: CODEBASE-003, CODEBASE-005, CODEBASE-006
  Acceptance Criteria:
  - scripts run without changing CLI behavior.
  - No direct imports from legacy modules remain (except shims).

- CODEBASE-012: Add tests for core and services with mocked connector.
  Depends on: CODEBASE-003, CODEBASE-005
  Acceptance Criteria:
  - At least 3 unit tests for RiskEngine.
  - At least 1 integration-style test with mocked BybitConnector.

- CODEBASE-013: Update documentation to reflect new structure.
  Depends on: CODEBASE-009, CODEBASE-011
  Acceptance Criteria:
  - readme_md.md and INTEGRATION.md updated with new import paths.
  - project_structure_md.md reflects target structure.
- CODEBASE-014: Implement Delta Analytics Service.
  Depends on: CODEBASE-004, CODEBASE-010
  Acceptance Criteria:
  - `TradeIngestor` and `OrderbookIngestor` implemented in `services/delta/`.
  - `DeltaCalculator` aggregates metrics to DB.
  - Integrated into app lifespan.
