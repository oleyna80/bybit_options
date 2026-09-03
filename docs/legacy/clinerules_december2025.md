# ARCHIVED: Options Risk Engine - Project Rules

> ⚠️ **STATUS: ARCHIVED**  
> This file was the original context document for Claude Code (December 2025).  
> **Current authoritative sources:**  
> - `.agent/*` — Agent roles and conventions  
> - `agreements/*` — Routing and permissions  
> - `docs/ops/running.md` — Runtime configuration (ports, commands)  
> - `docs/architecture.md` — System architecture  
>  
> **Archived:** 2026-01-17  
> **Reason:** Paths and ports were outdated; information split into specialized docs.

---

> Project-specific context for Claude Code. Global rules in ~/CLAUDE.md

---

## 📍 Project Info

**Name:** Bybit Options Risk Engine  
**Path:** `/mnt/e/Python_project/bybit-options-risk-engine` *(OUTDATED — see docs/ops/running.md)*  
**Status:** 🔴 CRITICAL BUG - 404 API errors *(May be resolved — verify current state)*  
**Started:** December 2025

---

## 🏗️ Architecture

### Backend (Python FastAPI)
```
Port: 8000
Entry: api_example.py

Modules:
├── api_example.py           # FastAPI app, endpoints
├── payoff_calculator.py     # P&L calculations
├── risk_engine.py           # Greeks (Black-Scholes)
├── live_state_keeper.py     # State management
├── websocket_manager.py     # Real-time updates
└── bybit_connector.py       # Bybit API wrapper

Key Endpoints:
- GET  /api/v1/options-board     # Options chain data
- GET  /api/v1/risk/portfolio    # Portfolio Greeks
- GET  /api/v1/positions         # Current positions
- GET  /api/v1/payoff-chart      # P&L projections
- GET  /api/v1/trade-log         # Trade history
- WS   /ws/portfolio             # Real-time updates
```

### Frontend (React + TypeScript + Vite)
```
Port: 3002 (was 3001, changed today)
Entry: src/main.tsx

Structure:
├── services/
│   ├── api.ts              # 🔴 CURRENT BUG HERE!
│   ├── websocket.ts        # WebSocket client
│   └── export.ts           # Data export
├── components/
│   ├── OptionsBoard/       # Options chain table
│   ├── Portfolio/          # Risk metrics
│   ├── Charts/             # Payoff charts
│   └── TradeLog/           # Trade history
├── stores/
│   └── portfolioStore.ts   # Zustand state
└── types/
    └── index.ts            # TypeScript types

Styling: Tailwind CSS (configured, working)
```

### Tech Stack
- **Backend:** Python 3.x, FastAPI, uvicorn, pybit, numpy, pandas
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS, Recharts
- **API:** Bybit mainnet (options market data)
- **Real-time:** WebSocket
- **State:** Zustand

---

## 🔴 CURRENT CRITICAL BUG

**Problem:** All API requests return 404

**Root Cause:** Path duplication in `frontend/src/services/api.ts`

**Details:**
```typescript
// Current (WRONG):
const API_BASE_URL = '/api/v1';              // ✅ Correct
const endpoint = '/api/v1/options-board';    // ❌ WRONG - duplicates prefix
// Result: '/api/v1' + '/api/v1/options-board' = '/api/v1/api/v1/options-board'

// Should be:
const API_BASE_URL = '/api/v1';              // ✅ Keep
const endpoint = '/options-board';           // ✅ Fix - remove prefix
// Result: '/api/v1' + '/options-board' = '/api/v1/options-board'
```

**Files to Fix:**
- `frontend/src/services/api.ts` - Remove `/api/v1` from all endpoints

**Affected Methods:**
- getOptionsBoard() - line ~171
- getPortfolio() - line ~178
- getPositions() - line ~184
- getPayoffChart() - line ~197
- getTradeLog() - line ~212
- getMetrics() - line ~218
- getMargin() - line ~224
- getCoinRisk() - line ~230

