# Workflow vs Codebase — Reviewer Report

## Key Findings (Risks + Evidence)

1) **WS broadcast load/rate-limit risk**
- Evidence: `bybit_options/api/app.py` starts a broadcast loop that calls `AnalysisOrchestrator.run_full_analysis()` when clients exist.
- Risk: This can increase Bybit API traffic linearly with broadcast interval and connected clients, causing rate limit issues or slowdowns.

2) **Tight coupling in API module**
- Evidence: `bybit_options/api/app.py` imports root-level `option_board_utils.py`, `websocket_manager.py`, `payoff_calculator.py`, DB utilities, and strategy modules.
- Risk: Makes packaging/refactor harder; increases import-time side effects surface.

3) **Database import-time failure surface**
- Evidence: `database.py` raises if `DATABASE_URL` is missing at import time.
- Risk: Any environment missing DB config will hard-fail API import/startup, even for endpoints that don’t need DB.

4) **Duplicate WS manager patterns**
- Evidence: `websocket_manager.py` defines a global singleton getter, while `bybit_options/api/app.py` also manages `_ws_manager` lifecycle.
- Risk: Two competing patterns can lead to confusion or subtle bugs if both are used.

5) **Options board fetch inefficiencies**
- Evidence: `bybit_options/api/app.py` fetches instruments and then fetches tickers per symbol batch; currently hard-limited to 50 symbols.
- Risk: UX limitations (partial board), plus repeated instrument fetch loops per request; might need caching and clearer `limit` semantics.

## Mitigation Recommendations (No code changes in this task)

- Add explicit config toggles:
  - WS broadcast enable/disable and interval via env vars.
  - Options-board `limit` parameter and default.
- Move toward a single WS manager lifecycle pattern (either global singleton or app lifespan-managed).
- Reduce DB hard dependency at import-time (lazy init or optional DB features).
- Add observability:
  - log request counts / Bybit call counts per minute
  - include correlation id per analysis run

## Task Card → Next Role (QA)

## Task ID

WF-QA-001

## Assigned Role

QA

## Goal

Define and run a minimal verification checklist that proves workflow functionality: CLI, API endpoints, WS streaming, options board.

## Inputs (read first)

- files:
  - `.agent/workflow/bybit_options_workflow.md`
  - `bybit_options/cli/main.py`
  - `bybit_options/api/app.py`
  - `websocket_manager.py`
  - `tests/`
- constraints:
  - No code changes; produce a runnable checklist + evidence.

## Steps

1. Propose a post-stage validation checklist (commands + expected outputs).
2. Identify missing automated tests and the minimal additions needed later.

## Acceptance Criteria (testable)

- AC1: Checklist includes CLI run, `/api/v1/options-board`, `/api/v1/payoff-chart`, and `/ws/portfolio`.
- AC2: Each checklist step includes expected response fields / success conditions.

