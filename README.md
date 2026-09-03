# Bybit Options Platform

> **Unified platform for options portfolio analysis, risk management, and automated hedging on Bybit.**

**Version:** v0.3.0-alpha  
**Last Updated:** 2026-01-17  
**Status:** Active Development

---

## 🎯 Project Vision

**Bybit Options Platform** — комплексная платформа для профессиональной торговли опционами на Bybit с интеграцией AI-агентов.

### 📊 Модуль 1: Dashboard (Портфолио)

Сводная информация по портфелю с разбивкой по типам активов:

| Функция | Описание |
|---------|----------|
| **Portfolio Summary** | Обзор позиций: Spot, Futures, Options |
| **Strategy Profile** | График P&L стратегии на экспирацию и текущую дату |
| **Greeks Charts** | Визуализация Delta, Gamma, Vega, Theta по портфелю |
| **Risk Metrics** | Margin utilization, Max loss, Breakeven points |

### 📈 Модуль 2: Trading (Торговля)

Торговый интерфейс с полной информацией по инструментам:

| Функция | Описание |
|---------|----------|
| **Multi-Asset Support** | Переключение между BTC / ETH / SOL / XRP |
| **Price Chart** | График цены базового актива (TradingView style) |
| **Options Board** | Доска опционов с греками и IV |
| **Order Book** | Стакан котировок с глубиной рынка |
| **Quick Trade** | Быстрое размещение ордеров |

#### 🤖 Trading Bots (Автоматизация)

| Бот | Статус | Описание |
|-----|--------|----------|
| **Delta Hedger** | ✅ Active | Автоматическое управление дельтой (NEUTRAL/DIRECTIONAL/DEFENSIVE) |
| **Market Maker** | 🔵 Planned | Выставление двусторонних котировок, управление спредом |
| **Volatility Arb** | 🔵 Planned | Арбитраж IV между страйками/экспирациями |

**Delta Hedger Modes:**
| Режим | Триггер | Действие |
|-------|---------|----------|
| NEUTRAL | Default | Target Δ = 0, микро-хедж фьючерсами |
| DIRECTIONAL | H1 Breakout | Bias Δ = ±0.01 BTC |
| DEFENSIVE | H4 Breakout | Покупка защитных опционов |

### 🔧 Модуль 3: Strategy Builder (Конструктор стратегий)

Визуальный конструктор опционных стратегий:

| Функция | Описание |
|---------|----------|
| **Strategy Templates** | Iron Condor, Butterfly, Straddle, Spreads |
| **Custom Builder** | Drag & drop конструктор позиций |
| **P&L Simulator** | Профиль стратегии при разных сценариях |
| **Greeks Calculator** | Суммарные греки комбинации |
| **What-If Analysis** | Симуляция изменения IV, времени, цены |

### 📉 Модуль 4: Analytics (Аналитика)

Инструменты для принятия торговых решений:

| Функция | Описание |
|---------|----------|
| **IV Rank / IV Percentile** | Исторический контекст волатильности |
| **Cumulative Delta** | Агрегированная дельта по страйкам |
| **Open Interest** | Распределение OI по страйкам и экспирациям |
| **Put/Call Ratio** | Соотношение put/call объёмов |
| **Gamma Exposure (GEX)** | Концентрация гаммы маркет-мейкеров |
| **Max Pain** | Уровень максимальной боли для продавцов |

---

## 🧠 AI Integration

Все модули спроектированы для интеграции с AI-агентами и LLM:

