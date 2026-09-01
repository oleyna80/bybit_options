# Project Structure & Architecture

## 📁 File Organization

```
bybit-options-risk-engine/
│
├── Configuration & Setup
│   ├── .env                          # Environment variables (NEVER commit!)
│   ├── .env.example                  # Example environment variables
│   ├── .gitignore                    # Git ignore rules
│   ├── requirements.txt              # Python dependencies
│   ├── requirements.lock.txt         # Locked versions
│   ├── package.json                  # Frontend/Node dependencies
│   └── docker-compose.yml            # Docker multi-container setup
│
├── Documentation
│   ├── README.md                     # Main user documentation (legacy)
│   ├── readme_md.md                  # Current main documentation
│   ├── INTEGRATION.md                # Integration guide
│   ├── AGENTS.md                     # Agent orchestration protocol
│   ├── project_structure_md.md       # This file - architecture guide
│   ├── CHANGELOG.md                  # Version history
│   └── Various analysis reports/     # DEBUG_*, REVIEW_*, STATUS_* reports
│
├── Entry Points
│   ├── main.py                       # CLI entry point (backward compatible)
│   ├── api_example.py                # API entry point (backward compatible)
│   └── apps/
│       ├── cli.py                    # CLI router (calls bybit_options.cli.main)
│       └── api.py                    # API router (calls bybit_options.api.app)
│
├── Core Application
│   └── bybit_options/
│       ├── __init__.py
│       ├── api/                      # FastAPI app + REST routes
│       │   ├── __init__.py
│       │   ├── app.py                # FastAPI application instance
│       │   └── routes.py             # API endpoints (/api/v1/...)
│       ├── cli/                      # CLI implementation
│       │   ├── __init__.py
│       │   └── main.py               # CLI command handlers
│       ├── config/                   # Settings & logging
│       │   ├── __init__.py
│       │   ├── settings.py           # Settings dataclass
│       │   └── logging.py            # Logging configuration
│       ├── core/                     # Business logic (pure functions)
│       │   ├── __init__.py
│       │   └── risk_engine.py        # RiskEngine with static methods
│       ├── models/                   # Pydantic data models
│       │   ├── __init__.py
│       │   └── *.py                  # GreeksModel, PositionModel, etc.
│       ├── orchestration/            # Workflow coordination
│       │   ├── __init__.py
│       │   └── analysis_orchestrator.py  # Main analysis pipeline
│       ├── reports/                  # Display & report formatting
│       │   ├── __init__.py
│       │   └── display_manager.py    # Console output & Markdown reports
│       ├── services/                 # External integrations
│       │   ├── __init__.py
│       │   ├── bybit_connector.py    # Bybit API client (async)
│       │   └── market_data_service.py    # Data fetching & caching
│       ├── storage/                  # Data persistence layer
│       │   ├── __init__.py
│       │   └── *.py                  # Database adapters, storage interfaces
│       └── utils/                    # Utility functions
│           ├── __init__.py
│           └── helpers.py            # Common utilities
│
├── Database & Migration
│   ├── database.py                   # Database connection (legacy)
│   ├── database_schema.sql           # SQL schema definition
│   └── migrations/                   # Alembic migration scripts
│
├── Scripts & Tools
│   ├── scripts/                      # Utility scripts
│   ├── tests/                        # Test suite
│   ├── startup.sh                    # Server startup script
│   ├── monitor_health.sh             # Health check script
│   └── check_infra.py                # Infrastructure verification
│
├── Agent Framework
│   ├── .agent/                       # Agent orchestration configs
│   │   ├── PROJECT_BRIEF.md          # Project brief for agents
│   │   ├── conventions.md            # Coding conventions
│   │   └── workflow/                 # Workflow definitions
│   ├── .memory_bank/                 # Agent memory (context persistence)
│   │   ├── productContext.md         # Product state
│   │   └── activeContext.md          # Current task state
│   └── agreements/                   # Agent routing & permissions
│       ├── 00-routing.md             # Request routing rules
│       ├── 10-model-routing.md       # Model selection rules
│       ├── 11-auto-context.md        # Context rules
│       └── 20-permissions.md         # Permission gates
│
├── Development & Analysis
│   ├── logs/                         # Application logs
│   ├── reports/                      # Generated reports
│   ├── artifacts/                    # Task cards & execution logs
│   ├── docs/                         # Additional documentation
│   ├── plans/                        # Planning documents
│   ├── strategy/                     # Strategy definitions
│   ├── frontend/                     # Web UI (if present)
│   └── screenshots/                  # UI screenshots & demos
│
├── Legacy & Analysis Tools
│   ├── analysis_orchestrator.py      # Legacy (see bybit_options/orchestration/)
│   ├── bybit_connector.py            # Legacy (see bybit_options/services/)
│   ├── market_data_service.py        # Legacy (see bybit_options/services/)
│   ├── risk_engine.py                # Legacy (see bybit_options/core/)
│   ├── display_manager.py            # Legacy (see bybit_options/reports/)
│   ├── data_models.py                # Legacy (see bybit_options/models/)
│   ├── config.py                     # Legacy (see bybit_options/config/)
│   └── *_calculator.py, *_analyzer.py    # Various analysis scripts
│
└── Docker
    └── Dockerfile.backend            # Docker build for API server
```

