# Project Map — Bybit Options

First human-readable map for `Bybit Options`. It explains authority, the
resolved installation profile, major repository zones, and what an agent should
read next.

## Architecture

`Bybit Options` uses a runtime-neutral Agentic SDLC control plane with four
separable layers:

1. **Governance Core** — authority, lifecycle, artifacts, Define-stage
   requirements quality/traceability, evaluation, risk gates, capability
   negotiation, assurance, and closeout.
2. **Portable workflow** — specifications, clarifications, requirements-quality
   reviews, decisions, Work Blocks, implementation/evaluation plans, traceable
   tasks, reports, skills, memory, and observable evidence.
3. **Runtime adapters** — Codex, Claude Code, OpenCode, generic, or another
   approved execution runtime.
4. **Integration adapters** — optional plugins, MCP servers, external runtime
   CLIs, hosted tools, and audited file transport.

Runtime, model, judge, integration, installation profile, requirements-quality
verdict, or traceability validator result never changes governance authority.

The product is a Python/FastAPI options-trading system with PostgreSQL-facing services and a JavaScript frontend. Primary source roots are `bybit_options/`, `tests/`, `frontend/`, `database_migrations/`, and `migrations/`.

Legacy material retained for recovery/discovery currently includes
`.agent/PROJECT_BRIEF.md`, `.agent/conventions.md`, `.agent/roles/**`,
`.agent/workflows/bybit_options_workflow.md`, project-local flat
`.agent/skills/*.md` files not selected by the bootstrap profile,
`agreements/**`, and `.memory_bank/**`. These surfaces are non-authoritative
after `SDLC-MIGRATION-001`; they may preserve product history that still needs
reconciliation. Current `.agent/ROSTER.md`, `.agent/workflows/sdd-protocol.md`,
bootstrap-selected folder-form skills, active Work Block state, and `.agent/hooks/**`
remain current control-plane/runtime surfaces as classified below.

## Installation Profile

Read `.agent/bootstrap-profile.json` first when runtime availability matters. It
records which runtime implementation surfaces and skills were installed. It is
installation evidence only and does not grant Work Block authority, integration
admission, credentials, side-effect permission, a passing requirements-quality
verdict, or a passing evaluation verdict.

Possible conditional surfaces:

- `.codex/` for Codex;
- `CLAUDE.md` and `.claude/` for Claude Code;
- `opencode.json` and `.opencode/` for OpenCode;
- `.mcp.json` as an inert MCP configuration surface.

Absence of an unselected runtime surface is expected.

## Authority Order

1. current Owner instruction or approved change request;
2. `AGENTS.md` and Governance Core;
3. approved specification and acceptance criteria;
4. accepted architecture decisions and external contracts;
5. approved implementation and evaluation plans and write-set;
6. active tasklist;
7. requirements-quality, consistency, review, verification, evaluation, drift,
   integration, and closeout evidence;
8. durable engineering memory;
9. runtime/integration policy, operational logs, generated output, references.

Requirements-quality reports, tasklists, validator output, scores, judges, and
logs are evidence or derived artifacts; they do not silently revise product
requirements or open authority gates.

## Work Block Profiles

Each Work Block selects independently:

- **Governance profile:** Advisory, Controlled, Managed, Assured, Distributed.
- **Runtime profile:** one installed or otherwise approved runtime adapter.
- **Integration profile:** none or an admitted bridge/tool/transport.
- **Model class:** task-appropriate capability class.
- **Isolation:** actual boundary from same context to OS-isolated.
- **Evaluation posture:** not required or an approved deterministic/output/trajectory plan.

The installation profile constrains local availability; it does not activate a
runtime, integration, requirements-quality, or evaluation authority.

## Define-Stage Requirements Quality

`governance/define-quality.md` strengthens Stage 0 for formal feature work:

```text
specification draft
  -> requirements clarification
  -> requirements-quality review
  -> architecture / implementation plan
  -> traceable task decomposition + write-set
  -> deterministic traceability validation
  -> read-only specification/plan/task consistency analysis
  -> Critic
  -> write gate READY
```

Clarification uses an evidence-first policy:

- repository/discovery-resolvable fact -> resolve from authoritative evidence;
- reasonable non-material default -> record as explicit assumption;
- material independent ambiguity -> ask in a small bounded batch;
- material dependent ambiguity -> ask sequentially;
- unresolved blocking ambiguity -> keep Define blocked.

Formal traceability uses stable identifiers:

```text
- REQ-001: Required behavior.
- AC-001 [req=REQ-001]: Measurable acceptance criterion.
- [ ] TASK-001 [type=requirement] [req=REQ-001] [ac=AC-001] [paths=src/a.py,tests/test_a.py] Implement behavior.
```

Enabling, assurance, and documentation tasks may use `req=-` and `ac=-` when they
do not directly implement a product requirement. Every task still declares an
explicit path/write-set. Do not create fake requirements to satisfy validation.

Use:

```text
skills: requirements-clarification, requirements-quality-review,
        task-decomposition, spec-consistency-analysis
docs/templates/requirements-quality-review-template.md
docs/templates/traceable-tasklist-template.md
scripts/validate-define-traceability.py
```

The validator checks structural coverage only. It cannot prove that the
requirements are correct, complete, secure, or valuable, and it never grants
source-write authority.

## Narrow Deterministic Repair

NDR is a constrained `Controlled` submode for deterministic, reversible
CI/bootstrap/runtime-validation repairs. It uses one repair record, one Coder
pass, deterministic checks, and one independent combined assurance report. It
permits one correction. Integration Stabilization may group at most three eligible
items and two correction rounds; both ceilings fail closed to an Owner decision.

## Evaluation Assurance

`governance/evaluation.md` distinguishes:

- deterministic tests for objective contracts;
- output evaluation against an approved rubric;
- observable trajectory evaluation for tool, gate, check, retry, side-effect,
  and evidence events.

Trajectory evidence never requires private chain-of-thought, hidden reasoning,
or model scratchpads. Missing events are blocked/unverified, not passed. An LM
judge cannot waive deterministic failures or open write/integration/deployment gates.

Use:

```text
docs/evals/<evaluation-id>/plan.json
docs/evals/<evaluation-id>/events.jsonl
docs/reports/evaluations/<evaluation-id>.json
scripts/validate-evaluation.py
```

## Key Paths

| Path | Status | Purpose |
|---|---|---|
| `AGENTS.md` | normative | Compact project operating contract |
| `.agent/bootstrap-profile.json` | generated | Resolved installation profile and path contract |
| `governance/` | normative | Runtime-neutral authority, lifecycle, artifacts, Define quality, evaluation, capabilities |
| `governance/define-quality.md` | normative | Clarification, requirements-quality review, traceability, pre-execution consistency |
| `governance/evaluation.md` | normative | Deterministic/output/observable trajectory contract |
| `.agent/workflows/sdd-protocol.md` | normative | Define / Execute / Assure / Close semantics |
| `.agent/ROSTER.md` | normative | Logical roles, skill routing, runtime binding, isolation |
| `.agent/active-work-block.json` | operational gate | Specification, write-set, integrations, assurance, closeout |
| `.agent/active-work-block.default.json` | portable default | Fail-closed restore state including optional PENDING evaluation |
| `.agent/verification-gate.md` | compatibility view | Review, verification, evaluation, drift, closeout summary |
| `.agent/hooks/` | shared runtime policy | Provider-neutral consequential-action guards |
| `.agent/skills/<selected-skill>/SKILL.md` | runtime adapter | Canonical portable skill selected by `.agent/bootstrap-profile.json`; flat legacy skill files are discovery context only |
| `docs/specs/` | normative | Approved product and technical behavior |
| `docs/architecture/` | normative | Accepted architecture decisions and contracts |
| `docs/plans/` | derived/log | Approved plans and Work Blocks |
| `docs/tasklist/` | derived | Active task decomposition with optional stable REQ/AC/TASK traceability |
| `docs/evals/` | evidence/config | Approved evaluation plans, fixtures, observable events |
| `docs/reports/evaluations/` | evidence | Evaluation matrices, gaps, risks, verdicts |
| `docs/reports/` | evidence | All assurance, integration, and closeout evidence |
| `docs/templates/requirements-quality-review-template.md` | normative template | Requirements-quality review contract |
| `docs/templates/traceable-tasklist-template.md` | normative template | Requirement/acceptance/task/write-set traceability |
| `docs/templates/` | normative templates | Work Block, evaluation, reports, integration admission |
| `docs/engineering-memory/` | durable reference | Evidence-backed reusable decisions |
| `memory_bank/` | operational/local | Current focus, progress, pending decisions, logs |
| `runtimes/` | adapter documentation | Capability, activation, limitation, fallback |
| `integrations/` | adapter documentation | Optional bridge/tool/transport admission |
| `integrations/repository-graph/README.md` | optional capability boundary | Provider-neutral local derived state; unadmitted and uninstalled |
| `docs/templates/repository-graph-opt-in-template.md` | normative template | Future Owner-approved local-state binding record |
| `scripts/bootstrap.sh` | health check | Validates profile/default and restores local state |
| `scripts/validate-installation-profile.py` | validator | Selected paths, kinds, absent surfaces, blocked default |
| `scripts/validate-define-traceability.py` | validator | Structural REQ/AC/TASK coverage and reference consistency |
| `scripts/validate-evaluation.py` | validator | Evaluation plan/report consistency and closeout binding |
| `scripts/repair-lifecycle.py` | validator | Fail-closed NDR record limit validation |
| `docs/templates/repair-record-template.md` | normative template | NDR scope, verification, and stop-condition record |
| `docs/templates/combined-assurance-report-template.md` | normative template | Independent NDR review and verification evidence |
| source/test directories | source | Controlled by approved Work Block write-sets |