**DO NOT TOUCH:**
- exportData() - line ~236 (already correct)
- healthCheck() - line ~243 (already correct)

**Priority:** 🔴 CRITICAL - blocks all functionality

---

## ✅ What Works

- ✅ Backend runs on port 8000
- ✅ Frontend runs on port 3002
- ✅ Vite proxy configured correctly (`vite.config.ts`)
- ✅ Backend returns data: `curl http://localhost:8000/api/v1/options-board` works
- ✅ Tailwind CSS fixed (success/danger colors added)
- ✅ Git initialized, initial commit done
- ✅ Dependencies installed (Python venv + npm)

---

## ❌ Known Issues

1. **API 404 errors** (current priority)
2. **WebSocket might use Mock** - needs verification after API fix
3. **Greeks accuracy** - formulas need validation (lower priority)
4. **No auto-start script** - backend must be started manually

---

## 🎯 Next Tasks (Priority Order)

### 1. Fix API endpoints (NOW!)
- Remove `/api/v1` prefix from all endpoints in `api.ts`
- Test: Network tab should show 200 OK
- Verify: Backend logs show incoming requests

### 2. Verify WebSocket (AFTER #1)
- Check `frontend/src/services/websocket.ts`
- Ensure using real WebSocket, not Mock
- Test: Real-time portfolio updates work

### 3. Validate Greeks calculations (LATER)
- Review Black-Scholes formulas in `risk_engine.py`
- Compare with Bybit UI values
- Test with known examples (ATM options Delta ~0.5)

### 4. Auto-start backend (LOW PRIORITY)
- Create `startup.sh` script
- Configure `.vscode/tasks.json`
- Add `README_START.md` instructions

---

## 🔧 Development Commands

### Start Backend
```bash
cd /mnt/e/Python_project/bybit-options-risk-engine
source venv/bin/activate
uvicorn api_example:app --reload --port 8000
```

### Start Frontend
```bash
cd /mnt/e/Python_project/bybit-options-risk-engine/frontend
npm run dev
# Opens on http://localhost:3002
```

### Test Backend
```bash
# Health check
curl http://localhost:8000/

# Options board
curl http://localhost:8000/api/v1/options-board

# Portfolio
curl http://localhost:8000/api/v1/risk/portfolio

# Swagger docs
open http://localhost:8000/docs
```

### Debug Frontend
```
Browser: http://localhost:3002
F12 → Console: JavaScript errors
F12 → Network: API requests (filter: "api")
```

---

## 📦 Dependencies

### Python (backend)
```
fastapi
uvicorn[standard]
pybit
numpy
pandas
websockets
python-dotenv
```

### Node.js (frontend)
```
react
react-dom
typescript
vite
tailwindcss
recharts
zustand
lucide-react
```

---

## 🔐 Environment Variables

**File:** `.env` (not in git, use `.env.example`)

```bash
# Bybit API (mainnet)
BYBIT_API_KEY=your_key
BYBIT_API_SECRET=your_secret

# API URLs
VITE_API_URL=/api/v1  # Frontend uses this

# Network
BYBIT_TESTNET=false
```

---

## 🎨 Code Patterns

### Backend API Endpoint Pattern
```python
@app.get("/api/v1/endpoint", summary="Description")
async def endpoint_name(
    param: str = Query("default", description="Param desc"),
    orchestrator: AnalysisOrchestrator = Depends(get_orchestrator)
):
    """Detailed docstring if complex logic."""
    result = orchestrator.method(param)
    return result
```

### Frontend API Call Pattern
```typescript
// In api.ts
async getEndpoint(filters: FilterType = {}): Promise<ApiResponse<DataType>> {
  const params = new URLSearchParams();
  if (filters.param) params.append('param', filters.param);
  
  const query = params.toString();
  const endpoint = `/endpoint${query ? `?${query}` : ''}`;
  const cacheKey = this.generateCacheKey('endpoint', filters);
  return this.request<DataType>(endpoint, {}, cacheKey, 30 * 1000);
}

// In component
import apiClient from '@/services/api';

const { data, error } = await apiClient.getEndpoint({ param: 'value' });
```