---

## ⚠️ Important Notes

### Active Code Location
- ✅ **Current**: `bybit_options/` package
- ⚠️ **Legacy**: Root-level Python files (for backward compatibility)
- 🚀 **Recommended**: Use imports from `bybit_options.*`

### Agent Framework
- The project uses a **Workspace Orchestrator** protocol (see `AGENTS.md`)
- Agent configs in `.agent/` define routing and workflows
- Memory bank in `.memory_bank/` tracks project state across sessions

---

## 📂 Detailed Substructure

### `bybit_options/api/`
**Purpose**: FastAPI application and REST endpoints

```
api/
├── __init__.py
├── app.py                    # FastAPI application instance
└── routes.py                 # All API endpoints
```

**Key Endpoints**:
- `GET /api/v1/risk/portfolio` — Full portfolio analysis
- `GET /api/v1/risk/coin/{coin}` — Per-coin risk metrics
- `GET /api/v1/margin` — Account margin information
- `GET /api/v1/positions` — All positions with Greeks
- `POST /api/v1/report/generate` — Generate Markdown report

---

### `bybit_options/cli/`
**Purpose**: Command-line interface commands

```
cli/
├── __init__.py
└── main.py                   # CLI command handlers
```

**Key Commands**:
- `portfolio` — Show portfolio summary
- `coin {symbol}` — Show coin-specific risk
- `report` — Generate Markdown report
- `monitor` — Real-time monitoring

---

### `bybit_options/config/`
**Purpose**: Configuration and logging setup

```
config/
├── __init__.py
├── settings.py               # Settings dataclass with defaults
└── logging.py                # Logging configuration
```

**Configuration Sources** (in priority order):
1. Environment variables (`.env`)
2. Settings dataclass defaults
3. CLI arguments (optional)

---

### `bybit_options/core/`
**Purpose**: Pure business logic (no I/O)

```
core/
├── __init__.py
└── risk_engine.py            # RiskEngine with static methods
```

**Guarantees**:
- ✅ No database calls
- ✅ No API calls
- ✅ No file I/O
- ✅ Deterministic (same input = same output)
- ✅ Fully testable in isolation

---

### `bybit_options/models/`
**Purpose**: Type-safe Pydantic models

```
models/
├── __init__.py
├── greeks.py                 # GreeksModel (Delta, Gamma, Vega, Theta)
├── position.py               # PositionModel (complete position with Greeks)
├── risk.py                   # CoinRiskModel, PortfolioRiskModel
├── margin.py                 # MarginModel (account margin metrics)
└── ...                       # Other domain models
```

**Key Models**:
- `GreeksModel`: Greek letters (δ, γ, ν, θ)
- `PositionModel`: Single option position with all metrics
- `CoinRiskModel`: Aggregated risk per coin
- `PortfolioRiskModel`: Complete portfolio snapshot

---

### `bybit_options/orchestration/`
**Purpose**: Workflow coordination

```
orchestration/
├── __init__.py
└── analysis_orchestrator.py  # AnalysisOrchestrator (main workflow)
```

**Main Method**:
```python
async def run_full_analysis(self) -> PortfolioRiskModel:
    """
    Complete analysis pipeline:
    1. Fetch positions
    2. Fetch margin info
    3. Fetch market data (parallel)
    4. Calculate Greeks (RiskEngine)
    5. Build portfolio model
    6. Generate warnings
    7. Return PortfolioRiskModel
    """
```

