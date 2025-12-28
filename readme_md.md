# Bybit Options Risk Engine

Production-ready async backend for options portfolio risk analysis on Bybit.

## 🏗️ Architecture

### Service-Oriented Design

```
┌─────────────────────────────────────────────────────────────┐
│                         main.py                              │
│                   (CLI Entry Point)                          │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                  AnalysisOrchestrator                        │
│              (Coordinates workflow)                          │
└──────┬─────────────────────┬────────────────────┬───────────┘
       │                     │                    │
       ▼                     ▼                    ▼
┌──────────────┐    ┌─────────────────┐   ┌─────────────┐
│ BybitConnector│    │ MarketDataService│   │ RiskEngine  │
│ (Async API)   │    │ (Data fetching)  │   │ (Pure logic)│
└──────────────┘    └─────────────────┘   └─────────────┘
       │                     │                    │
       ▼                     ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                      Pydantic Models                         │
│              (Type-safe data structures)                     │
└─────────────────────────────────────────────────────────────┘
```

### Key Principles

1. **Async First**: All I/O operations use `aiohttp` and `asyncio`
2. **Pure Business Logic**: `RiskEngine` has zero I/O - deterministic calculations
3. **Type Safety**: Pydantic models everywhere for validation and serialization
4. **Separation of Concerns**: Each service has a single responsibility
5. **FastAPI Ready**: Drop-in integration for web APIs

---

## 📦 Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
BYBIT_API_KEY=your_api_key_here
BYBIT_API_SECRET=your_secret_here
LOG_LEVEL=INFO
EOF
```

---

## 🚀 Usage

### CLI Mode (Current)

```bash
python main.py
```

This will:
1. Fetch all your Bybit positions
2. Calculate Greeks (Delta, Gamma, Vega, Theta)
3. Compute risk metrics (Margin, IV comparison, Slippage, Gamma Rent)
4. Display formatted results in console
5. **Generate Markdown report** in `reports/latest_analysis.md` (NEW!)

### Markdown Report Generation

The application now automatically generates detailed Markdown reports for AI analysis:

```
reports/
├── risk_analysis_2025-12-10_18-49-01.md  # Timestamped report
└── latest_analysis.md                     # Latest report (always)
```

**Report Contents**:
- 📊 Portfolio Summary (Equity, Margin, Delta, Theta, Vega, Prices)
- ⚠️ Risk Alerts and Warnings
- 📋 Complete Positions Table with Greeks
- 💡 Analysis Notes for AI Agents

**Use Cases**:
- Load `reports/latest_analysis.md` into Claude/ChatGPT for analysis
- Archive timestamped reports for historical tracking
- Integrate with AI agents for automated trading decisions

### Expected Output

```
==================================================
              POSITIONS OVERVIEW
==================================================

SYMBOL                         | TYPE   | SIDE | SIZE  | DELTA  | ...
────────────────────────────────────────────────────────────────────
────────────────────────────── BTC ───────────────────────────────────
BTC-19DEC25-100000-C          | OPTION | Buy  | 1.50  | +0.8234 | ...
BTCUSDT                       | LINEAR | Buy  | 0.10  | +0.1000 | ...

==================================================
              RISK BY COIN
==================================================

┌─ BTC ──────────────────────────────────────────
│
│ 📊 TOTAL EXPOSURE:
│   Delta:  +0.9234 BTC | Gamma: +0.000234 | ...
│   Underlying Price: $98,765.43
│
│ 📈 BREAKDOWN:
│   Futures:  Δ = +0.1000 BTC
│   Options:  Δ = +0.8234 BTC | Γ = +0.000234 | ...
│
│ 🗓️  BY EXPIRY:
│   • 19DEC25  | Δ=+0.8234 | Γ=+0.000234 | ...
└─────────────────────────────────────────────────

==================================================
           PORTFOLIO RISK SUMMARY
==================================================

💰 MARGIN & ACCOUNT:
   🟢 Account Type: UNIFIED
   • Total Equity:        $   50,000.00
   • Used Margin:         $   25,000.00
   • Margin Utilization:         50.00%

📊 PORTFOLIO GREEKS:
   • Total Vega:  $  +5,678.90
   • Total Theta: $    -987.65/day
     → 🟢 Long Vega: You profit when IV increases
     → 🔴 Negative Theta: Time decay works against you

⚠️  DELTA EXPOSURE (by coin - DO NOT aggregate):
   🟢 BTC     :      +0.9234 BTC
   🔴 ETH     :      -2.3456 ETH

