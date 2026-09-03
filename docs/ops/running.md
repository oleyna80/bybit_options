# Runtime Configuration

> **Last verified:** 2026-01-17  
> **Status:** ACTIVE  
> **Owner:** Tech Lead

---

## Services Overview

| Service | Port | Entry Point | Mode |
|---------|------|-------------|------|
| **Backend API** | 8000 | See below | REST + WS |
| **Frontend** | 3002 | `frontend/src/index.tsx` | React + Vite |
| **Delta Hedger** | — | `scripts/run_hedger.py` | Background |
| **WebSocket** | 8000 | `/ws/portfolio` | Real-time |

### Backend API Entry Points

| Type | Entry Point | Use Case |
|------|-------------|----------|
| **Demo/Dev** | `api_example.py` | Quick testing, backwards compat |
| **Production** | `bybit_options/api/app.py` | Production deployment |

> **SSOT:** For new development, use `bybit_options/api/app.py`.
> `api_example.py` is maintained for demo/backwards compatibility only.

---

## Start Commands

### Backend API (Risk Engine)

**Development (demo):**
```bash
cd /home/dmitrii/projects/bybit_options
source .venv/bin/activate
uvicorn api_example:app --reload --port 8000
```

**Production:**
```bash
cd /home/dmitrii/projects/bybit_options
source .venv/bin/activate
uvicorn bybit_options.api.app:app --host 0.0.0.0 --port 8000 --workers 4
```

### Frontend

```bash
cd /home/dmitrii/projects/bybit_options/frontend
npm run dev
# Opens on http://localhost:3002
```

### Delta Hedger Bot

```bash
cd /home/dmitrii/projects/bybit_options
source .venv/bin/activate
python scripts/run_hedger.py
# Or with dry-run: python scripts/run_hedger.py --dry-run
```

---

## Health Checks

| Service | Endpoint | Expected |
|---------|----------|----------|
| Backend API | `curl http://localhost:8000/` | `{"status": "ok"}` |
| Swagger Docs | `http://localhost:8000/docs` | OpenAPI UI |
| Frontend | `http://localhost:3002` | React app loads |
| Options Board API | `curl http://localhost:8000/api/v1/options-board` | JSON data |
| Portfolio API | `curl http://localhost:8000/api/v1/risk/portfolio` | JSON data |

---

## Environment Variables

Primary config file: `.env` (see `.env.example` for template)

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `BYBIT_API_KEY` | Bybit API key | `abc123...` |
| `BYBIT_API_SECRET` | Bybit API secret | `xyz789...` |
| `DATABASE_URL` | PostgreSQL connection | `postgresql://user:pass@localhost/db` |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `BYBIT_TESTNET` | `false` | Use testnet API |
| `VITE_API_URL` | `/api/v1` | Frontend API base URL |
| `HEDGER_ENABLED` | `false` | Enable Delta Hedger |
| `TELEGRAM_BOT_TOKEN` | — | Telegram alerts (optional) |
| `TELEGRAM_CHAT_ID` | — | Telegram chat ID (optional) |

---

## Database

### Connection

```bash
psql $DATABASE_URL
```

### Migrations

```bash
cd /home/dmitrii/projects/bybit_options
psql $DATABASE_URL -f database_migrations/003_create_hedger_tables.sql
psql $DATABASE_URL -f database_migrations/004_create_fractals_tables.sql
psql $DATABASE_URL -f database_migrations/005_add_option_config_fields.sql
```

---

## Ports Summary

| Port | Service | Protocol |
|------|---------|----------|
| 3002 | Frontend (Vite dev server) | HTTP |
| 8000 | Backend API (FastAPI) | HTTP/WS |
| 5432 | PostgreSQL (default) | TCP |

---

## Troubleshooting

### Port already in use

```bash
# Find process on port
lsof -ti:8000
# Kill it
kill $(lsof -ti:8000)
```

### Frontend can't reach backend

1. Check backend is running: `curl http://localhost:8000/`
2. Check Vite proxy config: `frontend/vite.config.ts`
3. Check browser Network tab for actual request URL

### Database connection failed

1. Check PostgreSQL is running: `pg_isready`
2. Verify `DATABASE_URL` in `.env`
3. Check migrations are applied

---

## See Also

- [Architecture Overview](../architecture.md)
- [Delta Hedger Tasklist](../tasklist/HEDGER.tasklist.md)
- [Frontend README](../../frontend/README.md)