---

### `bybit_options/reports/`
**Purpose**: Display and report generation

```
reports/
├── __init__.py
└── display_manager.py        # DisplayManager (console + Markdown output)
```

**Output Formats**:
- Console tables (ANSI colors)
- Markdown reports (AI-friendly)
- JSON (API responses)

---

### `bybit_options/services/`
**Purpose**: External integrations

```
services/
├── __init__.py
├── bybit_connector.py        # BybitConnector (HTTP client)
└── market_data_service.py    # MarketDataService (data orchestration)
```

**BybitConnector**: 
- Low-level async HTTP client
- Rate limiting
- Signature generation
- Connection pooling

**MarketDataService**:
- High-level data fetching
- Request caching
- Parallel data loading
- Business-friendly interface

---

### `bybit_options/storage/`
**Purpose**: Data persistence adapters

```
storage/
├── __init__.py
├── base.py                   # Storage interface (ABC)
├── sql_adapter.py            # SQLAlchemy adapter
├── redis_adapter.py          # Redis adapter (optional)
└── file_adapter.py           # File-based storage (optional)
```

---

### `bybit_options/utils/`
**Purpose**: Shared utility functions

```
utils/
├── __init__.py
├── helpers.py                # Common utilities
├── formatters.py             # Data formatting helpers
└── validators.py             # Input validation helpers
```

---

### `docs/`, `plans/`, `reports/`
**Purpose**: Documentation and planning

```
docs/
├── .active_ticket            # Current active task
├── prd/                      # Product requirement documents
├── plan/                     # Technical planning
└── tasklist/                 # Task checklists

plans/                         # High-level planning documents

reports/                       # Generated analysis reports
├── risk_analysis_*.md        # Timestamped risk reports
└── latest_analysis.md        # Latest report (updated)
```

---

### `.agent/` and `.memory_bank/`
**Purpose**: Agent orchestration framework

```
.agent/
├── PROJECT_BRIEF.md          # Project overview for agents
├── conventions.md            # Coding conventions for agents
└── workflow/
    └── bybit_options_workflow.md  # Workflow definition

.memory_bank/
├── productContext.md         # Product state & architecture
├── activeContext.md          # Current work context
└── progress.md               # Task progress tracking
```

**When to update Memory Bank**:
- After major architectural changes
- When starting new feature work
- Before switching between tasks
- At end of session (save state)

---

### `tests/`
**Purpose**: Test suite

```
tests/
├── __init__.py
├── conftest.py               # Pytest fixtures
├── test_risk_engine.py       # Risk engine tests
├── test_orchestrator.py      # Orchestrator tests
├── test_services.py          # Services tests
└── fixtures/
    └── *.json                # Mock API responses
```

---

### Root-level Legacy Files
⚠️ **Deprecated** — Use `bybit_options/` package instead

```
analysis_orchestrator.py  →  bybit_options/orchestration/
bybit_connector.py        →  bybit_options/services/
market_data_service.py    →  bybit_options/services/
risk_engine.py            →  bybit_options/core/
display_manager.py        →  bybit_options/reports/
data_models.py            →  bybit_options/models/
config.py                 →  bybit_options/config/
```

**Migration**: The new package structure is active. Legacy files remain for backward compatibility but should not be modified.

### Layer 1: Configuration (`bybit_options/config`)
**Purpose**: Centralize all settings and environment variables

**Key Components**:
- `Settings` (dataclass) in `bybit_options/config/settings.py`
- `configure_logging()` in `bybit_options/config/logging.py`

**Dependencies**: stdlib only (`dataclasses`, `os`, `logging`)

**Used By**: All modules

---

### Layer 2: Data Models (`bybit_options/models`)
**Purpose**: Type-safe data structures for the entire system

**Key Classes**:
- `GreeksModel`: Delta, Gamma, Vega, Theta
- `PositionModel`: Complete position with metrics
- `CoinRiskModel`: Risk aggregation per coin
- `MarginModel`: Account margin metrics
- `PortfolioRiskModel`: Complete portfolio snapshot

**Dependencies**: Pydantic only

**Used By**: All business logic and API layers

**Why Pydantic?**
- Automatic validation
- JSON serialization (FastAPI)
- Type safety
- IDE autocomplete

