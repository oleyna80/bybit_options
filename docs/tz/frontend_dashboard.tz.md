# 🖥️ Frontend Dashboard — Модульная Архитектура

**Статус:** 📝 DRAFT  
**Дата:** 2026-01-19  
**Приоритет:** 🟡 MEDIUM  

---

## 📋 Текущее состояние

### Tech Stack
- **Framework:** React 18 + TypeScript
- **Bundler:** Vite
- **Styling:** Tailwind CSS
- **State:** Zustand
- **Charts:** Recharts
- **Icons:** Lucide React

### Текущие вкладки (App.tsx)
| Tab | Описание | Статус |
|-----|----------|--------|
| **Dashboard** | Portfolio + MetricsCards | ✅ Базово работает |
| **Analytics** | IV Rank Chart | 🟡 Частично |
| **Constructor** | Strategy Builder | ❌ Placeholder |
| **Trading** | Options Board | ✅ Работает |

---

## 🎯 Предлагаемые модули

### Модуль 0: Portfolio Summary (Сводка) 🆕 [PRIORITY: HIGH]

**Назначение:** Общая картина портфеля — активы, фьючерсы, опционы.

**Компоненты:**
```
components/Portfolio/
├── PortfolioSummary.tsx    # Общая сводка всего портфеля
├── AssetBreakdown.tsx      # Разбивка по типам активов
├── ExposureGauge.tsx       # Визуализация риска
└── MarginStatus.tsx        # Статус маржи
```

**Wireframe:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  💼 PORTFOLIO SUMMARY                                      Total: $125,430  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐ │
│  │ 💰 SPOT / WALLET    │  │ 📈 FUTURES          │  │ 🎯 OPTIONS          │ │
│  │                     │  │                     │  │                     │ │
│  │ USDT: $50,000       │  │ BTCUSDT Perp        │  │ Calls: 5 positions  │ │
│  │ BTC:  0.5 ($46,500) │  │ Size: +2.5 BTC      │  │ Puts:  3 positions  │ │
│  │ ETH:  2.0 ($6,400)  │  │ P&L: +$1,230        │  │ Net Premium: -$2,100│ │
│  │                     │  │ Leverage: 3x        │  │ Net P&L: +$850      │ │
│  │ Total: $102,900     │  │                     │  │                     │ │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────┐  ┌─────────────────────────────┐│
│  │ ASSET ALLOCATION                       │  │ MARGIN STATUS              ││
│  │                                        │  │                            ││
│  │  [██████████████░░░░░░] Spot 65%      │  │  Used:  $45,000 (36%)      ││
│  │  [████████░░░░░░░░░░░░] Futures 18%   │  │  Free:  $80,430            ││
│  │  [█████░░░░░░░░░░░░░░░] Options 17%   │  │  [██████░░░░░░░░] 36%      ││
│  │                                        │  │  ⚠️ Warning at 70%        ││
│  └───────────────────────────────────────┘  └─────────────────────────────┘│
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### Модуль 1: Strategy P/L Chart 🆕 [PRIORITY: HIGH]

**Назначение:** Payoff диаграмма — текущий P&L и на экспирацию.

**Компоненты:**
```
components/Charts/
├── StrategyPayoff.tsx      # Main payoff chart
├── PayoffControls.tsx      # Toggle: Now / Expiry / Both
├── BreakevenMarkers.tsx    # Breakeven points
└── PriceSlider.tsx         # Interactive price selector
```

