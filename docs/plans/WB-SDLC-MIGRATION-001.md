# WB-SDLC-MIGRATION-001 — Controlled framework migration

## State

Define — in progress. Owner authorized local migration and preservation branch
creation; commit/push/merge/deployment remain separate approval gates.

## Frozen inputs

- Subject branch: `migration-wb-sdlc-migration-001`
- Subject baseline: `6fe1dac1440e313e175cff385d7e8b190e801d15`
- Framework source: `oleyna80/agentic-sdlc-framework`
- Framework source commit: `be988807c38543eb90a728fcb4349bc97dd5695a`
- Installation profile: `core`

## Approved write-set

`.gitignore`, `AGENTS.md`, `PROJECT_MAP.md`, `FILE_REGISTRY.yml`, `.agent/**`,
`governance/**`, `runtimes/**`, `integrations/**`, `docs/session-bootstrap.md`,
`docs/specs/**`, `docs/plans/**`, `docs/tasklist/**`, `docs/reports/**`,
`docs/architecture/README.md`, `docs/engineering-memory/**`, `docs/evals/**`,
`docs/templates/**`, and framework validator scripts under `scripts/`.

## Execution sequence

1. Materialize the framework `core` artifacts from the frozen source and adapt
   only project placeholders/authority links.
2. Add this Work Block state and project navigation/registry entries.
3. Run requirements-quality, traceability, installation-profile, and
   source-boundary checks.
4. Review the migration diff and create a local evidence report.
5. Stop for Owner review of branches and merge approach before any commit or
   remote publication.

## Stop conditions

Stop for Owner direction if the migration requires product-code changes,
dependency/configuration changes, secret handling, a live API call, or a change
outside the write-set.
