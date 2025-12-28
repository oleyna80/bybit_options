# Bybit Options System - Audit Report

**Date**: 2025-12-26
**Audited By**: Codex
**Project Path**: ~/projects/bybit_options

---

## Executive Summary

The project contains a functioning Bybit options risk analyzer with an async connector, risk engine, and multiple utilities for options board/quotes, IV Rank backfill, and a FastAPI example. The codebase mixes production-style modules (connector, risk engine, market data service, stream manager) with partial or mock implementations (iv_rank_calculator, iron_condor analyzer real-data path, options board API stub). Data infrastructure is geared toward PostgreSQL/TimescaleDB and includes backfill and daily IV Rank workflows, but a few schema/model mismatches and dependency gaps exist. Overall, the system is usable for portfolio risk snapshots and IV Rank dashboards, but it is not yet ready for Sigma-Fractal strategy construction without adding new data sources and building dedicated strategy modules.

---

## 1. Project Structure

bybit_options/
├── .clinerules
├── .env
├── .env.backup
├── .env.example
├── .gitignore
├── API_FIX_STATUS_REPORT.md
├── CHANGELOG.md
├── COMPLETION_SUMMARY.md
├── CURRENT_IMPLEMENTATION_AUDIT.md
├── Claude对话_2025-12-11.md
├── DEBUG_DIAGNOSTIC_REPORT.md
├── Dockerfile.backend
├── INTEGRATION.md
├── Multi-Agent Discussion.py
├── OPTION_BOARD_FIX_REPORT.md
├── OPTION_BOARD_README.md
├── OPTION_QUICK_START.py
├── OPTION_QUOTES_README.md
├── OPTION_QUOTES_START.txt
├── PROMPT_MULTI_AGENT_ANALYZER.md
├── README_START.md
├── REVIEW_OPTION_BOARD_IMPLEMENTATION.md
├── USAGE_EXAMPLES.md
├── WEB_INTERFACE_IMPLEMENTATION_PLAN.md
├── analysis_orchestrator.py
├── api_example.py
├── backfill_historical_data.py
├── bybit_connector.py
├── check_infra.py
├── config.py
├── daily_iv_update.py
├── data_models.py
├── database.py
├── database_schema.sql
├── display_manager.py
├── docker-compose.yml
├── frontend/
│   ├── Dockerfile
│   ├── README.md
│   ├── index.html
│   ├── package-lock.json
│   ├── package.json
│   ├── postcss.config.js
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── Charts/
│   │   │   │   ├── IVRankChart.tsx
│   │   │   │   ├── IVRankSummary.tsx
│   │   │   │   ├── PayoffChart.tsx
│   │   │   │   └── PriceChart.tsx
│   │   │   ├── Common/
│   │   │   │   ├── CoinSelector.tsx
│   │   │   │   ├── ErrorMessage.tsx
│   │   │   │   ├── ExpiryFilter.tsx
│   │   │   │   ├── ExportButton.tsx
│   │   │   │   └── LoadingSpinner.tsx
│   │   │   ├── HistoricalDataPage.tsx
│   │   │   ├── OptionsBoard/
│   │   │   │   └── OptionsBoard.tsx
│   │   │   ├── Portfolio/
│   │   │   │   ├── MetricsCards.tsx
│   │   │   │   └── PortfolioTable.tsx
│   │   │   └── TradeLog/
│   │   │       └── TradeLog.tsx
│   │   ├── index.css
│   │   ├── index.tsx
│   │   ├── services/
│   │   │   ├── api.ts
│   │   │   ├── export.ts
│   │   │   ├── ivRankApi.ts
│   │   │   └── websocket.ts
│   │   ├── stores/
│   │   │   └── portfolioStore.ts
│   │   ├── test-components.tsx
│   │   └── types/
│   │       ├── index.ts
│   │       └── ivrank.types.ts
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   ├── vite.config.ts
├── gamma_hedge_calculator.py
├── get_option_board.py
├── get_option_board_json.py
├── get_option_quotes.py
├── get_option_quotes_json.py
├── historical_quotes.json
├── implementation_summary.md
├── iron_condor_analyzer.py
├── iron_condor_config_example.json
├── iv_rank_calculator.py
├── iv_rank_service.py
├── live_state_keeper.py
├── main.py
├── market_data_service.py
├── option_board_utils.py
├── package-lock.json
├── package.json
├── payoff_calculator.py
├── plans/
│   ├── iron_condor_vega_hedge_architecture.md
│   ├── iron_condor_vega_hedge_final_plan.md
│   ├── option_board_fetcher_plan.md
│   ├── tech_spec_iv_rank_integration.md
│   └── web_interface_implementation_plan_detailed.md
├── project_structure_md.md
├── put_chain.json
├── quotes.json
├── readme_md.md
├── requirements.txt
├── requirements.txt.backup
├── risk_engine.py
├── scenario_simulator.py
├── screenshots/
│   ├── css_error_state.png
│   ├── frontend_after_config.png
│   ├── frontend_correct_port.png
│   ├── frontend_loading.png
│   └── frontend_test_1.png
├── startup.sh
├── strategy_models.py
├── strategy_trade.md
├── stream_manager.py
├── test.py
├── test_api.py
├── test_api_integration.js
├── test_btc_price.py
├── test_integration.html
├── test_pagination.py
├── trade_logger.py
├── vega_hedge_calculator.py
├── visualization.py
└── websocket_manager.py

