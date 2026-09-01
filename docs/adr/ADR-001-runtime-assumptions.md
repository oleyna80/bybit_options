# ADR-001: Runtime and Deployment Assumptions

Status: Accepted
Date: TBD

## Context
The project is currently used as a local developer tool (CLI + optional API) and is not yet deployed to production.

## Decision
- Default runtime is local dev first (venv + python).
- CLI entry is the primary interface; API is optional for frontend integration.
- Uvicorn runs the API locally when needed.
- Docker Compose is optional and not required for core development.

## Consequences
- Local setup stays simple and fast.
- Deployment concerns (auth, scaling, infra) remain out of scope for now.
- Production requirements will require a follow-up ADR.