---

### Layer 3: API Connector (`bybit_options/services/bybit_connector.py`)
**Purpose**: Low-level async HTTP client for Bybit API

**Key Classes**:
- `BybitConnector`: Main API client
- `RateLimiter`: Token bucket rate limiting

**Key Features**:
- Async/await with `aiohttp`
- Connection pooling
- Automatic signature generation
- Rate limiting
- Context manager support

**Dependencies**: `aiohttp`

**Used By**: `MarketDataService`

**Example**:
```python
async with BybitConnector(api_key, api_secret) as connector:
    positions = await connector.get_positions("option")
```

---

### Layer 4: Market Data Service (`bybit_options/services/market_data_service.py`)
**Purpose**: High-level data fetching with caching

**Key Classes**:
- `MarketDataService`: Data orchestration layer

**Key Methods**:
- `fetch_all_positions()`: Get all positions
- `fetch_margin_info()`: Get account margin
- `fetch_option_greeks()`: Get Greeks for coins
- `fetch_underlying_prices()`: Get perp prices
- `fetch_atm_iv()`: Find ATM implied volatility
- `calculate_slippage()`: Calculate spread metrics

**Dependencies**: `BybitConnector`

**Used By**: `AnalysisOrchestrator`

**Why This Layer?**
- Abstracts API complexity
- Implements caching
- Parallel data fetching
- Business-friendly interface

---

### Layer 5: Risk Engine (`bybit_options/core/risk_engine.py`)
**Purpose**: Pure business logic - ZERO I/O

**Key Classes**:
- `RiskEngine`: Static methods only

**Key Methods**:
- `calculate_position_greeks()`: Greeks calculation
- `calculate_iv_metrics()`: IV comparison
- `calculate_gamma_rent()`: Theta/Gamma ratio
- `aggregate_coin_risk()`: Per-coin aggregation
- `build_portfolio_risk()`: Portfolio construction
- `generate_warnings()`: Risk alerts

**Dependencies**: `bybit_options.models` only

**Used By**: `AnalysisOrchestrator`

**Critical Design Principle**:
> No API calls, no I/O, no side effects
> Same input → Same output (deterministic)
> Pure functions enable easy testing

---

### Layer 6: Orchestrator (`bybit_options/orchestration/analysis_orchestrator.py`)
**Purpose**: Coordinate the complete analysis workflow

**Key Classes**:
- `AnalysisOrchestrator`: Main workflow coordinator

**Key Method**:
- `run_full_analysis()`: Complete analysis pipeline

**Workflow**:
```
1. Fetch positions (MarketDataService)
2. Fetch margin info
3. Identify required data
4. Fetch market data in parallel
5. Calculate Greeks (RiskEngine)
6. Enrich with metrics (IV, slippage, rent)
7. Build portfolio model (RiskEngine)
→ Return PortfolioRiskModel
```

**Dependencies**: All services

**Used By**: CLI (`apps/cli.py`) or API (`apps/api.py`)

---

### Layer 7: Display (`bybit_options/reports/display_manager.py`)
**Purpose**: Console output formatting and report generation

**Key Classes**:
- `DisplayManager`: Static formatting and reporting methods

**Key Methods**:
- `print_positions_table()` - Display positions in formatted table
- `print_coin_risks()` - Show risk metrics per coin
- `print_portfolio_summary()` - Display portfolio summary
- `print_enhanced_position_details()` - Show IV, spread, gamma rent
- `save_report_to_markdown()` - **NEW!** Generate Markdown reports

**Markdown Report Method** (NEW):
```python
@staticmethod
def save_report_to_markdown(
    positions: List[PositionModel],
    portfolio: PortfolioRiskModel,
    output_dir: str = "reports"
) -> str:
    """
    Generates comprehensive Markdown report for AI analysis
    
    Output:
    - Portfolio Summary (Equity, Margin, Greeks, Prices)
    - Risk Alerts and Warnings
    - Complete Positions Table
    - Analysis Notes for AI Agents
    
    Files Created:
    - reports/risk_analysis_YYYY-MM-DD_HH-MM-SS.md (timestamped)
    - reports/latest_analysis.md (always latest)
    
    Returns: Path to generated report
    """
```

**Dependencies**: `bybit_options.models`, `os`, `shutil`, `datetime`

