# WB-DOCS-001 — Legacy Agent Layer Reconciliation

Status: EXECUTED / AWAITING ASSURANCE AND OWNER MERGE APPROVAL
Date: 2026-09-02
Scope: agent/governance documentation metadata only

## Objective

Reconcile the pre-migration agent documentation with the runtime-neutral Agentic SDLC control plane without deleting historical product knowledge or changing production/runtime behavior.

The current control-plane baseline is defined by `AGENTS.md`, `PROJECT_MAP.md`, `FILE_REGISTRY.yml`, `governance/**`, `.agent/ROSTER.md`, `.agent/workflows/sdd-protocol.md`, and `.agent/bootstrap-profile.json`.

The bootstrap profile records the `core` installation from `oleyna80/agentic-sdlc-framework` at framework commit `be988807c38543eb90a728fcb4349bc97dd5695a` and classifies retained migration material as non-authoritative context.

## Classification rules

- `CURRENT`: active control-plane/runtime surface; preserve as current authority or routing evidence according to `FILE_REGISTRY.yml`.
- `MIGRATE_KNOWLEDGE`: contains potentially reusable product/architecture/domain knowledge; do not delete before engineering truth reconstruction.
- `HISTORICAL`: useful recovery/provenance evidence but not current authority.
- `REMOVE_CANDIDATE`: predominantly superseded process/runtime instructions; removal still requires reference/evidence review and Owner-approved deletion scope.
- `SEPARATE_GATE`: requires a dedicated decision because it contains sensitive/generated account data or another materially different risk.

## Migration matrix

| Surface | Classification | Evidence / reason | Next action |
| --- | --- | --- | --- |
| `AGENTS.md` | CURRENT | Portable project operating contract installed by current framework migration | Keep |
| `PROJECT_MAP.md` | CURRENT | Human-readable authority/navigation map | Keep; narrow legacy wording |
| `FILE_REGISTRY.yml` | CURRENT | Machine-readable authority/navigation registry | Keep; distinguish selected skills from legacy flat files |
| `governance/**` | CURRENT | Runtime-neutral governance core | Keep |
| `.agent/ROSTER.md` | CURRENT | Current logical roles and routing | Keep |
| `.agent/workflows/sdd-protocol.md` | CURRENT | Canonical Define -> Execute -> Assure -> Close workflow | Keep |
| `.agent/bootstrap-profile.json` | CURRENT / generated evidence | Exact installed profile, paths, skills, provenance | Keep |
| `.agent/hooks/**` | CURRENT runtime adapter | Current consequential-action guard implementation | Keep; code changes are outside this Work Block |
| bootstrap-selected `.agent/skills/<skill>/SKILL.md` | CURRENT runtime adapter | Explicitly selected by bootstrap profile | Keep |
| `.agent/PROJECT_BRIEF.md` | MIGRATE_KNOWLEDGE | Contains product scope and architecture invariants but stale entrypoint/non-goal claims | Reconcile during engineering truth reconstruction, then archive/remove candidate |
| `.agent/conventions.md` | MIGRATE_KNOWLEDGE | Contains useful async, RiskEngine, Pydantic, logging and service-boundary rules mixed with historical assumptions | Reconcile into architecture/engineering memory |
| `.agent/workflows/bybit_options_workflow.md` | MIGRATE_KNOWLEDGE | Contains backend/service flow knowledge but stale runtime references | Use as discovery evidence, then archive/remove candidate |
| `.agent/roles/trading-expert.md` | MIGRATE_KNOWLEDGE / HIGH-RISK LEGACY | Contains domain rules plus obsolete instructions that can initiate data fetch/live trading actions | Extract only verified domain knowledge; do not migrate permissions |
| other `.agent/roles/**` | REMOVE_CANDIDATE | Superseded permanent-role topology conflicts with current runtime-neutral roster | Preserve until reference review, then delete/archive in dedicated scope |
| `.agent/rules/000-sdd-enforcer.md` | REMOVE_CANDIDATE | Defines a separate pre-migration SDD authority model and old role/memory preflight | Remove/archive after reference review |
| project-local flat `.agent/skills/*.md` not selected by bootstrap profile | MIGRATE_KNOWLEDGE or REMOVE_CANDIDATE | Not canonical installed skills; some contain project/domain knowledge | Classify individually before deletion |
| `agreements/00-routing.md` | REMOVE_CANDIDATE | Old intent routing, roles, gates and stale SSOT paths | Remove/archive after reference review |
| `agreements/10-model-routing.md` | REMOVE_CANDIDATE | Time-sensitive model catalog and mandatory Task-Auto/model-pause protocol | Remove/archive after reference review |
| `agreements/11-auto-context.md` | REMOVE_CANDIDATE | IDE-specific pre-migration context policy, no longer authority | Remove/archive after reference review |
| `agreements/20-permissions.md` | REMOVE_CANDIDATE | Old TASK-ID/Task-Auto permission model conflicts with Work Block authority | Remove/archive after reference review |
| `.clinerules` | REMOVE_CANDIDATE | Stale December 2025 project/runtime snapshot and provider-specific instructions | Remove after any still-useful product facts are reconciled |
| `readme_md.md` | REMOVE_CANDIDATE | Historical README with stale runtime/production claims | Preserve until engineering docs reconstruction, then remove/archive |
| `.memory_bank/**` | HISTORICAL / MIGRATE_KNOWLEDGE | Contains implementation chronology, decisions and recovery evidence; current status is stale | Preserve through engineering truth reconstruction; migrate verified durable knowledge later |
| `Claude对话_2025-12-11.md` | HISTORICAL / MIGRATE_KNOWLEDGE | Raw AI conversation contains WebSocket design history but is not normative documentation | Preserve until related implementation is reconciled; extract verified decisions only |
| historical root/review reports | HISTORICAL | Point-in-time evidence; completion claims are not automatically current | Preserve with evidence-lifetime semantics |
| `reports/risk_analysis_2025-12-26_16-51-43.md` | SEPARATE_GATE | Generated report contains account/portfolio-specific data | Do not reproduce values; handle deletion from current tree in a dedicated sensitive-artifact scope |