✅ No critical warnings
```

---

## 🌐 Web Interface

Complete React-based web interface for portfolio analysis with real-time updates.

### Features
- **Options Board**: Filter and analyze available options
- **Portfolio Dashboard**: Real-time position tracking with Greeks
- **Risk Charts**: Interactive P&L visualization
- **Data Export**: JSON, Markdown, CSV formats
- **WebSocket Updates**: Live portfolio changes

See [frontend/README.md](frontend/README.md) for detailed instructions.

### Quick Start

```bash
# Install frontend dependencies
cd frontend
npm install

# Start development server (port 3001)
npm run dev
```

The frontend automatically connects to the backend API at `http://localhost:8000/api/v1`.

---

## 🔌 FastAPI Integration Example

See `api_example.py` for full implementation:

```python
from fastapi import FastAPI, Depends
from bybit_connector import BybitConnector
from analysis_orchestrator import AnalysisOrchestrator
from data_models import PortfolioRiskModel

app = FastAPI()

async def get_orchestrator() -> AnalysisOrchestrator:
    connector = BybitConnector(api_key=..., api_secret=...)
    async with connector:
        yield AnalysisOrchestrator(connector)

@app.get("/risk/portfolio", response_model=PortfolioRiskModel)
async def get_portfolio_risk(
    orchestrator: AnalysisOrchestrator = Depends(get_orchestrator)
):
    """
    Get complete portfolio risk analysis
    Returns JSON with all Greeks, margins, and warnings
    """
    return await orchestrator.run_full_analysis()

@app.get("/risk/coin/{coin}")
async def get_coin_risk(coin: str, orchestrator = Depends(...)):
    portfolio = await orchestrator.run_full_analysis()
    return portfolio.coin_risks.get(coin.upper())
```

### Starting the Backend

```bash
# Development mode with auto-reload
uvicorn api_example:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn api_example:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)

```bash
# Start entire stack (backend + frontend + Redis + PostgreSQL)
docker-compose up -d

# Check services status
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Services will be available at:
- **Frontend**: http://localhost:3001
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Redis**: localhost:6379
- **PostgreSQL**: localhost:5432

### Building Docker Images

```bash
# Build backend image
docker build -t bybit-backend -f Dockerfile.backend .

# Build frontend image
docker build -t bybit-frontend -f frontend/Dockerfile .

# Run containers
docker run -p 8000:8000 -e BYBIT_API_KEY=... -e BYBIT_API_SECRET=... bybit-backend
docker run -p 3001:3001 bybit-frontend
```

### Environment Variables

Create `.env` file in the project root:

```env
# Bybit API Credentials (REQUIRED)
BYBIT_API_KEY=your_api_key_here
BYBIT_API_SECRET=your_api_secret_here

# Database
DATABASE_URL=postgresql://quant:secure_password@localhost:5432/bybit_data

# Redis
REDIS_URL=redis://localhost:6379

# Logging
LOG_LEVEL=INFO
```

---

## 📋 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Web Browser                               │
│                  (localhost:3001)                             │
└────────────────┬────────────────────────────────────────────┘
                 │ HTTP/WebSocket
                 ▼
┌─────────────────────────────────────────────────────────────┐
│              Frontend (React + Vite)                         │
│            - Real-time portfolio display                     │
│            - Options board & charts                          │
│            - Data export                                     │
└────────────────┬────────────────────────────────────────────┘
                 │ REST API + WebSocket
                 ▼
┌─────────────────────────────────────────────────────────────┐
│           Backend API (FastAPI + Uvicorn)                   │
│              (localhost:8000)                                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  API Endpoints:                                      │   │
│  │  - GET /api/v1/risk/portfolio                        │   │
│  │  - GET /api/v1/positions                             │   │
│  │  - GET /api/v1/options-board                         │   │
│  │  - GET /api/v1/payoff-chart                          │   │
│  │  - WS /ws/portfolio (WebSocket)                      │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────┬─────────────┬──────────────────┬────────────────┘
             │             │                  │
      ┌──────▼──────┐ ┌────▼─────┐  ┌─────────▼──────┐
      │ BybitAPI    │ │  Redis   │  │  PostgreSQL    │
      │ (Market     │ │  (Cache) │  │  (History)     │
      │  Data)      │ │          │  │                │
      └─────────────┘ └──────────┘  └────────────────┘