**Used By**: `apps/cli.py` (CLI mode)

**Features**:
- ✅ Beautiful Markdown formatting with emojis
- ✅ Automatic folder creation (`reports/`)
- ✅ Timestamped archive files
- ✅ Latest report alias for easy access
- ✅ Includes underlying prices (BTC, ETH, etc.)
- ✅ AI-friendly format (ready for Claude/ChatGPT)

**Example Output**:
```markdown
# 🛡️ Options Risk Report
**Generated:** 2025-12-10 18:49:01

## 1. Portfolio Summary

| Metric | Value | Status |
| :--- | :--- | :--- |
| **Equity** | `$1,188.69` | - |
| **Margin Utilization** | `87.91%` | ⚠️ High |
| **Total Delta** | `+0.0533 BTC` | 🔴 Directional |
| **Total Theta** | `$+10.18/day` | Cash Flow |
| **Total Vega** | `$-3.92` | Volatility Risk |

### Underlying Prices

- **BTC**: `$92,251.89`

## 2. Risk Alerts

- ⚠️ 🚨 CRITICAL: Margin ratio 87.9% (>80%) - Risk of liquidation!

## 3. Positions Details

| Symbol | Side | Size | Delta | Gamma | Vega | Theta |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `BTCUSDT` | Buy | 0.008 | `+0.0080` | `+0.000000` | `+0.0` | `+0.0` |
| `BTC-19DEC25-97000-C-USDT` | Buy | 0.13 | `+0.0329` | `+0.000006` | `+5.9` | `-15.6` |
...
```

---

### Layer 8: Entry Points

#### CLI Mode (`apps/cli.py`)
```
User → main() → Orchestrator → Display
```

**Purpose**: Interactive terminal analysis

**Use Case**: 
- Quick portfolio checks
- Testing
- Debugging

#### API Mode (`bybit_options/api/app.py`)
```
HTTP Request → FastAPI → Orchestrator → JSON Response
```

**Purpose**: REST API for web frontends

**Endpoints**:
- `GET /api/v1/risk/portfolio`
- `GET /api/v1/risk/coin/{coin}`
- `GET /api/v1/margin`
- `GET /api/v1/positions`

---

## 🔄 Data Flow

### Complete Analysis Flow

```
┌─────────┐
│  User   │
└────┬────┘
     │
     ▼
┌─────────────────────────┐
│  apps/cli.py / API      │
│  (Entry Point)          │
└────┬────────────────────┘
     │
     ▼
┌─────────────────────────────────┐
│  AnalysisOrchestrator           │
│  ┌───────────────────────────┐  │
│  │ 1. Fetch Positions        │  │
│  │ 2. Fetch Margin           │  │
│  │ 3. Fetch Market Data      │  │
│  │ 4. Calculate Greeks       │  │
│  │ 5. Enrich Metrics         │  │
│  │ 6. Build Portfolio Model  │  │
│  └───────────────────────────┘  │
└──────┬──────────────────────────┘
       │
       ├───────────────────────────┐
       │                           │
       ▼                           ▼
┌──────────────────┐      ┌───────────────┐
│ MarketDataService│      │  RiskEngine   │
│ ┌──────────────┐ │      │  (Pure Logic) │
│ │Fetch Parallel│ │      │               │
│ │Cache Results │ │      │  • Greeks     │
│ └──────────────┘ │      │  • IV         │
└──────┬───────────┘      │  • Slippage   │
       │                  │  • Rent       │
       ▼                  │  • Warnings   │
┌──────────────────┐      └───────────────┘
│ BybitConnector   │
│ ┌──────────────┐ │
│ │Rate Limiter  │ │
│ │Signature     │ │
│ │HTTP Pool     │ │
│ └──────────────┘ │
└──────┬───────────┘
       │
       ▼
   Bybit API
```

---

## 🎯 Design Principles

### 1. Separation of Concerns
Each module has ONE responsibility:
- `BybitConnector`: HTTP communication
- `MarketDataService`: Data fetching
- `RiskEngine`: Calculations
- `AnalysisOrchestrator`: Workflow
- `DisplayManager`: Presentation

### 2. Async First
All I/O operations use `async/await`:
```python
# ✅ Correct
async def fetch_data():
    async with connector.get_positions() as resp:
        return await resp.json()

# ❌ Wrong
def fetch_data():
    return requests.get(...)
```

