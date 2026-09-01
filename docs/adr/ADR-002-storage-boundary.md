# ADR-002: Storage Boundary and Placeholder Choice

Status: Accepted
Date: TBD

## Context
Some workflows require persistence (trade history, snapshots, reports). The current code uses ad-hoc DB helpers, but the long-term storage choice is not finalized.

## Decision
- Define a storage interface boundary in bybit_options.storage.repositories.
- Implement a thin adapter around existing database.py/trade_history.py.
- The concrete storage engine remains TBD (PostgreSQL vs SQLite vs file-based).

## Consequences
- Core code depends on interfaces, not concrete storage.
- Storage implementation can change later without touching domain logic.
- A future ADR will finalize the storage engine.