```

---

## 📊 Features Implemented

### 1. Core Greeks
- ✅ **Delta**: Directional exposure per coin
- ✅ **Gamma**: Rate of delta change
- ✅ **Vega**: Sensitivity to IV changes
- ✅ **Theta**: Time decay ($/day)

### 2. Risk Metrics
- ✅ **Margin Utilization**: Used / Total Equity %
- ✅ **IV Comparison**: Position IV vs ATM IV
- ✅ **Slippage Risk**: (Ask-Bid)/Mark spread
- ✅ **Gamma Rent**: Theta/Gamma ratio

### 3. Aggregations
- ✅ **By Coin**: Total Greeks per base coin
- ✅ **By Type**: Futures vs Options breakdown
- ✅ **By Expiry**: Greeks per option series
- ✅ **Portfolio-wide**: Vega/Theta totals

### 4. Warnings
- ✅ **High Margin**: >60% utilization
- ✅ **High Gamma**: Rapid delta changes
- ✅ **High Vega**: Large IV exposure
- ✅ **Negative Theta**: Time decay cost

### 5. Report Generation (NEW!)
- ✅ **Markdown Reports**: Full analysis in MD format
- ✅ **Timestamped Archives**: Keep historical reports
- ✅ **Latest Report**: Always accessible at `reports/latest_analysis.md`
- ✅ **AI-Friendly Format**: Ready for Claude/GPT analysis
- ✅ **Underlying Prices**: BTC/ETH prices included in reports

## 🧪 Testing

```bash
# Run with debug logging
LOG_LEVEL=DEBUG python main.py

# Test specific modules
python -c "
from risk_engine import RiskEngine
print(RiskEngine.parse_symbol('BTC-19DEC25-100000-C'))
"
```

---

## 🔒 Rate Limiting

The `BybitConnector` includes a token bucket rate limiter:
- Default: 50 requests/second
- Configurable via constructor
- Automatically throttles requests

```python
connector = BybitConnector(
    api_key=...,
    api_secret=...,
    rate_limit=30  # More conservative
)
```

---

## 📈 Performance

- **Concurrent fetching**: All market data fetched in parallel using `asyncio.gather`
- **Connection pooling**: `aiohttp` with 100 connections max
- **Caching**: Ticker data cached in memory during analysis
- **Typical execution**: 2-5 seconds for 50+ positions

---

## 🚧 Roadmap

### Ready for Implementation
- [ ] WebSocket streaming for real-time Greeks
- [ ] Historical Greeks tracking (time series)
- [ ] Scenario analysis (stress testing)
- [ ] Greeks hedging recommendations
- [ ] Multi-account aggregation

### Backend Features
- [ ] Redis caching for market data
- [ ] PostgreSQL for position history
- [ ] Celery for background analysis
- [ ] Prometheus metrics

### Frontend Features  
- [ ] React dashboard with live updates
- [ ] Interactive Greeks charts (Recharts/Plotly)
- [ ] Risk alerts and notifications
- [ ] Position builder / simulator

---

## 🐛 Debugging

### Enable detailed logging

```python
# In main.py
setup_logging("DEBUG")
```

### Test individual components

```python
# Test connector
async with BybitConnector(...) as connector:
    positions = await connector.get_positions("option")
    print(positions)

# Test risk engine
from risk_engine import RiskEngine
greeks = RiskEngine.calculate_position_greeks(...)
```

---

## 📝 Code Style

- **Type hints**: Everywhere for IDE support
- **Docstrings**: Google style for all public methods
- **Async/await**: Consistent async patterns
- **Error handling**: Try/except with logging
- **Naming**: Clear, descriptive variable names

---

## ⚠️ Important Notes

### Delta Aggregation
**You CANNOT sum Delta across different coins!**

❌ Wrong: `total_delta = BTC_delta + ETH_delta`  
✅ Correct: Track per coin separately

### Greeks Math
- **Long Call**: Δ ∈ [0,1], Γ>0, ν>0, θ<0
- **Long Put**: Δ ∈ [-1,0], Γ>0, ν>0, θ<0
- **Short**: All Greeks flip sign

### Gamma Rent
- **Negative**: Paying theta to hold gamma (long options)
- **Positive**: Earning theta while exposed to gamma (short options)

---

## 🤝 Contributing

This is production-ready code designed for:
1. Direct integration into FastAPI apps
2. Extension with new risk metrics
3. Integration with other exchanges (using adapter pattern)

To add a new feature:
1. Add data model in `data_models.py`
2. Add calculation in `RiskEngine` (pure logic)
3. Add data fetching in `MarketDataService` (if needed)
4. Wire up in `AnalysisOrchestrator`

---

## 📄 License

MIT License - Use freely in production or personal projects.

---

## 🆘 Support

For questions or issues:
1. Check logs with `LOG_LEVEL=DEBUG`
2. Verify API credentials in `.env`
3. Test Bybit API directly: https://bybit-exchange.github.io/docs/

---

**Built for production. Ready for FastAPI. Async from the ground up.** 🚀