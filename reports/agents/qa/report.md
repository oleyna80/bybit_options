# Workflow vs Codebase — QA Report

## Current Automated Coverage (observed)

- Unit tests:
  - `tests/test_risk_engine.py` (symbol parse, option greeks sign, iv metrics)
  - `tests/test_market_data_service.py` (positions fetched + category tagging)
  - `tests/test_storage_adapters.py` (adapter empty-input behavior)
  - `tests/test_option_board_utils.py` (symbol normalization in ticker fetch)

Gaps: No automated tests for FastAPI endpoints or WebSocket streaming behavior.

## Minimal Manual Verification Checklist (workflow-aligned)

Prereqs:
- `.env` has real `BYBIT_API_KEY` / `BYBIT_API_SECRET` (do not paste into chat)
- venv activated or call `./.venv/bin/python`

1) CLI workflow smoke
- Command: `./.venv/bin/python main.py`
- Pass: completes without exception and updates `reports/latest_analysis.md`.

2) API startup
- Command: `./.venv/bin/python -m uvicorn bybit_options.api.app:app --host 127.0.0.1 --port 8000`
- Pass: startup completes (no crash), logs show connector init.

3) Options board endpoint
- Command: `curl "http://127.0.0.1:8000/api/v1/options-board?base_coin=BTC"`
- Pass: JSON contains `underlying_price` and non-empty `options` array.

4) Payoff chart endpoint
- Command: `curl "http://127.0.0.1:8000/api/v1/payoff-chart?base_coin=BTC"`
- Pass: JSON contains `current_price`, `price_range`, `pnl`, `breakeven_points`, and `portfolio_summary`.

5) WebSocket endpoint
- Tool: any WS client (e.g. `wscat`, browser devtools, or frontend)
- URL: `ws://127.0.0.1:8000/ws/portfolio`
- Pass: receives `connection_established` message then periodic `portfolio_update` messages.

## Suggested Next Automated Tests (later)

- FastAPI TestClient tests for:
  - `/api/v1/options-board` contract fields
  - `/api/v1/payoff-chart` contract fields
- WS integration test (basic connect + receive one message), if test harness supports async WS.

## Task Card → Next Role (Validator)

## Task ID

WF-VALIDATE-001

## Assigned Role

Validator

## Goal

Verify gate/status alignment and produce a single “what’s done / what’s next” summary grounded in repo artifacts.

## Inputs (read first)

- files:
  - `docs/tasklist/CODEBASE.tasklist.md`
  - `docs/tasklist/WEB.tasklist.md`
  - `docs/plan/CODEBASE.plan.md`
  - `.agent/workflow/bybit_options_workflow.md`
  - `reports/agents/*/report.md`

## Steps

1. Check gate statuses (PLAN/TASKLIST) and note missing gate artifacts.
2. Consolidate next steps into a short ordered list of task IDs.

## Acceptance Criteria (testable)

- AC1: Validator report lists gate statuses with evidence paths.
- AC2: Validator report proposes the next task to start.

