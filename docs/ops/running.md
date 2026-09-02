# Runtime Configuration

> **Verified against `main`:** 2026-09-02 (`e46a944383111a79336b15544436f2e97de2c862`)  
> **Status:** CURRENT REPOSITORY SNAPSHOT  
> **Owner:** Tech Lead

This document describes repository-observable runtime facts. It is not authority
to start live trading, mutate a live database, deploy production, or use
production credentials. Those actions remain Hard Stops under `AGENTS.md` and
`governance/authority.md`.

## Safety boundary

- Treat backend/hedger startup as **network-capable**, not as a harmless smoke
  check, whenever real credentials are present.
- `bybit_options/api/app.py` currently creates `BybitConnector(...,
  testnet=False)` during application lifespan. `BYBIT_TESTNET` therefore does
  **not** make this API entry point testnet-safe today.
- `python scripts/run_hedger.py --dry-run` is **not an offline/no-side-effect
  verifier**: the script loads credentials, requires `DATABASE_URL`, creates a DB
  pool and connector, and starts/stops the bot task before exit.
- Do not apply SQL migrations from a documentation recipe. Migration ordering,
  target environment, backup/rollback, and Owner approval must be established for
  the specific database first.
- Do not copy real credentials into documentation, chat, reports, or committed
  files.

## Verified services and ports

| Surface | Repository-observed port | Entry point / evidence | Notes |
|---|---:|---|---|
| Backend API | 8000 | `bybit_options/api/app.py` | Canonical app; network-capable |
| Docker backend | 8000 | `Dockerfile.backend` → `api_example:app` | `api_example.py` is a compatibility shim to the canonical app |
| Frontend dev server | 3001 | `frontend/vite.config.ts` | Vite binds `0.0.0.0:3001` |
| Frontend container | 3001 | `frontend/Dockerfile`, `docker-compose.yml` | `serve -s dist -l 3001` |
| WebSocket | 8000 | `/ws/portfolio` in FastAPI app | Same backend process |
| Delta Hedger | — | `scripts/run_hedger.py` | Background process; can reach exchange/DB |
| PostgreSQL / TimescaleDB | 5432 in Compose | `docker-compose.yml` | Local Compose mapping only |
| Redis | 6379 in Compose | `docker-compose.yml` | Local Compose mapping only |

The former `3002` frontend value found in older documentation is stale relative
to both `frontend/vite.config.ts` and current Docker configuration.

## Entry points

### CLI compatibility entry

```bash
python main.py
```

`main.py` is a thin compatibility shim to `apps.cli`. Whether the resulting CLI
performs network access depends on the called application path and available
environment configuration. Inspect the target code before using live
credentials.

### Backend API

Canonical application object:

```text
bybit_options.api.app:app
```

A common development launch shape is:

```bash
uvicorn bybit_options.api.app:app --reload --host 127.0.0.1 --port 8000
```

**Do not run this command as a generic verification step with production/live
Bybit credentials.** The current application hard-codes `testnet=False` when it
initializes the connector.

### Frontend

From `frontend/`:

```bash
npm run dev
```

Repository-observed URL:

```text
http://localhost:3001
```

The Vite proxy targets backend HTTP at `http://localhost:8000` and WebSocket at
`ws://localhost:8000`.

### Delta Hedger

Entry point:

```text
scripts/run_hedger.py
```

This is a trading-capable runtime surface. Do not start it against live
credentials without the required Owner/external capability approval. The current
`--dry-run` flag is initialization-and-exit behavior, not evidence of full
network/database isolation.

## Environment variables verified from current code

There is **no committed `.env.example` on `main`** as of the verification date.
Do not rely on older documentation that points to one.

### FastAPI application (`bybit_options/api/app.py`)

| Variable | Observed use |
|---|---|
| `BYBIT_API_KEY` | Required at lifespan startup |
| `BYBIT_API_SECRET` | Required at lifespan startup |
| `DATABASE_URL` | Required by imported `database.py`; missing value raises during import |
| `CORS_ALLOW_ORIGINS` | Optional; default `http://localhost:3001` |
| `API_AUTH_TOKEN` | Optional bearer-token enforcement |
| `ENABLE_DELTA_SERVICES` | Optional; default `false` |

`BYBIT_TESTNET` is **not honored by this FastAPI connector path** at present;
`testnet=False` is explicit in the code.

### Delta Hedger (`scripts/run_hedger.py`)

| Variable | Observed use |
|---|---|
| `BYBIT_API_KEY` | Required |
| `BYBIT_API_SECRET` | Required |
| `DATABASE_URL` | Required |
| `BYBIT_TESTNET` | Read by this script; default is `true` |

Other services may read additional variables. Treat undocumented variables as
`UNKNOWN` until verified in the relevant code/config surface.

## Docker Compose notes

`docker-compose.yml` exposes backend `8000`, frontend `3001`, Redis `6379`, and
TimescaleDB `5432`.

The Compose file currently contains a development-looking database password and
connection string (`secure_password`). Treat these as repository configuration,
**not** as an approved production secret-management pattern. This review does not
change runtime configuration.

Running `docker compose up`, restarting services, or changing Compose state may
have external/runtime effects. Confirm the target environment and applicable
Hard Stops first.

## Database and migrations

Current repository migration inventory is broader than the old 003–005 recipe:
`database_migrations/` contains 001–010 and 012–014 on this baseline, and the
repository also contains `migrations/`.

Because the authoritative ordering/application procedure is not established by a
single verified migration runner in this documentation review, the correct
command to apply migrations is **UNKNOWN**. Do not infer that running individual
`psql -f` files is safe or complete.

Read-only connectivity checks may still reach a database and must use an approved
non-production target when environment separation matters.

## Health and verification

Safe static checks for documentation/runtime reconciliation include inspecting:

- `frontend/vite.config.ts` and `frontend/Dockerfile` for frontend port;
- `Dockerfile.backend` and `api_example.py` for container backend target;
- `bybit_options/api/app.py` for API startup/env behavior;
- `scripts/run_hedger.py` for hedger startup behavior;
- `database.py` for DB configuration requirements;
- `docker-compose.yml` for container port mappings.

HTTP `curl`, database connection, Bybit API calls, container startup, and hedger
startup are runtime checks, not static documentation checks. Their safety depends
on the target environment and credentials.

## See also

- [Architecture contracts](../architecture/README.md)
- [Session/bootstrap authority](../session-bootstrap.md)
- [Delta Hedger tasklist](../tasklist/HEDGER.tasklist.md)
- [Frontend README](../../frontend/README.md)
- [Project operating contract](../../AGENTS.md)
