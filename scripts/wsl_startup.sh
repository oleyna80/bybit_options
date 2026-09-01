#!/usr/bin/env bash
set -euo pipefail

LOCK_FILE="/tmp/bybit_options_wsl_startup.lock"

if [ -e "$LOCK_FILE" ]; then
  echo "Startup already running (lock exists): $LOCK_FILE"
  exit 0
fi

cleanup() {
  rm -f "$LOCK_FILE"
}

trap cleanup EXIT
touch "$LOCK_FILE"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${ROOT_DIR}/.venv/bin/python"
if [ -f "${ROOT_DIR}/.venv/bin/activate" ]; then
  # shellcheck disable=SC1090
  source "${ROOT_DIR}/.venv/bin/activate"
  PYTHON_BIN="${ROOT_DIR}/.venv/bin/python"
elif [ ! -x "$PYTHON_BIN" ]; then
  PYTHON_BIN="python3"
fi

echo "Using python: ${PYTHON_BIN}"

TRADES_COUNT="$($PYTHON_BIN -c $'import asyncio\nfrom sqlalchemy import text\nfrom database import async_engine\nasync def main():\n    async with async_engine.connect() as conn:\n        result = await conn.execute(text("SELECT COUNT(1) FROM trades"))\n        print(result.scalar() or 0)\nasyncio.run(main())')"

if [ "${TRADES_COUNT}" -eq 0 ]; then
  echo "Trades table empty; running backfill."
  "$PYTHON_BIN" scripts/sync_trades.py --backfill --days 180 --category option
fi

echo "Running incremental trade sync."
"$PYTHON_BIN" scripts/sync_trades.py --category option

start_portfolio_snapshots() {
  if command -v systemctl >/dev/null 2>&1; then
    if systemctl --user is-system-running >/dev/null 2>&1; then
      if systemctl --user start bybit-portfolio-snapshot.timer >/dev/null 2>&1; then
        echo "Started systemd timer: bybit-portfolio-snapshot.timer"
        return 0
      fi
    fi
  fi

  echo "Systemd user not available; starting background snapshot loop."
  mkdir -p logs
  nohup "$PYTHON_BIN" scripts/sync_portfolio.py >> logs/portfolio_syncer.log 2>&1 &
  echo "Portfolio snapshot loop running in background (logs/portfolio_syncer.log)."
}

start_portfolio_snapshots