**Total Python Files**: 37
**Total Lines of Code**: ~14484

---

## 2. Component Analysis

### Core Components

#### File: `Multi-Agent Discussion.py`
- **Purpose**: Empty placeholder file.
- **Key Classes/Functions**: None.
- **Dependencies**: None.
- **API Calls**: None.
- **Data I/O**: None.
- **Completeness**: Stub.
- **Code Quality**: N/A.
- **Lines of Code**: ~0.

#### File: `OPTION_QUICK_START.py`
- **Purpose**: CLI quick-start notes and small helper functions for option payoff intuition.
- **Key Classes/Functions**: `put_max_loss`, `put_max_gain`, `call_max_loss`, `call_max_gain`.
- **Dependencies**: None.
- **API Calls**: None.
- **Data I/O**: Console output.
- **Completeness**: Complete.
- **Code Quality**: Good (simple utility).
- **Lines of Code**: ~160.

#### File: `analysis_orchestrator.py`
- **Purpose**: Coordinates full portfolio risk analysis flow.
- **Key Classes/Functions**: `AnalysisOrchestrator.run_full_analysis`, `_process_positions`, `_enrich_positions`.
- **Dependencies**: `bybit_connector`, `market_data_service`, `risk_engine`, `data_models`.
- **API Calls**: Indirect (via MarketDataService -> BybitConnector).
- **Data I/O**: None directly.
- **Completeness**: Complete.
- **Code Quality**: Good.
- **Lines of Code**: ~220.

#### File: `api_example.py`
- **Purpose**: FastAPI example exposing risk, options board, and IV Rank history endpoints.
- **Key Classes/Functions**: FastAPI app, `get_portfolio_risk`, `get_options_board`, websocket endpoint.
- **Dependencies**: `fastapi`, `bybit_connector`, `analysis_orchestrator`, `iv_rank_service`, `websocket_manager`.
- **API Calls**: Yes (Bybit via connector; DB queries via IVRankService).
- **Data I/O**: HTTP API, WebSocket, DB.
- **Completeness**: Partial (options board endpoint marked as shortened/stub-like, uses limited logic).
- **Code Quality**: Needs refactor (inline logic, missing error handling consistency).
- **Lines of Code**: ~311.

#### File: `backfill_historical_data.py`
- **Purpose**: Hybrid backfill for OHLCV + HV proxy IV + real IV snapshots + IV Rank calculation.
- **Key Classes/Functions**: `HybridVolatilityBackfiller`, `run_full_backfill`.
- **Dependencies**: `bybit_connector`, `database`, `config`, `numpy`, `pandas`, `sqlalchemy`.
- **API Calls**: Yes (Bybit public endpoints for kline/tickers).
- **Data I/O**: PostgreSQL/Timescale inserts.
- **Completeness**: Mostly complete (HV proxy approach is intentional).
- **Code Quality**: Good, but heavy and complex.
- **Lines of Code**: ~671.

