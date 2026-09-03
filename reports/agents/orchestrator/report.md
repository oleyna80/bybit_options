# Workflow vs Codebase — Orchestrator Summary

## Scope

Compare current repository state with `.agent/workflow/bybit_options_workflow.md` and summarize:
- what is already implemented and working
- what gaps remain (relative to the workflow + current WEB plan)
- what to do next

Constraint: no code changes as part of this research task.

## Sources Reviewed

- Workflow reference: `.agent/workflow/bybit_options_workflow.md`
- Backend package layout: `bybit_options/`
- API app: `bybit_options/api/app.py`
- Legacy shims: `main.py`, `api_example.py`, `bybit_connector.py`, `market_data_service.py`, `risk_engine.py`, `analysis_orchestrator.py`, `display_manager.py`, `data_models.py`
- WebSocket utilities: `websocket_manager.py`, `live_state_keeper.py`
- Tasklists: `docs/tasklist/CODEBASE.tasklist.md`, `docs/tasklist/WEB.tasklist.md`
- Tests: `tests/`

## What’s Already Ready (Matches Workflow)

- **CLI entrypoint present**:
  - Canonical: `bybit_options/cli/main.py`
  - Backward-compat: `apps/cli.py`, root `main.py`
- **Core services present and aligned**:
  - `BybitConnector`: `bybit_options/services/bybit_connector.py`
  - `MarketDataService`: `bybit_options/services/market_data_service.py`
  - `RiskEngine` is **pure** (no I/O): `bybit_options/core/risk_engine.py`
  - `AnalysisOrchestrator`: `bybit_options/orchestration/analysis_orchestrator.py`
  - `DisplayManager`: `bybit_options/reports/display_manager.py`
- **Models moved into package and re-exported**:
  - Canonical: `bybit_options/models/*`
  - Backward-compat: `data_models.py`
- **Reports flow works** (reports exist on disk): `reports/latest_analysis.md`, `reports/risk_analysis_*.md`
- **API app exists** with key endpoints:
  - `bybit_options/api/app.py` has `/api/v1/risk/portfolio`, `/api/v1/options-board`, `/api/v1/payoff-chart`, `/ws/portfolio`, etc.
- **Basic unit/integration tests exist** and pass locally:
  - `tests/test_risk_engine.py`
  - `tests/test_market_data_service.py`
  - `tests/test_storage_adapters.py`
  - `tests/test_option_board_utils.py`

## Gaps / Deviations vs Workflow (and/or Architecture Rules)

- **Workflow mentions `api_example.py` as “example”**; now it is a shim to `bybit_options.api.app`.
  - Not a problem, but docs/workflow may need a note that canonical is `bybit_options.api.app`.
- **API app imports several non-packaged modules directly** (`option_board_utils`, `websocket_manager`, `payoff_calculator`, DB helpers, strategy modules).
  - This partially conflicts with the earlier CODEBASE plan guideline “new code imports from `bybit_options.*` only”.
  - It’s functional, but increases coupling and makes packaging/refactor harder.
- **WebSocket broadcast implementation is functional but heavy**:
  - In `bybit_options/api/app.py`, the broadcast loop can call `AnalysisOrchestrator.run_full_analysis()` periodically when clients connected.
  - This increases API usage and can impact rate limits.
- **LiveStateKeeper not integrated as the source of truth for WS**:
  - `live_state_keeper.py` supports broadcasting, but API WS broadcasting is currently driven by orchestrator polling rather than keeper-driven updates.
- **Storage boundary added but not adopted by business flows yet**:
  - `bybit_options/storage/repositories.py` and adapter exist, but current runtime flows still use legacy DB access patterns elsewhere.

## Current Status vs Tasklists

- `docs/tasklist/CODEBASE.tasklist.md`: tasks 001–013 appear completed based on file presence and shims/tests/docs.
- `docs/tasklist/WEB.tasklist.md`:
  - WEB-101 (payoff endpoint): implemented and verified via live curl output.
  - WEB-102 (WS broadcasting): implemented (API-level periodic push).
  - WEB-103+ (frontend contract & UI integration): remaining.

## Recommended Next Step (Research Delegation)

We need a structured, role-by-role deep dive to:
1) validate workflow alignment at the “behavior level” (not only file presence),
2) identify architectural risks (coupling, rate limits, secrets/logging),
3) define the minimal next implementation sequence for WEB.

### Task Card → Next Role (Researcher)

## Task ID

WF-RESEARCH-001

## Assigned Role

Researcher

## Goal

Create a detailed “workflow-to-code mapping” with evidence and identify the highest-impact gaps.

## Inputs (read first)

- files:
  - `.agent/workflow/bybit_options_workflow.md`
  - `.agent/PROJECT_BRIEF.md`
  - `bybit_options/cli/main.py`
  - `bybit_options/orchestration/analysis_orchestrator.py`
  - `bybit_options/services/market_data_service.py`
  - `bybit_options/core/risk_engine.py`
  - `bybit_options/reports/display_manager.py`
  - `bybit_options/api/app.py`
- constraints:
  - No code changes; produce report only.

## Steps

1. Map each “workflow step” to concrete functions/files.
2. List mismatches and missing pieces (especially WS + options-board + caching boundaries).
3. Propose a small set of next tasks, in dependency order.

## Acceptance Criteria (testable)

- AC1: Report includes a table mapping workflow steps → functions/files.
- AC2: Report lists top 5 gaps with evidence and suggested fixes.

