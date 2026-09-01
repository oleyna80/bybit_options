# SDLC-MIGRATION-001 — Controlled adoption of Agentic SDLC Framework

## Status

Approved by Owner for local implementation on 2026-09-01. Remote publication is explicitly out of scope until branch reconciliation and a later Owner approval.

## Intent

Adopt the stable Agentic SDLC Framework control plane from
`oleyna80/agentic-sdlc-framework` at immutable commit
`be988807c38543eb90a728fcb4349bc97dd5695a`, while preserving the Bybit Options
product source, tests, deployment material, and durable project documentation.

## Installation decision

- Profile: `core` (minimal, provider-neutral).
- Active execution runtime: Codex in the current session.
- No project-local provider-specific runtime adapter is installed by this Work
  Block.
- No MCP/plugin/integration is admitted or activated.

## Requirements

- REQ-001: Install the framework's stable `core` control-plane artifacts with
  recorded source provenance and a valid installation-profile state.
- REQ-002: Replace the legacy agent operating contract with a concise
  runtime-neutral contract, while retaining legacy material as non-authoritative
  project history.
- REQ-003: Establish a Controlled Work Block that limits migration writes to
  governance, framework control-plane, and migration documentation.
- REQ-004: Preserve application source, tests, runtime/deployment configuration,
  and historical project documents without functional changes.
- REQ-005: Produce structural validation and security/publication evidence that
  contains no secret values and records residual risks.

## Acceptance criteria

- AC-001 [req=REQ-001]: `.agent/bootstrap-profile.json` resolves to `core`,
  records the frozen source commit, and the framework profile validator passes.
- AC-002 [req=REQ-002]: `AGENTS.md`, `PROJECT_MAP.md`, and
  `FILE_REGISTRY.yml` identify the new authority order and explicitly classify
  legacy agent material as non-authoritative.
- AC-003 [req=REQ-003]: `.agent/active-work-block.json` names this Work Block,
  its write-set, and a fail-closed external/publication boundary.
- AC-004 [req=REQ-004]: No files under `bybit_options/`, `tests/`,
  `database_migrations/`, `migrations/`, `frontend/`, `docker-compose.yml`, or
  `Dockerfile.backend` are changed by this Work Block.
- AC-005 [req=REQ-005]: Traceability and installation-profile checks pass; a
  report records the secrets scan, whitespace debt, and the fact that no live
  Bybit/API actions, commit, push, merge, or deployment occurred.

## Explicit exclusions

- Product features, strategy logic, database/schema changes, dependency updates,
  and code formatting are excluded.
- Credential rotation, API-key generation, live trading, external service calls,
  deployment, GitHub push, and merge are excluded.
- Generated logs, backups, local databases, and raw secrets remain local and
  are not admitted to the migration branch.

## Risks and assumptions

- The preserved baseline intentionally retains legacy whitespace debt; correcting
  it would obscure the migration diff and requires a separate scoped task.
- Existing legacy `.agent/` and `agreements/` material is retained for history
  and referenced from the map, but may not override the new contract.
- The current Bybit API surface has known live-trading and authentication risks;
  they are documented security follow-up work, not silently changed here.