#### File: `bybit_connector.py`
- **Purpose**: Async Bybit V5 API client with rate limiting and signing.
- **Key Classes/Functions**: `BybitConnector`, `RateLimiter`, `get_positions`, `get_tickers`, `get_instruments_info`, `get_kline_history`, `get_wallet_balance`, `get_historical_implied_volatility`.
- **Dependencies**: `aiohttp`, `hmac`, `hashlib`.
- **API Calls**: Yes (Bybit REST V5).
- **Data I/O**: Network.
- **Completeness**: Partial (missing order placement/cancel, account endpoints beyond balance).
- **Code Quality**: Good.
- **Lines of Code**: ~474.

#### File: `check_infra.py`
- **Purpose**: Checks Redis and Postgres connectivity.
- **Key Classes/Functions**: `check_redis`, `check_postgres`.
- **Dependencies**: `redis`, `asyncpg`, `dotenv`.
- **API Calls**: DB/Redis connections.
- **Data I/O**: Creates/drops table in DB; writes to Redis.
- **Completeness**: Complete.
- **Code Quality**: Good.
- **Lines of Code**: ~104.

#### File: `config.py`
- **Purpose**: Pydantic settings for app config, Bybit, analysis, DB.
- **Key Classes/Functions**: `AppConfig`, `BybitConfig`, `AnalysisConfig`, `get_config`.
- **Dependencies**: `pydantic`, `pydantic_settings`.
- **API Calls**: None.
- **Data I/O**: Loads `.env`.
- **Completeness**: Complete.
- **Code Quality**: Good.
- **Lines of Code**: ~268.

#### File: `daily_iv_update.py`
- **Purpose**: Daily cron job for ATM IV snapshot + IV Rank recalculation.
- **Key Classes/Functions**: `DailyIVUpdater`, `run_daily_update`.
- **Dependencies**: `bybit_connector`, `database`, `numpy`, `aiohttp`.
- **API Calls**: Yes (Bybit tickers + health check).
- **Data I/O**: PostgreSQL writes.
- **Completeness**: Complete.
- **Code Quality**: Good.
- **Lines of Code**: ~550.

#### File: `data_models.py`
- **Purpose**: Core Pydantic models for positions, greeks, portfolio, IV Rank history.
- **Key Classes/Functions**: `PositionModel`, `GreeksModel`, `PortfolioRiskModel`, etc.
- **Dependencies**: `pydantic`.
- **API Calls**: None.
- **Data I/O**: None.
- **Completeness**: Complete.
- **Code Quality**: Good.
- **Lines of Code**: ~532.

#### File: `database.py`
- **Purpose**: Async SQLAlchemy engine/session setup.
- **Key Classes/Functions**: `AsyncSessionLocal`, `get_db`, `init_db`.
- **Dependencies**: `sqlalchemy`, `asyncpg`, `dotenv`.
- **API Calls**: DB connection.
- **Data I/O**: Database sessions.
- **Completeness**: Complete.
- **Code Quality**: Good.
- **Lines of Code**: ~79.

#### File: `display_manager.py`
- **Purpose**: Console formatting and Markdown report generation for portfolio risk.
- **Key Classes/Functions**: `DisplayManager.print_positions_table`, `save_report_to_markdown`.
- **Dependencies**: `data_models`.
- **API Calls**: None.
- **Data I/O**: Writes markdown reports in `reports/`.
- **Completeness**: Complete.
- **Code Quality**: Good.
- **Lines of Code**: ~547.

#### File: `gamma_hedge_calculator.py`
- **Purpose**: Gamma-aware hedge recommendation logic.
- **Key Classes/Functions**: `GammaHedgeCalculator.calculate_hedge`.
- **Dependencies**: `dataclasses`, `enum`.
- **API Calls**: None.
- **Data I/O**: None.
- **Completeness**: Complete.
- **Code Quality**: Good.
- **Lines of Code**: ~432.