### 3. Type Safety
Pydantic models everywhere:
```python
# ✅ Correct
def calculate(position: PositionModel) -> GreeksModel:
    ...

# ❌ Wrong
def calculate(position: dict) -> dict:
    ...
```

### 4. Pure Business Logic
`RiskEngine` has no side effects:
```python
# ✅ Correct - Pure function
@staticmethod
def calculate_greeks(data: Dict) -> GreeksModel:
    return GreeksModel(...)

# ❌ Wrong - Side effects
def calculate_greeks(symbol: str) -> GreeksModel:
    ticker = fetch_from_api(symbol)  # I/O!
    return GreeksModel(...)
```

### 5. Dependency Injection
Pass dependencies, don't create them:
```python
# ✅ Correct
class Orchestrator:
    def __init__(self, connector: BybitConnector):
        self.connector = connector

# ❌ Wrong
class Orchestrator:
    def __init__(self):
        self.connector = BybitConnector()  # Hard dependency
```

---

## 🧪 Testing Strategy

### Unit Tests
Test pure logic in isolation:

```python
# test_risk_engine.py
def test_calculate_greeks():
    raw_data = {"delta": 0.5, "gamma": 0.001, ...}
    greeks = RiskEngine.calculate_position_greeks(...)
    assert greeks.delta_coin == 0.5
```

### Integration Tests
Test with mock API responses:

```python
# test_orchestrator.py
async def test_full_analysis():
    mock_connector = MockBybitConnector()
    orchestrator = AnalysisOrchestrator(mock_connector)
    portfolio = await orchestrator.run_full_analysis()
    assert portfolio.margin.total_equity > 0
```

### E2E Tests
Test against Bybit testnet:

```python
# test_e2e.py
async def test_real_api():
    connector = BybitConnector(..., testnet=True)
    # Full workflow against testnet
```

---

## 📈 Scaling Considerations

### Current Design (Single Instance)
- ✅ Perfect for personal use
- ✅ Low latency (<5s)
- ✅ Simple deployment

### Future Scaling (Production)

#### Option 1: Horizontal Scaling
```
Load Balancer
    ├── API Instance 1
    ├── API Instance 2
    └── API Instance 3
         ↓
    Redis (Shared Cache)
         ↓
    Bybit API
```

#### Option 2: Background Workers
```
FastAPI (API Layer)
    ↓
Redis Queue
    ↓
Celery Workers (Analysis)
    ↓
PostgreSQL (Results Storage)
```

#### Option 3: WebSocket Streaming
```
FastAPI (WebSocket Server)
    ↓
Bybit WebSocket → Real-time Greeks
    ↓
Push Updates to Frontend
```

---

## 🔐 Security Checklist

- ✅ Never commit `.env` file
- ✅ Use environment variables for secrets
- ✅ Validate all inputs with Pydantic
- ✅ Rate limit API requests
- ✅ Use HTTPS only (enforced by Bybit)
- ✅ Implement CORS properly in production
- ✅ Log errors without exposing secrets

---

## 🚀 Deployment

### Development
```bash
python main.py
```

### Production API
```bash
gunicorn bybit_options.api.app:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000
```

### Docker (Future)
```dockerfile
FROM python:3.11-slim
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "bybit_options.api.app:app", "--host", "0.0.0.0"]
```

---

## 📚 Adding New Features

### Example: Add Historical Greeks Tracking

1. **Data Model** (`bybit_options/models`):
```python
class GreeksSnapshot(BaseModel):
    timestamp: datetime
    greeks: GreeksModel
```

2. **Storage Service** (new file: `storage_service.py`):
```python
class StorageService:
    async def save_snapshot(self, snapshot: GreeksSnapshot):
        # PostgreSQL or Redis
```

3. **Update Orchestrator** (`bybit_options/orchestration/analysis_orchestrator.py`):
```python
async def run_full_analysis(self):
    portfolio = ...
    await self.storage.save_snapshot(...)
    return portfolio
```

4. **Add API Endpoint** (`bybit_options/api/app.py`):
```python
@app.get("/api/v1/history/{coin}")
async def get_history(coin: str):
    return await storage.get_snapshots(coin)
```

---

**This architecture is ready for production and designed to scale.** 🚀
