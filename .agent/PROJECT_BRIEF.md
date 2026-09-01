# Project Brief — Bybit Options Risk Engine / Platform

## What this is

Async backend service for analyzing Bybit options portfolio risk (Greeks, risk metrics, Markdown reports, and API for frontend).

## Current scope (near-term)

- Reliable ingestion of positions + market data (Bybit V5)
- Deterministic risk calculation (pure RiskEngine)
- Portfolio summaries and warnings
- Outputs: Markdown reports + API for frontend

## Key architecture rules (must follow)

- RiskEngine is pure (no I/O)
- All I/O is async and goes via BybitConnector / MarketDataService
- Use Pydantic models for public boundaries

## Primary entry points

- CLI: main.py
- API example: api_example.py

## Frontend

React (Vite) in `frontend/`, talks to `http://localhost:8000/api/v1`

## Non-goals (for now)

- Landing/affiliate content
- Execution/trading automation beyond analysis