#### File: `get_option_board.py`
- **Purpose**: CLI tool to fetch and render option board in table/markdown.
- **Key Classes/Functions**: `fetch_option_board`, `print_option_board_table`.
- **Dependencies**: `bybit_connector`, `option_board_utils`.
- **API Calls**: Yes (Bybit tickers/instruments).
- **Data I/O**: Console and optional markdown file.
- **Completeness**: Complete.
- **Code Quality**: Good.
- **Lines of Code**: ~461.

#### File: `get_option_board_json.py`
- **Purpose**: CLI tool to fetch option board in JSON format.
- **Key Classes/Functions**: `fetch_option_board_json`.
- **Dependencies**: `bybit_connector`, `option_board_utils`.
- **API Calls**: Yes.
- **Data I/O**: JSON output to stdout or file.
- **Completeness**: Complete (note: uses symbol without -USDT in some calls).
- **Code Quality**: Needs refactor (inconsistent symbol format vs other scripts).
- **Lines of Code**: ~267.

#### File: `get_option_quotes.py`
- **Purpose**: CLI quick quotes for specific options.
- **Key Classes/Functions**: `get_option_quotes`.
- **Dependencies**: `bybit_connector`.
- **API Calls**: Yes (tickers).
- **Data I/O**: Console.
- **Completeness**: Complete.
- **Code Quality**: Good.
- **Lines of Code**: ~176.

#### File: `get_option_quotes_json.py`
- **Purpose**: CLI quotes in JSON for specific options.
- **Key Classes/Functions**: `get_option_quotes_json`.
- **Dependencies**: `bybit_connector`.
- **API Calls**: Yes.
- **Data I/O**: JSON output.
- **Completeness**: Complete.
- **Code Quality**: Good.
- **Lines of Code**: ~164.

#### File: `iron_condor_analyzer.py`
- **Purpose**: Iron Condor analysis with vega hedging and scenario simulation.
- **Key Classes/Functions**: `IronCondorAnalyzer`, `run_analysis`, `generate_report`.
- **Dependencies**: `strategy_models`, `vega_hedge_calculator`, `scenario_simulator`, `visualization`.
- **API Calls**: Optional (intended Bybit connector usage).
- **Data I/O**: Writes charts and reports to output directory.
- **Completeness**: Partial (real-data path calls BybitConnector without required keys).
- **Code Quality**: Needs refactor (real data path likely broken).
- **Lines of Code**: ~711.

#### File: `iv_rank_calculator.py`
- **Purpose**: Offline IV Rank calculation and DB initialization helper.
- **Key Classes/Functions**: `IVRankCalculator`, `DatabaseManager`.
- **Dependencies**: `sqlalchemy`, `sqlalchemy_utils`, `numpy`, `pandas`.
- **API Calls**: None.
- **Data I/O**: DB reads/writes (but uses mock data by default).
- **Completeness**: Partial (mock data, schema mismatch vs `database_schema.sql`).
- **Code Quality**: Needs refactor.
- **Lines of Code**: ~240.

#### File: `iv_rank_service.py`
- **Purpose**: Async DB access for OHLCV and IV Rank history.
- **Key Classes/Functions**: `IVRankService.get_perpetual_ohlcv`, `get_iv_rank_history`.
- **Dependencies**: `database`, `sqlalchemy`.
- **API Calls**: DB queries.
- **Data I/O**: Reads from DB.
- **Completeness**: Complete.
- **Code Quality**: Good.
- **Lines of Code**: ~117.

#### File: `live_state_keeper.py`
- **Purpose**: Real-time portfolio state aggregation from WebSockets.
- **Key Classes/Functions**: `LiveStateKeeper`, `initialize`, debounce + snapshot logic.
- **Dependencies**: `stream_manager`, `market_data_service`, `risk_engine`, `websocket_manager`.
- **API Calls**: Indirect (WebSockets + REST snapshots).
- **Data I/O**: Emits WebSocket updates.
- **Completeness**: Partial (requires integration with stream callbacks and trade logger).
- **Code Quality**: Good but complex.
- **Lines of Code**: ~741.

