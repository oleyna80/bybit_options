# Frontend-Backend Integration Guide

Полная документация по интеграции React frontend с FastAPI backend для Bybit Options Portfolio Risk Analyzer.

## Таблица содержания

1. [Архитектура](#архитектура)
2. [Быстрый старт](#быстрый-старт)
3. [API Endpoints](#api-endpoints)
4. [WebSocket](#websocket)
5. [Кэширование](#кэширование)
6. [Обработка ошибок](#обработка-ошибок)
7. [Развертывание](#развертывание)

---

## Архитектура

### Компоненты системы

```
Frontend (React)              Backend (FastAPI)        External Services
┌─────────────────┐          ┌─────────────────┐      ┌──────────────┐
│                 │ REST API │                 │      │  Bybit API   │
│  React App      ├─────────►│ FastAPI Server  ├─────►│              │
│  (Vite)         │◄─────────│                 │◄─────┤              │
│                 │ WebSocket│  - api (bybit_options.api.app) │      │              │
└─────────────────┘          │  - orchestrator (bybit_options.orchestration) │      └──────────────┘
                             │  - risk_engine (bybit_options.core) │
                             └────────┬────────┘
                                      │
                        ┌─────────────┴────────────┐
                        ▼                          ▼
                    ┌────────┐              ┌──────────┐
                    │ Redis  │              │PostgreSQL│
                    │ (Cache)│              │(History) │
                    └────────┘              └──────────┘
```

### Поток данных

1. **Frontend запрашивает данные** → REST API endpoint
2. **Backend получает запрос** → Загружает данные из Bybit API
3. **Backend обрабатывает** → Расчет Greeks, risk metrics
4. **Backend возвращает** → JSON response с полными данными
5. **Frontend отображает** → React компоненты обновляют UI
6. **WebSocket обновления** → Real-time изменения портфеля

---

## Быстрый старт

### 1. Development окружение

```bash
# Backend setup
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend setup
cd frontend
npm install
cd ..

# Создать .env файл
cat > .env << EOF
BYBIT_API_KEY=your_key
BYBIT_API_SECRET=your_secret
LOG_LEVEL=INFO
EOF
```

### 2. Запуск сервисов (в отдельных терминалах)

```bash
# Terminal 1: Backend
uvicorn bybit_options.api.app:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev
```

### 3. Открыть в браузере

```
http://localhost:3001
```

### 3. Docker Compose (все сервисы сразу)

```bash
docker-compose up -d
```

Сервисы будут доступны:
- Frontend: http://localhost:3001
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

---

## API Endpoints

### Portfolio Data

#### GET `/api/v1/risk/portfolio`
Получить полный анализ портфеля с Greeks и risk metrics.

**Response:**
```json
{
  "timestamp": "2025-12-19T13:28:00Z",
  "margin": {
    "account_type": "UNIFIED",
    "total_equity": 52345.67,
    "margin_ratio": 45.5,
    "health_status": "HEALTHY"
  },
  "coin_risks": {
    "BTC": {
      "base_coin": "BTC",
      "underlying_price": 95000.50,
      "total_greeks": {
        "delta_coin": 0.5234,
        "gamma_coin": 0.000234,
        "vega_usd": 4567.89,
        "theta_usd": -123.45
      },
      "positions": [...]
    }
  },
  "total_vega_usd": 4567.89,
  "total_theta_usd": -123.45,
  "warnings": []
}
```

#### GET `/api/v1/positions`
Получить список всех позиций.

**Query Parameters:**
- `category` (optional): "linear" или "option"

**Response:**
```json
{
  "count": 10,
  "positions": [
    {
      "symbol": "BTC-19DEC25-100000-C-USDT",
      "side": "Buy",
      "size": 1.5,
      "pos_type": "OPTION",
      "greeks": {...}
    }
  ]
}
```

### Options Data

#### GET `/api/v1/options-board`
Получить доску опционов с фильтрацией.

**Query Parameters:**
- `base_coin` (default: "BTC"): BTC, ETH, etc.
- `expiry` (optional): "19DEC25", "26DEC25"
- `option_type` (optional): "CALL" или "PUT"
- `sort_by` (default: "strike"): strike, mark_price, delta, iv
- `sort_order` (default: "asc"): asc или desc

**Response:**
```json
{
  "underlying_price": 95000.50,
  "base_coin": "BTC",
  "expiry": "19DEC25",
  "total_options": 45,
  "options": [
    {
      "strike": 90000,
      "type": "C",
      "bid": 1234.5,
      "ask": 1256.8,
      "mark": 1245.0,
      "iv": 0.65,
      "delta": 0.75,
      "gamma": 0.000045,
      "vega": 234.56,
      "theta": -45.67
    }
  ],
  "statistics": {
    "atm_iv": 0.62,
    "bid_ask_spread_avg": 22.3
  }
}
```

### Payoff Chart

#### GET `/api/v1/payoff-chart`
Получить данные для графика P&L портфеля.

**Query Parameters:**
- `days_to_expiry` (optional): Дни до экспирации
- `price_range_pct` (default: 20): % диапазон от текущей цены
- `include_theta` (default: false): Включить theta decay

**Response:**
```json
{
  "current_price": 95000.50,
  "current_pnl": 1234.56,
  "price_range": [76000, 78000, 80000, ...],
  "pnl": [-1500, -1200, -900, ...],
  "breakeven_points": [89000, 101000],
  "max_profit": 4500.50,
  "max_loss": -1800.75,
  "mode": "at_expiry",
  "summary": {
    "total_positions": 10,
    "options_count": 8,
    "linear_count": 2,
    "total_delta": 0.5234,
    "total_theta": -123.45
  },
  "expiry_payoffs": {
    "19DEC25": {
      "current_pnl": 1000.00,
      "max_profit": 2000.00,
      "max_loss": -500.00
    }
  }
}
```

### Trade Log

#### GET `/api/v1/trade-log`
Получить историю сделок.

**Query Parameters:**
- `start_date` (optional): YYYY-MM-DD
- `end_date` (optional): YYYY-MM-DD
- `symbol` (optional): Фильтр по символу
- `side` (optional): "Buy" или "Sell"
- `limit` (default: 100): Количество записей
- `offset` (default: 0): Смещение для pagination

**Response:**
```json
[
  {
    "timestamp": "2025-12-18T10:30:00Z",
    "symbol": "BTC-19DEC25-100000-C-USDT",
    "side": "Buy",
    "size": 1.5,
    "price": 1245.0,
    "fee": 1.87,
    "role": "Taker",
    "iv": 0.65,
    "pnl": 83.25
  }
]
```

### Export

#### GET `/api/v1/export`
Экспортировать портфель в различных форматах.

**Query Parameters:**
- `format` (default: "json"): "json", "md" или "csv"

**Response:**
- JSON: Полный объект портфеля
- Markdown: Отформатированный отчет
- CSV: Таблица позиций

---

## WebSocket

### Подключение

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/portfolio');

ws.onopen = () => {
  console.log('Connected');
  ws.send(JSON.stringify({
    type: 'subscribe',
    channels: ['portfolio_update', 'options_board_update', 'trade_update']
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message);
};
```

### Message Types

#### connection_established
```json
{
  "type": "connection_established",
  "timestamp": "2025-12-19T13:28:00Z",
  "data": {
    "client_id": "abc123",
    "message": "Connected to portfolio updates"
  }
}
```

#### portfolio_update
```json
{
  "type": "portfolio_update",
  "timestamp": "2025-12-19T13:28:05Z",
  "data": {
    "timestamp": "2025-12-19T13:28:05Z",
    "margin": {...},
    "coin_risks": {...},
    "total_vega_usd": 4567.89,
    "total_theta_usd": -123.45,
    "warnings": []
  }
}
```

#### trade_update
```json
{
  "type": "trade_update",
  "timestamp": "2025-12-19T13:28:10Z",
  "data": [
    {
      "timestamp": "2025-12-19T13:28:09Z",
      "symbol": "BTC-19DEC25-100000-C-USDT",
      "side": "Buy",
      "size": 1.5,
      "price": 1245.0
    }
  ]
}
```

---

## Кэширование

### Frontend API Caching

API клиент автоматически кэширует responses с следующие TTL:

```typescript
// src/services/api.ts

// Portfolio data: 10 seconds
getPortfolio() → cache TTL: 10s

// Options board: 30 seconds
getOptionsBoard() → cache TTL: 30s

// Payoff chart: 30 seconds
getPayoffChart() → cache TTL: 30s

// Trade log: 60 seconds
getTradeLog() → cache TTL: 60s

// Metrics: 5 seconds
getMetrics() → cache TTL: 5s
```

### Управление кэшем

```typescript
// Очистить кэш для конкретного endpoint
apiClient.clearCacheFor('portfolio');

// Очистить весь кэш
apiClient.clearAllCache();

// Отключить кэширование
const response = await apiClient.getPortfolio(); // Берет из кэша
const uncached = await apiClient.request('/api/v1/risk/portfolio'); // Без кэша
```

---

## Обработка ошибок

### Frontend Error Handling

```typescript
// API errors с retry логикой
try {
  const data = await apiClient.getPortfolio();
} catch (error) {
  if (error instanceof ApiError) {
    console.error('API Error:', error.status, error.message);
  }
}

// WebSocket reconnection
const ws = new WebSocketClient();
ws.connect(); // Auto-reconnects with exponential backoff
```

### Backend Error Responses

```json
{
  "detail": "Failed to fetch positions: Connection timeout",
  "status": 503
}
```

HTTP Status Codes:
- `200`: Success
- `400`: Bad Request (invalid parameters)
- `404`: Not Found
- `500`: Server Error
- `503`: Service Unavailable (connector not ready)

---

## Развертывание

### Development

```bash
# Backend
uvicorn bybit_options.api.app:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd frontend && npm run dev
```

### Production

#### Using Docker Compose

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

#### Manual Production Build

```bash
# Frontend build
cd frontend
npm run build
npm install -g serve
serve -s dist -l 3001

# Backend with gunicorn
pip install gunicorn
gunicorn bybit_options.api.app:app -w 4 -b 0.0.0.0:8000
```

#### Using Nginx Reverse Proxy

```nginx
upstream backend {
    server backend:8000;
}

upstream frontend {
    server frontend:3001;
}

server {
    listen 80;
    server_name options-risk.example.com;

    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # API
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

### Environment Variables (Production)

```bash
# Backend
BYBIT_API_KEY=production_key
BYBIT_API_SECRET=production_secret
LOG_LEVEL=WARNING
DATABASE_URL=postgresql://user:pass@host:5432/db
API_AUTH_TOKEN=strong_token_value
CORS_ALLOW_ORIGINS=https://app.example.com

# Frontend
VITE_API_URL=https://api.example.com
NODE_ENV=production
```

---

## Чек-лист обновления API (перед продом)

- CI: Убедиться, что прошли `ruff check .` и `pytest --maxfail=1 --disable-warnings` (см. GitHub Actions workflow).
- Auth: Установить `API_AUTH_TOKEN` и требовать `Authorization: Bearer ...` на всех REST endpoints.
- CORS: Настроить `CORS_ALLOW_ORIGINS` (без `*` в проде), сверить с доменом фронтенда.
- Логи/секреты: `LOG_LEVEL=INFO/ WARNING`, проверить, что `.env` не в репозитории и ключи не логируются.
- Документация: Обновить `/docs` и этот файл при изменении контрактов (новые параметры/форматы).
- Деплой: Прогнать миграции БД (если есть), перезапустить backend/gunicorn, прогреть кэш при необходимости.

---

## Мониторинг

### Health Checks

```bash
# Backend health
curl http://localhost:8000/

# Frontend health (after build)
curl http://localhost:3001/

# API documentation
open http://localhost:8000/docs
```

### Logging

```python
# Backend logs with DEBUG level
LOG_LEVEL=DEBUG uvicorn bybit_options.api.app:app --reload
```

### Performance Metrics

- Backend response time: < 2 seconds for portfolio analysis
- WebSocket latency: < 500ms
- Frontend bundle size: < 500KB
- Cache hit rate: > 80% for stable queries

---

## Troubleshooting

### Frontend not connecting to Backend

1. Check if backend is running: `curl http://localhost:8000/`
2. Verify API URL in `frontend/src/services/api.ts`
3. Check browser console for CORS errors
4. Ensure CORS is configured in `bybit_options/api/app.py`

### WebSocket disconnections

1. Check if port 8000 is open and accessible
2. Verify WebSocket proxy in `frontend/vite.config.ts`
3. Check backend logs for connection errors
4. Frontend will auto-reconnect with exponential backoff

### High API latency

1. Check Bybit API rate limits
2. Monitor backend CPU and memory usage
3. Check Redis connection for caching
4. Reduce `price_range_pct` in payoff calculations

---

## API Version History

- **v1.0.0** (Current)
  - REST API endpoints for portfolio, positions, options
  - WebSocket real-time updates
  - Payoff chart calculations
  - Data export (JSON, MD, CSV)

---

## Ссылки

- [Backend API Documentation](http://localhost:8000/docs)
- [Frontend README](frontend/README.md)
- [Deployment Guide](docker-compose.yml)
- [Risk Engine Details](WEB_INTERFACE_IMPLEMENTATION_PLAN.md)
