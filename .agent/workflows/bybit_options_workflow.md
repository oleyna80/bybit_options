# Bybit Options Risk Engine Workflow

Short reference for how the backend analyzes Bybit options risk and where to extend it.

## Entry Points

**Legacy/Demo (root level):**
- `main.py`: CLI demo — loads `.env`, runs `AnalysisOrchestrator.run_full_analysis`, prints tables, saves reports.
- `api_example.py`: FastAPI usage example showing how to inject `AnalysisOrchestrator` for HTTP endpoints.

**Canonical Package (recommended for production):**
- `bybit_options/api/app.py`: FastAPI application (production entry point)
- `scripts/run_hedger.py`: Delta Hedger Bot entry point

> **Note:** For new development, use package-level imports (`from bybit_options.services...`).
> Root-level scripts are maintained for backward compatibility.


## Core Services
- `BybitConnector`: Async V5 client with token-bucket rate limiter, signed/public requests, pagination safety, and helpers for positions, tickers, instruments, klines, wallet balance.
- `MarketDataService`: Fetches positions (linear + option), wallet/margin, option tickers/Greeks, underlying perp prices, ATM IV lookup, slippage calc; caches tickers/instruments.
- `RiskEngine`: Pure, deterministic calculations. Symbol parsing, option detail extraction, position Greeks calculation (handles sign/side), IV comparison, gamma rent, aggregation by coin/series, portfolio risk build + warnings.
- `DisplayManager`: Console + Markdown formatting for positions, per-coin risk, portfolio summary. Used by CLI to write reports.
- `data_models.py`: Pydantic models/enums for positions, Greeks, IV metrics, gamma rent, margin, holdings, coin/portfolio risk; supports aggregation logic.

## Analysis Flow (CLI)
1) Load env + logging.
2) `BybitConnector` context opened with rate limiting.
3) `MarketDataService.fetch_all_positions` in parallel (linear + option) → tag categories; `fetch_margin_info` for equity/margin/holdings.
4) Derive base coins/option coins → `fetch_option_greeks` + `fetch_underlying_prices` in parallel (caches tickers).
5) `_process_positions`: detect type/series/strike, load ticker if option, compute Greeks via `RiskEngine.calculate_position_greeks`, build `PositionModel`.
6) `_enrich_positions`: for options only, compute IV metrics vs ATM IV, slippage, gamma rent.
7) `RiskEngine.build_portfolio_risk`: aggregate per coin/series, sum portfolio vega/theta, generate warnings, attach margin.
8) `DisplayManager`: print tables and save Markdown report.

## Running & Configuration

> **SSOT:** See [`docs/ops/running.md`](../../docs/ops/running.md) for ports, commands, and env vars.

- Env vars: `BYBIT_API_KEY`, `BYBIT_API_SECRET`, optional `LOG_LEVEL`. `.env` example in `readme_md.md`.
- Dependencies: `requirements.txt` (aiohttp, pydantic, python-dotenv, etc.). Create venv then `pip install -r requirements.txt`.
- Reports: written to `reports/latest_analysis.md` and timestamped files; ensure `reports/` exists/writable.

## Extending / Notes
- Keep `RiskEngine` I/O-free; add new calculations there for easy testing.
- Reuse `MarketDataService` caches; prefer new methods here for API fetches.
- Add new outputs via `DisplayManager` or FastAPI serialization.
- Frontend lives in `frontend/` (React); uses `VITE_API_URL` to connect to backend API.