#### File: `main.py`
- **Purpose**: CLI entry for full risk analysis and report generation.
- **Key Classes/Functions**: `main`, `setup_logging`.
- **Dependencies**: `bybit_connector`, `analysis_orchestrator`, `display_manager`, `dotenv`.
- **API Calls**: Yes (via connector).
- **Data I/O**: Console + `reports/` markdown.
- **Completeness**: Complete.
- **Code Quality**: Good.
- **Lines of Code**: ~113.

#### File: `market_data_service.py`
- **Purpose**: Fetches positions, tickers, underlying prices, and slippage.
- **Key Classes/Functions**: `fetch_all_positions`, `fetch_option_greeks`, `fetch_underlying_prices`.
- **Dependencies**: `bybit_connector`, `data_models`.
- **API Calls**: Yes.
- **Data I/O**: None.
- **Completeness**: Complete.
- **Code Quality**: Good.
- **Lines of Code**: ~325.

#### File: `option_board_utils.py`
- **Purpose**: Option symbol parsing, formatting, board stats, batch ticker fetch.
- **Key Classes/Functions**: `parse_option_symbol`, `format_option_display`, `fetch_option_tickers`.
- **Dependencies**: `re`.
- **API Calls**: Indirect (via connector in helpers).
- **Data I/O**: None.
- **Completeness**: Complete.
- **Code Quality**: Good.
- **Lines of Code**: ~417.

#### File: `payoff_calculator.py`
- **Purpose**: Vectorized payoff and PnL curve calculation for portfolios.
- **Key Classes/Functions**: `PayoffCalculator.calculate_payoff_at_expiry`.
- **Dependencies**: `numpy`, `data_models`.
- **API Calls**: None.
- **Data I/O**: None.
- **Completeness**: Complete.
- **Code Quality**: Good (large but structured).
- **Lines of Code**: ~944.

#### File: `risk_engine.py`
- **Purpose**: Pure risk calculations for Greeks and warnings.
- **Key Classes/Functions**: `calculate_position_greeks`, `build_portfolio_risk`.
- **Dependencies**: `data_models`.
- **API Calls**: None.
- **Data I/O**: None.
- **Completeness**: Complete.
- **Code Quality**: Good.
- **Lines of Code**: ~547.

#### File: `scenario_simulator.py`
- **Purpose**: Scenario PnL simulation across price/IV grids.
- **Key Classes/Functions**: `ScenarioSimulator.simulate_all_scenarios`.
- **Dependencies**: `numpy`, `strategy_models`.
- **API Calls**: None.
- **Data I/O**: None.
- **Completeness**: Complete.
- **Code Quality**: Good.
- **Lines of Code**: ~604.

#### File: `strategy_models.py`
- **Purpose**: Pydantic models for options strategies and analysis results.
- **Key Classes/Functions**: `IronCondorConfig`, `AnalysisResult`, `HedgeRecommendation`.
- **Dependencies**: `pydantic`.
- **API Calls**: None.
- **Data I/O**: None.
- **Completeness**: Complete.
- **Code Quality**: Good.
- **Lines of Code**: ~456.

#### File: `stream_manager.py`
- **Purpose**: WebSocket stream manager for public/private feeds.
- **Key Classes/Functions**: `BybitStreamManager`, `BaseWebSocketClient`.
- **Dependencies**: `aiohttp`, `hmac`, `hashlib`.
- **API Calls**: Yes (Bybit WebSocket).
- **Data I/O**: Network.
- **Completeness**: Complete but large.
- **Code Quality**: Good.
- **Lines of Code**: ~1302.

#### File: `test.py`
- **Purpose**: Simple pybit SDK test for option ticker.
- **Key Classes/Functions**: None (script).
- **Dependencies**: `pybit`.
- **API Calls**: Yes.
- **Data I/O**: Console.
- **Completeness**: Complete.
- **Code Quality**: OK (test script).
- **Lines of Code**: ~24.

