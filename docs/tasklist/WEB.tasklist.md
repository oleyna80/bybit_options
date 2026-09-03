# WEB Tasklist

Status: TASKLIST_READY

## Scope

- Source: WEB_INTERFACE_IMPLEMENTATION_PLAN.md
- Frontend lives in `frontend/` (Vite/React)
- Backend app entrypoint: `bybit_options/api/app.py`

## Tasks

- WEB-101: Add payoff chart endpoint (`/api/v1/payoff-chart`) using `payoff_calculator.py`.
  Depends on: none
  Acceptance Criteria:
  - Endpoint returns `price_range`, `pnl`, `breakeven_points`, `current_price`.
  - Response includes a minimal portfolio summary (delta/theta/vega or equivalent).

- WEB-102: Wire WebSocket broadcasting for portfolio updates.
  Depends on: none
  Acceptance Criteria:
  - `/ws/portfolio` pushes periodic updates without crashing if WS is unavailable.
  - `LiveStateKeeper` can attach a WebSocket manager and broadcast updates.

- WEB-103: Stabilize options board API contract for frontend.
  Depends on: none
  Acceptance Criteria:
  - `/api/v1/options-board` supports `base_coin`, `expiry`, `option_type`, `sort_by`, `sort_order`.
  - Response uses consistent fields for pricing, greeks, moneyness, and liquidity.

- WEB-201: Frontend API client + types for backend endpoints.
  Depends on: WEB-101, WEB-103
  Acceptance Criteria:
  - `frontend/src/services/api.ts` has functions for portfolio, options board, payoff chart.
  - Types defined in `frontend/src/types`.

- WEB-202: Options board UI component.
  Depends on: WEB-201
  Acceptance Criteria:
  - Options board renders data with expiry filter and sorting controls.
  - Table columns match API response fields.

- WEB-203: Payoff chart UI component.
  Depends on: WEB-201
  Acceptance Criteria:
  - Chart renders `price_range` vs `pnl` and shows current price marker.
  - Refresh interval or manual refresh is available.

- WEB-204: WebSocket store integration.
  Depends on: WEB-102, WEB-201
  Acceptance Criteria:
  - `frontend/src/services/websocket.ts` updates a central store.
  - Portfolio widgets update without full page reload.

- WEB-205: Trade log + export flow.
  Depends on: WEB-201
  Acceptance Criteria:
  - UI lists recent trades with basic filters.
  - Export to JSON/Markdown using `frontend/src/services/export.ts`.

- WEB-206: Docs and integration update.
  Depends on: WEB-202, WEB-203, WEB-204, WEB-205
  Acceptance Criteria:
  - `frontend/README.md` updated with run + env + endpoints.
  - `INTEGRATION.md` references frontend workflow and WS URL.