```
┌─────────────────────────────────────────────────────────────┐
│                    AI / LLM Layer                           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │   Claude    │ │   GPT-5    │ │  Custom LLM │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└──────────────────────────┬──────────────────────────────────┘
                           │ API / Reports / Webhooks
┌──────────────────────────▼──────────────────────────────────┐
│                  Bybit Options Platform                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │Dashboard │ │ Trading  │ │ Strategy │ │Analytics │       │
│  │          │ │          │ │ Builder  │ │          │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│                           │                                 │
│              ┌────────────▼────────────┐                    │
│              │    Delta Hedger Bot     │                    │
│              │   (Autonomous Agent)    │                    │
│              └─────────────────────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

**AI Use Cases:**
- 📊 Анализ рисков портфеля (`reports/latest_analysis.md`)
- 💡 Рекомендации по хеджированию
- 🔔 Интерпретация алертов и сигналов
- 📝 Генерация торговых отчётов
- ⚡ Автоматическое исполнение через Delta Hedger Bot

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [docs/architecture.md](docs/architecture.md) | System architecture & data flow |
| [docs/ops/running.md](docs/ops/running.md) | Ports, commands, env vars |
| [docs/tasklist/PRODUCT.tasklist.md](docs/tasklist/PRODUCT.tasklist.md) | Product backlog (Closed Beta) |
| [docs/tasklist/HEDGER.tasklist.md](docs/tasklist/HEDGER.tasklist.md) | Delta Hedger development tasks |
| [frontend/README.md](frontend/README.md) | Frontend setup |
| [AGENTS.md](AGENTS.md) | AI agent protocol |

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Web Browser                              │
│                      (localhost:3002)                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                  Frontend (React + Vite)                        │
│   Dashboard • Trading • Strategy Builder • Analytics            │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST + WebSocket
┌────────────────────────────▼────────────────────────────────────┐
│                Backend API (FastAPI :8000)                      │
│  ┌──────────────────┐  ┌──────────────────┐                    │
│  │   Risk Engine    │  │  Market Data Svc │                    │
│  │  Greeks • P&L    │  │  Bybit API       │                    │
│  └──────────────────┘  └──────────────────┘                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│              Delta Hedger Bot (Background)                      │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │Signal Detect │ │Position Mon. │ │Order Executor│            │
│  │ H1/H4 Fractal│ │ Delta Calc   │ │ Bybit Orders │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
│                                                                 │
│  Modes: NEUTRAL → DIRECTIONAL → DEFENSIVE                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │ Bybit API│  │PostgreSQL│  │ Telegram │
        │ (Market) │  │ (State)  │  │ (Alerts) │
        └──────────┘  └──────────┘  └──────────┘
```

### Key Principles

1. **Async First**: All I/O uses `asyncio`
2. **Pure Business Logic**: `RiskEngine` has zero I/O
3. **Type Safety**: Pydantic models everywhere
4. **Separation of Concerns**: Each service has single responsibility
5. **AI-Agent Ready**: Designed for AI-assisted development

---

## 📈 Development Status

| Module | Status | Progress | Notes |
|--------|--------|----------|-------|
| **Dashboard** | 🟡 Partial | 60% | Portfolio + Greeks ✅, Strategy Profile 🔵 |
| **Trading** | 🟡 Partial | 50% | Options Board ✅, Order Book 🔵 |
| **Trading Bots** | 🟡 Partial | 70% | Delta Hedger ✅, Market Maker 🔵 |
| **Strategy Builder** | 🔵 Planned | 0% | Design phase |
| **Analytics** | 🟡 Partial | 40% | IV Rank ✅, GEX/OI 🔵 |

**Legend:** ✅ Complete | 🟡 In Progress | 🔵 Planned

---

## 💰 Business Model

### Freemium + Commission

| Tier | Access | Price |
|------|--------|-------|
| **Free** | Dashboard, Trading, Strategy Builder | Free (Bybit referral commission) |
| **Pro** | Analytics + AI Recommendations | $29/month |
| **Premium** | Full AI Agents + API Access | $99/month |

### Revenue Streams

1. **Referral Commission** — Users trade via platform, we earn Bybit referral %
2. **Subscription** — Pro/Premium access to advanced features
3. **API Access** — Pay-per-call for signals (future)

### Target Users

- 🎯 **Retail Options Traders** — Individual crypto options traders
- 🏢 **Prop Desks** — Small trading firms
- 🔬 **Quant Researchers** — Backtesting and analysis

---

## ⚠️ Current Limitations

| Limitation | Status | Plan |
|------------|--------|------|
| **Single Exchange** | Bybit only | Deribit planned |
| **Options Focus** | BTC options primary | ETH + more assets planned |
| **Spot View Only** | View positions, no trading | Spot trading planned |
| **Desktop Only** | Web interface | Mobile app future |
| **Single User** | No multi-account | Team features planned |