#### File: `test_api.py`
- **Purpose**: Simple Bybit connector smoke test.
- **Key Classes/Functions**: `test`.
- **Dependencies**: `bybit_connector`.
- **API Calls**: Yes.
- **Data I/O**: Console.
- **Completeness**: Complete.
- **Code Quality**: OK.
- **Lines of Code**: ~34.

#### File: `test_btc_price.py`
- **Purpose**: Fetch BTC spot price via connector.
- **Key Classes/Functions**: `test_btc_price`.
- **Dependencies**: `bybit_connector`.
- **API Calls**: Yes.
- **Data I/O**: Console.
- **Completeness**: Complete.
- **Code Quality**: OK.
- **Lines of Code**: ~37.

#### File: `test_pagination.py`
- **Purpose**: Pagination test for instruments info.
- **Key Classes/Functions**: `run_test`.
- **Dependencies**: `bybit_connector`, `option_board_utils`.
- **API Calls**: Yes.
- **Data I/O**: Console.
- **Completeness**: Complete.
- **Code Quality**: OK.
- **Lines of Code**: ~52.

#### File: `trade_logger.py`
- **Purpose**: Async trade logging to PostgreSQL with enrichment.
- **Key Classes/Functions**: `TradeLogger`, `_flush_batch`.
- **Dependencies**: `sqlalchemy`, `stream_manager`.
- **API Calls**: Indirect (WS cache lookup).
- **Data I/O**: DB writes.
- **Completeness**: Partial (some deprecated stubs; DB config defaults differ from main DB).
- **Code Quality**: Good but needs consolidation.
- **Lines of Code**: ~533.

#### File: `vega_hedge_calculator.py`
- **Purpose**: Calculates vega hedge recommendations.
- **Key Classes/Functions**: `VegaHedgeCalculator`.
- **Dependencies**: `strategy_models`.
- **API Calls**: None.
- **Data I/O**: None.
- **Completeness**: Complete.
- **Code Quality**: Good.
- **Lines of Code**: ~460.

#### File: `visualization.py`
- **Purpose**: Charting and report exports for strategy analysis.
- **Key Classes/Functions**: `StrategyVisualizer`.
- **Dependencies**: `matplotlib`, `numpy`.
- **API Calls**: None.
- **Data I/O**: Writes charts/CSV/JSON.
- **Completeness**: Complete.
- **Code Quality**: Good.
- **Lines of Code**: ~871.

#### File: `websocket_manager.py`
- **Purpose**: WebSocket broadcast manager for FastAPI clients.
- **Key Classes/Functions**: `WebSocketManager.broadcast_portfolio_update`.
- **Dependencies**: `fastapi`.
- **API Calls**: None.
- **Data I/O**: WebSocket messages.
- **Completeness**: Complete.
- **Code Quality**: Good.
- **Lines of Code**: ~540.

---

### Configuration System

- **Primary config**: `config.py` using Pydantic Settings with `.env`.
- **.env**: `BYBIT_API_KEY` and `BYBIT_API_SECRET` are set (redacted), `BYBIT_TESTNET=false`, `DATABASE_URL=postgresql://...`.
- **Thresholds**: `AnalysisConfig` defines gamma/vega/theta thresholds and margin warning levels. Additional IV Rank parameters in `.env` (`IV_RANK_PERIOD_DAYS`, `ATM_DAYS_TO_EXPIRY_MIN/MAX`).

### Dependencies

From `requirements.txt`:
- aiohttp, pydantic, pydantic-settings, python-dotenv
- redis, asyncpg, sqlalchemy, greenlet
- pandas, numpy
- apscheduler
- loguru
- httpx
- python-dateutil
- matplotlib, seaborn

**Missing/Unlisted but used in code**:
- `fastapi`, `uvicorn` (used in `api_example.py`, `websocket_manager.py`)
- `sqlalchemy_utils` (used in `iv_rank_calculator.py`)
- `pybit` (used in `test.py`)

**Not present but likely needed for Sigma-Fractal**:
- `scipy` (stats)
- `plotly` or similar for interactive charts

**Missing Dependencies for Sigma-Fractal**:
- Deribit API client (or generic HTTP integration)
- Indicators library for fractals/BB (could be custom or `ta`/`pandas-ta`)