**Wireframe:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  📊 STRATEGY P&L                          [Current] [Expiry] [Both] [+7d]   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│     P&L ($)                                                                 │
│        ▲                                                                    │
│  +5,000├─────────────────────────╲                                          │
│        │                      ╱╲  ╲                                         │
│  +2,500├──────────────────╱────╲───╲────────────── Expiry (blue)           │
│        │               ╱╱      ╲   ╲                                        │
│      0 │─────────────╱╱─────────╲───╲────────────                           │
│        │           ╱  ╲          ╲   ╲   Current (white)                    │
│  -2,500├─────────╱─────╲──────────╲───╲──────────                           │
│        │        ╱       ╲                                                   │
│  -5,000├───────╱─────────╲───────────────────────                           │
│        │                                                                    │
│        └───────┬────────┬────────┬────────┬────────┬────────► Price ($)    │
│             85,000   90,000   93,250  96,000  100,000  105,000             │
│                               ↑ NOW                                         │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Max Profit: +$4,200 @ $95,000   │ Max Loss: -$3,500 @ <$88,000      │   │
│  │ Breakeven 1: $89,500            │ Breakeven 2: $97,200              │   │
│  │ Probability of Profit: 62%      │ Expected P&L: +$1,100             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### Модуль 2: Greeks Charts 🆕 [PRIORITY: HIGH]

**Назначение:** Визуализация Greeks по цене и времени.

**Компоненты:**
```
components/Charts/
├── GreeksOverview.tsx      # Summary cards (Delta/Gamma/Theta/Vega)
├── GreeksByPrice.tsx       # Delta/Gamma curve vs price
├── ThetaDecay.tsx          # Theta decay over time
└── VegaExposure.tsx        # Vega by strike/expiry
```

**Wireframe:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  📈 GREEKS ANALYSIS                                       [Total] [By Leg]  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐│
│  │ Δ DELTA     │  │ Γ GAMMA     │  │ Θ THETA     │  │ ν VEGA             ││
│  │   -15.2     │  │   +0.82     │  │   +$85      │  │   -$420            ││
│  │   BTC       │  │   /1%       │  │   /day      │  │   /1% IV           ││
│  │   Short ⬇   │  │   High ⚡   │  │   Earning ✅│  │   Short Vol ⬇     ││
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘│
│                                                                             │
│  ┌───────────────────────────────────┐  ┌───────────────────────────────┐  │
│  │ DELTA/GAMMA vs PRICE              │  │ THETA DECAY                   │  │
│  │                                   │  │                               │  │
│  │      Delta                        │  │  Theta                        │  │
│  │  +20 ├─────────────╱──────        │  │  +100├─────╲                  │  │
│  │      │          ╱╱                │  │      │      ╲                 │  │
│  │    0 │────────╱╱──────────        │  │   +50├───────╲────            │  │
│  │      │     ╱╱                     │  │      │        ╲               │  │
│  │  -20 ├──╱╱────────────────        │  │    0 ├─────────╲──            │  │
│  │      └──────────────────► Price   │  │      └──────────► Days        │  │
│  │                                   │  │      30   20   10   0         │  │
│  └───────────────────────────────────┘  └───────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ VEGA HEATMAP BY STRIKE & EXPIRY                                       │ │
│  │                                                                       │ │
│  │ Expiry  │ 85K  │ 90K  │ 95K  │ 100K │ 105K                           │ │
│  │ ────────│──────│──────│──────│──────│──────                           │ │
│  │ 24JAN   │ ░░░  │ ▓▓▓  │ ███  │ ▓▓▓  │ ░░░   (darker = higher vega)  │ │
│  │ 31JAN   │ ░░   │ ▓▓   │ ██   │ ▓▓   │ ░░                             │ │
│  │ 28FEB   │ ░    │ ▓    │ █    │ ▓    │ ░                              │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### Модуль 3: Delta Analytics Dashboard 🆕

**Назначение:** Визуализация объёмной дельты для подтверждения торговых сигналов.

**Компоненты:**
```
components/Delta/
├── DeltaOverview.tsx       # Summary card: Cumulative delta, OI change
├── DeltaChart.tsx          # Real-time delta chart (1m/5m/1h buckets)
├── WhaleTradesTable.tsx    # Recent large trades >5 BTC
├── OrderbookImbalance.tsx  # Bid/Ask imbalance gauge
└── DeltaDivergence.tsx     # Alert when delta diverges from price
```

**API endpoints нужны:**
```
GET /api/delta/metrics?symbol=BTCUSDT&interval=1h&limit=24
GET /api/delta/summary?symbol=BTCUSDT
GET /api/delta/trades?symbol=BTCUSDT&limit=50
```

