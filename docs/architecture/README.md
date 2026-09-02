# Architecture

Store accepted architecture decisions, system contracts, boundaries, and durable
technical design choices here when they apply beyond a single implementation task.

Keep feature requirements and acceptance criteria in `docs/specs/`; keep temporary
execution planning in `docs/plans/`.

## Source-of-truth boundary

- `docs/architecture/` is the canonical location for accepted architecture
  decisions/contracts under the current SDLC control plane.
- `docs/architecture.md` is a pre-migration architecture snapshot dated
  2026-01-17. It contains confirmed drift (for example the old frontend port,
  incomplete migration inventory, and legacy module layout) and must **not** be
  treated as current runtime truth without repository verification.
- Runtime ports, launch behavior, and environment assumptions belong in
  `docs/ops/running.md`, backed by current code/config.
- Repository structure/navigation is best resolved from current source plus
  `PROJECT_MAP.md`; historical structure documents are discovery aids only.

When an architecture fact cannot be confirmed from an accepted decision or the
current repository, record it as `UNKNOWN` rather than copying a historical claim
into this directory.

## Known documentation gap

`governance/README.md` currently links to
`docs/architecture/decisions/2026-07-25-runtime-neutral-control-plane.md`, but that
path does not exist on the reviewed `main` baseline. The intended ADR target is
`UNKNOWN`; do not invent a replacement link.