---

## 3. Current Capabilities

### Bybit API Coverage

| Endpoint | Implemented | Quality | Notes |
|----------|-------------|---------|-------|
| get_positions | Yes | Good | Pagination + filtering implemented in `BybitConnector.get_positions`. |
| get_tickers | Yes | Good | Public tickers for spot/linear/options. |
| get_instruments_info | Yes | Good | Pagination with cursor safeguards. |
| get_kline | Partial | Good | `get_kline_history` exists; no auto-pagination. |
| place_order | No | N/A | Missing in connector. |
| get_wallet_balance | Yes | Good | Implemented via `get_wallet_balance`. |
| historical IV | Yes | Good | `get_historical_implied_volatility`. |
| order management | No | N/A | No place/cancel/replace methods. |

### Risk Analysis Features

`analysis_orchestrator.py`:
- Fetches positions (linear + option), margin data.
- Fetches option tickers and underlying prices in parallel.
- Computes position Greeks and aggregates by coin/series.
- Enriches with IV comparison, slippage metrics, gamma rent.
- Generates warnings via `risk_engine.generate_warnings`.

No strategy construction is implemented in the orchestrator; it analyzes existing positions.

### Data Infrastructure

**Database**:
- Status: PostgreSQL/TimescaleDB expected.
- Config: `DATABASE_URL` in `.env` points to Postgres.
- Schema: `database_schema.sql` defines `perpetual_ohlcv`, `option_iv_daily`, `iv_rank_daily`, `data_update_log`, `system_config`.

**Historical Data**:
- Backfill script fetches 2 years OHLCV and computes HV proxy IV.
- Daily update script inserts real ATM IV and recalculates IV Rank.

**File-based storage**:
- JSON files: `quotes.json`, `put_chain.json`, `historical_quotes.json`.
- Markdown reports created by `DisplayManager` under `reports/` (generated, not in repo).

### Display/Output

- `display_manager.py` generates console tables and markdown reports.
- `visualization.py` creates matplotlib charts for Iron Condor analysis.
- Frontend exists under `frontend/` with charts and tables (IV Rank, PnL, options board).

---

## 4. Gap Analysis for Sigma-Fractal

### Critical Missing Components

| Component | Status | Priority | Build Estimate |
|-----------|--------|----------|----------------|
| Deribit API integration (DVOL fetching) | Missing | HIGH | 3-5 hours |
| Historical data collection (hourly DVOL + candles) | Missing | HIGH | 6-10 hours |
| Williams Fractals detection algorithm | Missing | HIGH | 4-6 hours |
| Bollinger Bands (1s, 2s) | Missing | HIGH | 2-4 hours |
| Squeeze detection (BB width percentile) | Missing | HIGH | 3-5 hours |
| Multi-timeframe analysis (D1/H4/H1) | Missing | HIGH | 4-6 hours |
| Regime detection (Range vs Trend) | Missing | HIGH | 4-6 hours |
| Strategy construction (Iron Condor, Bull/Bear spreads) | Partial | HIGH | 6-10 hours |
| Delta-based strike selection | Missing | HIGH | 3-5 hours |
| Cat Ears system (Gamma monitoring + triggers) | Missing | HIGH | 4-6 hours |
| Combo transformation (H4 breakout, flip logic) | Missing | HIGH | 4-6 hours |
| Interactive PnL curve + scenario analysis | Partial | MEDIUM | 4-6 hours |
| Alert system (multi-timeframe triggers) | Missing | MEDIUM | 4-6 hours |

### Partially Implemented

- **IV Rank infrastructure**: DB schema + backfill + daily update exist, but `iv_rank_calculator.py` uses mock data and schema mismatch.
- **Strategy analysis**: Iron condor analyzer exists with scenario simulation and charts, but real data path is not wired correctly.
- **P&L visualization**: `visualization.py` and frontend charts exist but are not integrated with Sigma-Fractal data sources.

---

## 5. Code Quality Assessment