**Wireframe:**
```
┌─────────────────────────────────────────────────────────────────────┐
│  📊 DELTA ANALYTICS                                    [BTC ▼] [4H] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │
│  │ Buy Volume  │  │ Sell Volume │  │ Net Delta   │  │ OI Change  │ │
│  │   +350 BTC  │  │   -280 BTC  │  │  +70.2 BTC  │  │ +1,500 📈 │ │
│  │   ▲ 12%     │  │   ▼ 8%      │  │    ✅       │  │ contracts  │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘ │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │                    DELTA CHART (1m buckets)                   │ │
│  │  [Bar chart: green=buy, red=sell, line=cumulative delta]      │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌────────────────────────────┐  ┌───────────────────────────────┐ │
│  │ 🐋 WHALE TRADES            │  │ ORDERBOOK IMBALANCE           │ │
│  │                            │  │                               │ │
│  │ 15.3 BTC BUY @ $100,250    │  │    [═════════█░░░░░]          │ │
│  │ 12.1 BTC SELL @ $100,180   │  │     65% BID | 35% ASK         │ │
│  │ 8.5 BTC BUY @ $100,300     │  │     Bullish imbalance         │ │
│  └────────────────────────────┘  └───────────────────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

### Модуль 2: Fractal Signals Dashboard 🆕

**Назначение:** Отображение ключевых фракталов с Delta-обогащением.

**Компоненты:**
```
components/Fractals/
├── FractalOverview.tsx     # Active key fractals summary
├── FractalChart.tsx        # Price chart with fractal markers
├── FractalTable.tsx        # List of fractals with confidence score
├── FractalAlert.tsx        # Real-time alert on new fractal
└── FractalHistory.tsx      # Historical fractal performance
```

**API endpoints нужны:**
```
GET /api/fractals/active?symbol=BTCUSDT&timeframe=H4
GET /api/fractals/history?symbol=BTCUSDT&limit=50
GET /api/fractals/{id}/details
```

**Wireframe:**
```
┌─────────────────────────────────────────────────────────────────────┐
│  🔺 FRACTAL SIGNALS                               [BTC ▼] [H4] [D1] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                     PRICE CHART + FRACTALS                   │   │
│  │   [Candlestick chart with BB bands, Alligator, fractals]    │   │
│  │                                                              │   │
│  │      ▲ 98,500 (Key Up Fractal)  Confidence: 85% ✅           │   │
│  │      ▼ 92,000 (Key Down Fractal) Confidence: 72%             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ ACTIVE KEY FRACTALS                                          │   │
│  │                                                              │   │
│  │ Type   | Price   | Time      | Delta 4H | Conf. | Status    │   │
│  │ ───────|─────────|───────────|──────────|───────|───────────│   │
│  │ ▲ UP   | 98,500  | 12:00     | +45 BTC  | 85%   | CONFIRMED │   │
│  │ ▼ DOWN | 92,000  | 08:00     | -20 BTC  | 72%   | PENDING   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

### Модуль 3: Enhanced Portfolio Module 🔄

**Назначение:** Улучшенная визуализация портфеля с группировкой.

**Компоненты:**
```
components/Portfolio/
├── PortfolioOverview.tsx   # Total P&L, Delta, Theta status
├── PositionsByExpiry.tsx   # Group positions by expiry
├── GreeksHeatmap.tsx       # Visual heatmap of Greeks
├── RiskGauge.tsx           # Delta/Margin risk indicator
└── TradeHistory.tsx        # Recent trades from /api/trades
```

---

### Модуль 4: Strategy Constructor 🔨

**Назначение:** Visual multi-leg strategy builder.

**Компоненты:**
```
components/Constructor/
├── LegBuilder.tsx          # Add/edit legs (call/put/futures)
├── PayoffChart.tsx         # P&L at expiry + current
├── StrategyTemplates.tsx   # Presets: Condor, Butterfly, etc.
├── GreeksSummary.tsx       # Total Greeks for strategy
└── ExecutePanel.tsx        # Send to Bybit (future)
```

---

### Модуль 5: Settings & Config ⚙️

**Назначение:** Настройки приложения.