---

## 📦 Installation

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
BYBIT_API_KEY=your_api_key_here
BYBIT_API_SECRET=your_secret_here
DATABASE_URL=postgresql://user:pass@localhost:5432/bybit_options
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

# Start development server (port 3002)
npm run dev
```

The frontend automatically connects to the backend API at `http://localhost:8000/api/v1`.

---

## 🤖 Delta Hedger Bot

Автономный бот для управления дельтой опционного портфеля.

### Features

- **NEUTRAL Mode**: Target delta = 0, micro-hedge with futures
- **DIRECTIONAL Mode**: Bias delta ±0.01 BTC on H1 breakout
- **DEFENSIVE Mode**: Buy protective options on H4 breakout

### Quick Start

```bash
# Run hedger
python scripts/run_hedger.py

# Dry-run (no real orders)
python scripts/run_hedger.py --dry-run
```

### Configuration

See `hedger_config` table in PostgreSQL or environment variables.

### Tasks & Progress

See [docs/tasklist/HEDGER.tasklist.md](docs/tasklist/HEDGER.tasklist.md) for development status.

**Current Status:** Phase 3 (Defensive Mode) ✅ Complete

---

## 🔌 FastAPI Integration Example

See `bybit_options/api/app.py` for the canonical implementation (with
`apps/api.py` and `api_example.py` as backward-compatible shims):

```python
from fastapi import FastAPI, Depends
from bybit_options.services.bybit_connector import BybitConnector
from bybit_options.orchestration.analysis_orchestrator import AnalysisOrchestrator
from bybit_options.models import PortfolioRiskModel

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
uvicorn bybit_options.api.app:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn bybit_options.api.app:app --host 0.0.0.0 --port 8000 --workers 4
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
- **Frontend**: http://localhost:3002
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
docker run -p 3002:3002 bybit-frontend
```

### Environment Variables

Create `.env` file in the project root:

```env
# Bybit API Credentials (REQUIRED)
BYBIT_API_KEY=your_api_key_here
BYBIT_API_SECRET=your_api_secret_here

# Database (REQUIRED)
DATABASE_URL=postgresql://user:password@localhost:5432/bybit_options

# Redis (OPTIONAL - for caching)
REDIS_URL=redis://localhost:6379

# Logging
LOG_LEVEL=INFO
```

---

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/risk/portfolio` | GET | Portfolio Greeks & Risks |
| `/api/v1/positions` | GET | Current positions |
| `/api/v1/options-board` | GET | Options chain with IV |
| `/api/v1/payoff-chart` | GET | P&L projection data |
| `/ws/portfolio` | WS | Real-time updates |

See [Backend API docs](http://localhost:8000/docs) for full OpenAPI spec.

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
from bybit_options.core.risk_engine import RiskEngine
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

### Delta Hedger (In Progress)
- [x] Phase 1: Core Bot (NEUTRAL mode)
- [x] Phase 2: Signal Detection (H1/H4 fractals)
- [x] Phase 3: Defensive Mode (options buying)
- [ ] Phase 4: Production Ready (Telegram alerts, Docker)

### Risk Engine
- [ ] WebSocket streaming for real-time Greeks
- [ ] Historical Greeks tracking (time series)
- [ ] Scenario analysis (stress testing)
- [ ] Greeks hedging recommendations

### Frontend
- [x] React dashboard with live updates
- [x] Options board & charts
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
from bybit_options.services.bybit_connector import BybitConnector

async with BybitConnector(...) as connector:
    positions = await connector.get_positions("option")
    print(positions)

# Test risk engine
from bybit_options.core.risk_engine import RiskEngine
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
1. Add data model in `bybit_options/models`
2. Add calculation in `bybit_options/core/risk_engine.py` (pure logic)
3. Add data fetching in `bybit_options/services/market_data_service.py` (if needed)
4. Wire up in `bybit_options/orchestration/analysis_orchestrator.py`

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