**Strengths**:
1. Clear separation between connector, market data, risk engine, and display.
2. Solid async patterns for Bybit API and WebSocket streaming.
3. Rich set of data models and analysis utilities (Greeks, slippage, gamma rent, payoff).

**Weaknesses**:
1. Mixed maturity: some modules are production-like, others are mock or partial.
2. Dependency mismatch (`sqlalchemy_utils`, `fastapi`, `pybit` used but not in requirements).
3. Schema mismatch in `iv_rank_calculator.py` vs `database_schema.sql`.

**Technical Debt**:
- Real-data path in `iron_condor_analyzer.py` is broken (missing API keys in constructor).
- `api_example.py` contains an abbreviated options-board implementation.
- Two parallel IV Rank implementations (calculator vs service) with inconsistent schemas.

---

## 6. Extension Strategy Recommendation

**Recommended Approach**: Option B (Parallel System)

**Justification**:
The existing system is a strong base for portfolio risk and IV Rank, but Sigma-Fractal requires a new data pipeline (Deribit DVOL, multi-timeframe indicators) and a dedicated strategy engine. Building a parallel `strategy/` module tree avoids tight coupling and preserves current risk analysis features. You can reuse config, connector, and DB services while isolating new strategy logic.

**Implementation Plan**:
1. **Phase 1**: Add Deribit data ingestion + historical storage (hourly DVOL, candles).
2. **Phase 2**: Build indicator module (fractals, Bollinger bands, squeeze) + regime detection.
3. **Phase 3**: Implement Sigma-Fractal strategy builder and signal engine.
4. **Phase 4**: Integrate risk/PNL visualization and alerting.

**Estimated Effort**:
- Option A: 30-45 hours
- Option B (recommended): 40-60 hours
- Option C: 60-80 hours

---

## 7. Test Results

Executed `python main.py` successfully. Output summary:

- Status: Completed without errors
- Positions fetched: 5 option positions (BTC only)
- Margin: Equity $508.92, Used $338.71, Utilization 66.55%
- Underlying price: BTC $86,982.10
- Option tickers loaded: 1196
- Report generated: `reports/risk_analysis_2025-12-26_16-51-43.md` and `reports/latest_analysis.md`

Positions observed:
- BTC-9JAN26-76000-P-USDT Buy 0.0200
- BTC-30JAN26-98000-C-USDT Buy 0.0800
- BTC-30JAN26-78000-P-USDT Buy 0.0800
- BTC-9JAN26-94000-C-USDT Sell 0.1300
- BTC-9JAN26-82000-P-USDT Sell 0.1200

---

## 8. Next Steps

### Immediate Actions
1. Add missing dependencies to `requirements.txt` (`fastapi`, `uvicorn`, `sqlalchemy_utils`, `pybit` if needed).
2. Reconcile IV Rank schema and models (`iv_rank_calculator.py` vs `database_schema.sql`).

### Development Roadmap

**Phase 1: Data Foundation** (Priority: CRITICAL)
- [ ] Add Deribit DVOL fetcher + scheduler
- [ ] Store DVOL and candles in DB

**Phase 2: Regime Detection** (Priority: HIGH)
- [ ] Implement Williams Fractals detection
- [ ] Implement Bollinger Bands and squeeze logic

**Phase 3: Strategy Building** (Priority: HIGH)
- [ ] Build Sigma-Fractal strategy module
- [ ] Add strike selection logic and builders

**Phase 4: Dynamic Adjustments** (Priority: MEDIUM)
- [ ] Add alerting and multi-timeframe trigger engine
- [ ] Integrate dynamic hedging signals

---

## Appendix A: File Details

(See component analysis section for per-file summaries.)

---

## Appendix B: Recommendations for Claude

**Questions Requiring Clarification**:
1. Which data source is authoritative for DVOL (Deribit vs other providers)?
2. What is the exact timeframe policy for regime detection (weights among D1/H4/H1)?

**Architectural Suggestions**:
1. Add a dedicated `strategy/` package with `data/`, `indicators/`, `signals/`, `execution/` submodules.
2. Standardize schema + ORM models for IV Rank and historical data to avoid drift.
