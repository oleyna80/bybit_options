# CODEBASE Architecture + Codebase Plan

Recommended reasoning effort: high

## Goals
- Create a maintainable package structure with clear boundaries.
- Keep RiskEngine pure and deterministic (no I/O).
- Keep async I/O isolated in services/connectors.
- Preserve current CLI/API entry points while migrating incrementally.
- Keep frontend and strategy modules decoupled from core risk logic.

## Target directory structure

bybit_options/
  __init__.py
  api/
    app.py
    routes/
      portfolio.py
      health.py
  cli/
    main.py
  core/
    risk_engine.py
    greeks.py
    portfolio.py
    calculations/
  models/
    positions.py
    greeks.py
    portfolio.py
    market_data.py
  services/
    bybit_connector.py
    market_data_service.py
    stream_manager.py
    websocket_manager.py
    iv_rank_service.py
    delta/
      ingestor.py
      calculator.py
      database.py
  orchestration/
    analysis_orchestrator.py
  reports/
    display_manager.py
  storage/
    repositories.py
    adapters/
      database.py
  config/
    settings.py
    logging.py
  utils/
    time.py
    parsing.py
apps/
  cli.py
  api.py
scripts/
  backfill_trades.py
  backfill_historical_data.py
  daily_iv_update.py
  get_option_board.py
  get_option_quotes.py
frontend/
  (unchanged)
strategy/
  (unchanged)

Notes:
- Keep root-level legacy scripts as thin shims during migration.
- New code imports from bybit_options.* only.

## Module responsibilities and boundaries
- bybit_options.core: Pure math and domain logic (Greeks, aggregation). No I/O.
- bybit_options.models: Pydantic models for public boundaries and validation.
- bybit_options.services: Async I/O (Bybit API, caching, websockets). No math.
- bybit_options.orchestration: Workflows that wire services + core.
- bybit_options.reports: Presentation formatting (Markdown/console).
- bybit_options.api: HTTP layer, input validation, mapping to orchestration.
- bybit_options.cli: CLI entry that configures logging/env and runs workflows.
- bybit_options.storage: Repository interfaces + adapters (DB or file). No domain logic.
- bybit_options.config: Environment, settings, logging config.
- apps/: Backward-compatible entry points (import from package).
- scripts/: One-off tasks that call services/orchestration.

## Data flow (ingestion -> normalization -> risk engine -> reports/api)
1) CLI/API receives request and validates inputs (Pydantic).
2) Orchestrator requests data from MarketDataService.
3) MarketDataService uses BybitConnector (async) to fetch raw data.
4) Raw responses are normalized into Pydantic models.
5) RiskEngine consumes normalized models and returns risk outputs.
6) Orchestrator aggregates results, adds warnings, attaches margin data.
7) Reports layer renders Markdown/console, or API layer returns JSON.

## Interfaces / contracts
- Pydantic models define input/output for RiskEngine and API responses.
- BybitConnector interface: async methods for positions, tickers, instruments.
- MarketDataService interface: async methods returning normalized models.
- Storage repository interface: save/load trades, portfolio snapshots, reports.
- Orchestrator interface: run_full_analysis(params) -> PortfolioRiskModel.

## Risks and trade-offs
- Incremental migration creates temporary duplicate files and shims.
- Import paths may break if moves are not staged carefully.
- Some scripts mix I/O and logic; refactor must keep behavior stable.
- Async boundaries require careful testing to avoid event loop issues.

## Logging / observability plan
- Central logging config in bybit_options.config.logging.
- Log levels from LOG_LEVEL; avoid logging secrets.
- Add request/analysis correlation id in orchestration and API.
- Keep logs structured (key=value) for later parsing.

## Testing strategy
- Unit tests for core calculations and model validation.
- Integration tests for MarketDataService with mocked BybitConnector.
- Contract tests for API request/response models.
- Optional E2E tests against Bybit testnet (separate env).

## Migration plan (stepwise)
1) Introduce bybit_options package skeleton and config/logging modules.
2) Move Pydantic models into bybit_options.models and add re-exports.
3) Move RiskEngine into bybit_options.core and update imports.
4) Move BybitConnector and MarketDataService into bybit_options.services.
5) Move AnalysisOrchestrator and DisplayManager into orchestration/reports.
6) Create bybit_options.cli and bybit_options.api with thin wrappers.
7) Add storage interfaces and adapters, update call sites.
8) Update scripts to import from bybit_options.*
9) Add tests and update docs to reflect new layout.

Status: PLAN_APPROVED