## Confirmed governance corrections in this Work Block

1. `PROJECT_MAP.md` no longer classifies all `.agent/**` material as legacy. It now names the actual retained legacy surfaces and preserves current status for `ROSTER`, `sdd-protocol`, selected skills, Work Block state, and hooks.
2. `.agent/skills/README.md` now defines bootstrap-selected folder-form `SKILL.md` files as canonical and explicitly treats unselected flat project-local skill files as historical context.
3. `FILE_REGISTRY.yml` is to distinguish canonical selected skills from retained flat legacy skill files instead of assigning one current classification to the entire `.agent/skills/**` tree.

## Intentionally not changed

- Production Python/TypeScript source.
- Tests, dependencies, CI, Docker/Compose configuration.
- Database migrations or database state.
- Runtime hooks or safety code.
- `AGENTS.md` and governance contracts.
- Product/architecture claims in legacy files pending engineering truth reconstruction.
- `.memory_bank/**` and trading/domain knowledge.
- Historical reports/transcripts.
- Sensitive/generated account artefacts.
- Local dirty working tree and local `master`.

## Deletion policy for follow-up work

No historical file should be deleted merely because it is old or non-authoritative. Removal requires evidence that:

1. any still-valid product/architecture/domain knowledge has been reconciled into a current SSOT or durable engineering memory;
2. current control-plane files no longer reference the legacy surface as operational authority;
3. the deletion does not discard the only available recovery provenance for local uncommitted work;
4. sensitive/generated data is handled under an appropriately narrow separate gate.

## Remaining blockers / UNKNOWN

- Exact alignment of legacy product claims with the large local dirty backend/frontend/storage tree remains UNKNOWN until Engineering Truth Reconstruction.
- Individual trading flat skills may contain unique reusable domain knowledge and therefore are not bulk-delete candidates.
- Current applicability of `.memory_bank/progress.md` claims is UNKNOWN until code/tests are mapped to capabilities.
- Sensitive generated report removal from Git history is explicitly out of scope; current-tree deletion is a separate Owner gate.
- Existing PR #1 mixes legacy deletion with executable hook changes and should not be used as the implementation vehicle for this reconciliation.
- Existing PR #3 remains separate audit evidence and is not expanded by this Work Block.

## Closeout posture

This Work Block only normalizes authority/navigation metadata and records the migration plan. It does not complete engineering documentation recovery and does not authorize deletion, merge, deployment, database mutation, secret access, or live trading.