### WebSocket Pattern
```typescript
// Connect
const ws = new WebSocket('ws://localhost:8000/ws/portfolio');

// Listen
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  updateStore(data);
};

// Reconnect logic
ws.onclose = () => {
  setTimeout(() => reconnect(), 5000);
};
```

---

## 🐛 Debugging Tips

### Backend Issues
```bash
# Check if backend running
curl http://localhost:8000/

# Check logs (terminal with uvicorn)
# Should see: INFO: "GET /api/v1/endpoint HTTP/1.1" 200 OK

# Python errors
# Check traceback in terminal

# Bybit API issues
# Verify credentials in .env
# Check rate limits
```

### Frontend Issues
```javascript
// Check API calls (browser console)
fetch('/api/v1/options-board')
  .then(r => r.json())
  .then(d => console.log(d));

// Check WebSocket (browser console)
const ws = new WebSocket('ws://localhost:8000/ws/portfolio');
ws.onmessage = (e) => console.log('WS:', e.data);

// Check Vite proxy (vite.config.ts)
// Should have: proxy: { '/api': { target: 'http://localhost:8000' } }
```

### Network Issues
```bash
# Check ports in use
netstat -tuln | grep 8000
netstat -tuln | grep 3002

# Kill process on port
kill $(lsof -ti:8000)
```

---

## 📚 Key Files Reference

### Critical Files (modify carefully)
- `api_example.py` - All backend endpoints
- `risk_engine.py` - Greeks calculations ($$$ critical)
- `frontend/src/services/api.ts` - 🔴 CURRENT BUG
- `frontend/src/stores/portfolioStore.ts` - Global state
- `vite.config.ts` - Proxy configuration

### Configuration Files
- `tailwind.config.js` - Tailwind setup (success/danger colors added)
- `tsconfig.json` - TypeScript config
- `requirements.txt` - Python dependencies
- `package.json` - Node dependencies

### Documentation
- `README.md` - Project overview
- `INTEGRATION.md` - Integration guide
- `COMPLETION_SUMMARY.md` - Development history
- `options_engine_continuation.md` - Context document (comprehensive)

---

## 🚫 Don't Touch Unless Necessary

- `venv/` - Virtual environment
- `node_modules/` - Node packages
- `.git/` - Git history
- `dist/` - Build output

---

## 💡 Product Context

**Purpose:** Real-time options portfolio risk analysis

**Target User:** Options traders on Bybit

**Key Features:**
1. Live options chain with Greeks
2. Portfolio-wide risk metrics (Delta, Gamma, Vega, Theta)
3. P&L projections (payoff charts)
4. Trade history and analysis
5. Real-time WebSocket updates

**Business Value:**
- Quick risk assessment
- Better hedging decisions
- Avoid over-concentration
- Track performance

**Future Plans:**
- Auto-hedging suggestions
- Historical backtesting
- Multi-exchange support
- Mobile app

---

## 📊 Success Metrics

### Current Sprint
- [ ] Fix 404 API errors
- [ ] Verify real-time updates work
- [ ] Validate Greeks accuracy
- [ ] Export functionality works

### Phase 1 (MVP)
- [ ] All endpoints return real data
- [ ] No console errors
- [ ] Greeks match Bybit UI (±5%)
- [ ] Can export portfolio data

### Phase 2 (Production Ready)
- [ ] Auto-start scripts work
- [ ] Error handling robust
- [ ] Unit tests for critical logic
- [ ] Docker containerization

---

**Last Updated:** December 21, 2025  
**Current Focus:** Fix API 404 errors in `api.ts`

---

## Quick Commands for Claude Code

```bash
# Fix current bug (after you make changes)
cd frontend && npm run dev

# Test fix
curl http://localhost:8000/api/v1/options-board
# Open: http://localhost:3002 (F12 Network tab)

# If broken, rollback
git checkout frontend/src/services/api.ts
```