## Safe Defaults

- no plugin, external bridge, MCP server, or watcher is enabled automatically;
- no provider-named authority agent is installed;
- external runtime calls require active integration approval;
- Repository Graph Provider state is local, derived, rebuildable, and
  non-authoritative; it is not installed or admitted by default;
- requirements-quality and consistency reports are evidence, not write authority;
- blocked default evaluation is optional, `PENDING`, unbound, and has no authority;
- credentials and private runtime state remain local;
- observable evidence must exclude secrets, protected payloads, and hidden reasoning.

## Core Lifecycle

```text
Define
  discovery -> specification -> clarification -> requirements quality -> architecture/plan
  -> traceable tasks -> consistency analysis -> critic

Execute
  scoped implementation -> self-check -> observable event capture -> frozen diff

Assure
  independent review -> technical verification -> agent evaluation -> drift audit

Close
  SSOT sync -> engineering memory -> closeout report
```

Required Define-stage quality checks must be resolved before the write gate can be
`READY` where the selected governance profile requires them. Required evaluation
must be `READY` for `success-closeout`. Optional evaluation may be skipped only
with a concrete reason.

## Generated, Derived, Evidence, and Local Boundaries

- specifications and accepted architecture decisions are normative;
- implementation/evaluation plans and tasklists are derived/configuration;
- requirements-quality, consistency, review, verification, evaluation, drift,
  and closeout reports are evidence, not requirement authority;
- `.agent/bootstrap-profile.json` is generated installation evidence;
- engineering memory is durable only when evidence-backed and secret-free;
- `memory_bank/**` and runtime memory are operational/local by default;
- provider auth, downloaded plugins, browser sessions, local IDE state, `.env*`,
  tokens, cookies, credentials, keys, and live customer data must not be committed.

## New-Session Read Strategy

Always for non-trivial work:

1. `AGENTS.md`;
2. `.agent/bootstrap-profile.json` when runtime availability matters;
3. active Work Block;
4. active specification and revision;
5. approved implementation/evaluation plans and active tasklist;
6. relevant architecture decisions;
7. repository status and current diff.

Read conditionally:

- relevant Governance Core contract, especially `define-quality.md` and `evaluation.md`;
- requirements-quality/consistency evidence required by the active Work Block;
- detailed SDLC protocol and role/skill roster;
- installed/approved runtime adapter;
- selected integration adapter and admission record;
- evaluation evidence required by the Work Block;
- relevant skills, engineering memory, and operational logs.

Do not treat an absent unselected runtime surface as corruption.

Update this map and `FILE_REGISTRY.yml` when installation composition, authority,
source-of-truth order, lifecycle, Define quality, evaluation, integration, gates,
adapters, or normative/evidence/local boundaries change.
