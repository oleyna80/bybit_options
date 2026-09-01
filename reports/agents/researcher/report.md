# Workflow vs Codebase — Researcher Report

## Workflow-to-Code Mapping (Evidence)

Reference workflow: `.agent/workflow/bybit_options_workflow.md`

### Entry points

- CLI:
  - Canonical: `bybit_options/cli/main.py` (`main()` / `run()`)
  - Shims: `apps/cli.py`, `main.py`
- API:
  - Canonical: `bybit_options/api/app.py`
  - Shims: `apps/api.py`, `api_example.py`

### Core services

- `BybitConnector`: `bybit_options/services/bybit_connector.py`
- `MarketDataService`: `bybit_options/services/market_data_service.py`
- `RiskEngine` (pure): `bybit_options/core/risk_engine.py`
- `AnalysisOrchestrator`: `bybit_options/orchestration/analysis_orchestrator.py`
- `DisplayManager`: `bybit_options/reports/display_manager.py`
- Models:
  - Canonical: `bybit_options/models/*`
  - Legacy re-export: `data_models.py`

### Workflow steps (CLI flow)

1) Load env + logging
- Implemented in `bybit_options/cli/main.py` (`load_dotenv()`, `setup_logging()`).

2) Open connector
- Implemented in `bybit_options/cli/main.py` via `async with BybitConnector(...) as connector`.

3) Fetch positions + margin
- Implemented in `bybit_options/orchestration/analysis_orchestrator.py` calling `MarketDataService.fetch_all_positions()` and `fetch_margin_info()`.

4) Fetch greeks + prices in parallel
- Implemented in `bybit_options/orchestration/analysis_orchestrator.py` using service methods.

5) Process positions → PositionModel
- Implemented in `bybit_options/orchestration/analysis_orchestrator.py` (build positions) and `bybit_options/core/risk_engine.py` (`calculate_position_greeks`, `build_position_model`).

6) Enrich positions (IV metrics, slippage, gamma rent)
- Implemented across `bybit_options/orchestration/analysis_orchestrator.py` and `bybit_options/services/market_data_service.py` + `bybit_options/core/risk_engine.py`.

7) Aggregate portfolio risk + warnings
- Implemented in `bybit_options/core/risk_engine.py` (`build_portfolio_risk`, `generate_warnings`).

8) Display + save report
- Implemented in `bybit_options/reports/display_manager.py` and called by `bybit_options/cli/main.py`.

## Gaps / Mismatches (Highest impact)

1) **WS architecture mismatch**: workflow focuses on analysis flow; current WS broadcasting uses periodic `run_full_analysis()` in `bybit_options/api/app.py` when clients are connected, rather than event-driven updates from `LiveStateKeeper`.
2) **Options board coupling**: API uses `option_board_utils.py` at repo root, not a packaged module. Functional but not aligned with “package boundaries” goal.
3) **Rate-limit/load risk**: WS broadcast loop can generate significant Bybit traffic for each connected client period; needs explicit throttling/backoff and possibly caching.
4) **Storage boundary not yet used by app flows**: repository interfaces exist but are not the standard path for DB operations; the API still imports `database.py` directly.
5) **Workflow doc drift**: references to `api_example.py` as main API implementation are outdated (now shim).

## Suggested next tasks (dependency order)

- WEB-103: Stabilize `/api/v1/options-board` contract (already mostly done; ensure explicit schema + pagination/limit semantics).
- WEB-201: Frontend API client + types using current endpoints.
- WEB-102b (optional): Rework WS broadcasting to use `LiveStateKeeper` snapshots instead of polling `run_full_analysis()`.

## Task Card → Next Role (Reviewer)

## Task ID

WF-REVIEW-001

## Assigned Role

Reviewer

## Goal

Identify architectural and operational risks in current implementation relative to workflow (rate limits, coupling, error handling).

## Inputs (read first)

- files:
  - `bybit_options/api/app.py`
  - `websocket_manager.py`
  - `live_state_keeper.py`
  - `bybit_options/services/bybit_connector.py`
- constraints:
  - No code changes; report only.

## Steps

1. Review WS broadcasting flow end-to-end and assess load/rate-limit risks.
2. Review API module imports for boundary violations and refactor pressure.
3. List concrete risk mitigations (throttling, caching, toggles, observability).

## Acceptance Criteria (testable)

- AC1: Report lists at least 5 concrete risks with evidence.
- AC2: Report proposes mitigations with clear “done” criteria.