**Компоненты:**
```
components/Settings/
├── DeltaThresholds.tsx     # Configure BTC/ETH thresholds
├── AlertSettings.tsx       # Telegram/browser notifications
├── APIConnection.tsx       # API status, reconnect
└── ThemeSettings.tsx       # Dark/Light mode
```

---

## 📁 Предлагаемая структура

```
frontend/src/
├── components/
│   ├── Common/              # Shared UI components
│   │   ├── Card.tsx
│   │   ├── Button.tsx
│   │   ├── Select.tsx
│   │   ├── LoadingSpinner.tsx
│   │   └── ErrorMessage.tsx
│   │
│   ├── Delta/               # 🆕 Delta Analytics
│   │   ├── DeltaOverview.tsx
│   │   ├── DeltaChart.tsx
│   │   ├── WhaleTradesTable.tsx
│   │   └── OrderbookImbalance.tsx
│   │
│   ├── Fractals/            # 🆕 Fractal Signals
│   │   ├── FractalChart.tsx
│   │   ├── FractalTable.tsx
│   │   └── FractalAlert.tsx
│   │
│   ├── Portfolio/           # Enhanced Portfolio
│   │   ├── PortfolioOverview.tsx
│   │   ├── PositionsByExpiry.tsx
│   │   └── GreeksHeatmap.tsx
│   │
│   ├── OptionsBoard/        # Trading
│   │   └── OptionsBoard.tsx
│   │
│   ├── Charts/              # Shared charts
│   │   ├── IVRankChart.tsx
│   │   ├── PayoffChart.tsx
│   │   └── PriceChart.tsx
│   │
│   └── Layout/              # 🆕 App layout
│       ├── Header.tsx
│       ├── Sidebar.tsx
│       ├── TabNav.tsx
│       └── Footer.tsx
│
├── hooks/                   # 🆕 Custom hooks
│   ├── useDelta.ts          # Delta API hooks
│   ├── useFractals.ts       # Fractals API hooks
│   ├── usePortfolio.ts      # Portfolio hooks
│   └── useWebSocket.ts      # WS connection
│
├── services/
│   ├── api.ts               # REST client
│   ├── websocket.ts         # WS client
│   └── deltaApi.ts          # 🆕 Delta-specific API
│
├── stores/
│   ├── portfolioStore.ts    # Zustand store
│   ├── deltaStore.ts        # 🆕 Delta state
│   └── fractalStore.ts      # 🆕 Fractals state
│
├── types/
│   ├── portfolio.ts
│   ├── delta.ts             # 🆕 Delta types
│   └── fractals.ts          # 🆕 Fractal types
│
└── App.tsx                  # Main app with tabs
```

---

## 🗓️ Приоритеты реализации

### Phase 1 (MVP) — 4-6 часов
1. **Delta Overview Card** — summary с current delta
2. **Delta Chart** — простой bar chart
3. **API integration** — подключить /api/delta/*

### Phase 2 — 4-6 часов
1. **WhaleTradesTable** — таблица крупных сделок
2. **OrderbookImbalance** — gauge component
3. **Fractal Table** — list of key fractals

### Phase 3 — 4-6 часов
1. **Fractal Chart** — candlestick with markers
2. **Strategy Constructor** — basic leg builder
3. **Settings page** — thresholds config

---

## 🔌 Необходимые API endpoints (Backend)

| Endpoint | Описание | Статус |
|----------|----------|--------|
| `GET /api/delta/metrics` | Delta metrics by interval | ❌ TODO |
| `GET /api/delta/summary` | Daily delta summary | ❌ TODO |
| `GET /api/delta/trades` | Recent whale trades | ❌ TODO |
| `GET /api/fractals/active` | Active key fractals | ❌ TODO |
| `GET /api/trades` | Trade history | ⚠️ Error |
| `WS /ws/delta` | Real-time delta updates | ❌ TODO |

---

## Следующий шаг

1. **Создать FRONTEND.tasklist.md** с детальными задачами?
2. **Начать с Delta Overview Card**?
3. **Сначала доделать backend API**?
