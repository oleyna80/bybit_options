# Project Structure & Architecture

## 📁 File Organization

```
bybit-options-risk-engine/
│
├── .env                          # Environment variables (NEVER commit!)
├── .gitignore                    # Git ignore rules
├── requirements.txt              # Python dependencies
├── README.md                     # User documentation
├── PROJECT_STRUCTURE.md          # This file - architecture guide
│
├── config.py                     # Centralized configuration
├── bybit_connector.py            # Async Bybit API client
├── data_models.py                # Pydantic data models
├── market_data_service.py        # Data fetching layer
├── risk_engine.py                # Pure business logic
├── analysis_orchestrator.py      # Workflow coordinator
├── display_manager.py            # Console output formatter
│
├── main.py                       # CLI entry point
└── api_example.py                # FastAPI REST API example
```

---

## 🏗️ Architecture Layers

### Layer 1: Configuration (`config.py`)
**Purpose**: Centralize all settings and environment variables

**Key Classes**:
- `AppConfig`: Main configuration
- `BybitConfig`: API credentials
- `AnalysisConfig`: Risk thresholds

**Dependencies**: None (pure Pydantic)

**Used By**: All modules

---

### Layer 2: Data Models (`data_models.py`)
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

### Layer 3: API Connector (`bybit_connector.py`)
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

### Layer 4: Market Data Service (`market_data_service.py`)
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

### Layer 5: Risk Engine (`risk_engine.py`)
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

**Dependencies**: `data_models` only

**Used By**: `AnalysisOrchestrator`

**Critical Design Principle**:
> No API calls, no I/O, no side effects
> Same input → Same output (deterministic)
> Pure functions enable easy testing

---

### Layer 6: Orchestrator (`analysis_orchestrator.py`)
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

**Used By**: CLI (`main.py`) or API (`api_example.py`)

---

### Layer 7: Display (`display_manager.py`)
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

**Dependencies**: `data_models`, `os`, `shutil`, `datetime`

**Used By**: `main.py` (CLI mode)

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

#### CLI Mode (`main.py`)
```
User → main() → Orchestrator → Display
```

**Purpose**: Interactive terminal analysis

**Use Case**: 
- Quick portfolio checks
- Testing
- Debugging

#### API Mode (`api_example.py`)
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
│  main.py / API          │
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
gunicorn api_example:app \
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
CMD ["uvicorn", "api_example:app", "--host", "0.0.0.0"]
```

---

## 📚 Adding New Features

### Example: Add Historical Greeks Tracking

1. **Data Model** (`data_models.py`):
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

3. **Update Orchestrator** (`analysis_orchestrator.py`):
```python
async def run_full_analysis(self):
    portfolio = ...
    await self.storage.save_snapshot(...)
    return portfolio
```

4. **Add API Endpoint** (`api_example.py`):
```python
@app.get("/api/v1/history/{coin}")
async def get_history(coin: str):
    return await storage.get_snapshots(coin)
```

---

**This architecture is ready for production and designed to scale.** 🚀