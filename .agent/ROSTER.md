# Agent Routing Roster

> Maps logical SDLC roles to authority, responsibilities, and portable skills.
> Runtime-specific agent names, models, plugins, judges, and launch commands
> belong in adapters or Work Block evidence. They do not create governance roles.

## Core Logical Roles

| Role | Responsibility | Default authority | Core skills |
|---|---|---|---|
| Orchestrator | Frame Work Blocks, select profiles/evaluation posture, manage scope, route functions, consolidate evidence, enforce gates, close out | Workflow artifacts and approved coordination paths | task-decomposition, spec-consistency-analysis, ssot-sync-closeout, memory-bank-manager, subagent-mission-brief, orchestrator-log |
| Architect | Discover constraints, draft/refine specifications, propose architecture and implementation/evaluation plans | Read-only by default; approved draft paths | architecture-discovery, technical-discovery, requirements-clarification, project-estimation |
| Critic | Challenge scope, assumptions, risk, routing, Define-quality evidence, verification, and evaluation design before implementation | Read-only; critic report path only | critic-review |
| Coder | Implement the approved plan inside one explicit write-set | Approved source write-set only | scoped-coder, scoped-commit-guard, shell-context-guard, systematic-debugging |
| Reviewer | Review written requirements or the frozen implementation subject, according to specialization | Read-only; approved review report only | requirements-quality-review, reviewer, security-audit-triage |
| Verifier | Test acceptance criteria and synthesize deterministic/output/trajectory evidence | Read-only for source/runtime; verification/evaluation artifacts only | verifier, webapp-testing, security-verification-gate |

## Temporary Specializations

Specializations narrow focus but never expand authority. Examples:

- Architecture Analyst
- Product Analyst
- **Requirements Reviewer** — evaluates completeness, clarity, consistency,
  measurability, scenario coverage, assumptions, and traceability before Execute
- **Consistency Analyzer** — compares specification, accepted architecture/plan,
  tasks, dependencies, and write-set before Critic
- Frontend Reviewer
- Backend Coder
- Security Reviewer
- QA Verifier
- **Evaluator** — executes an approved output/trajectory evaluation plan
- Documentation Analyst
- Release Analyst
- Specification Drift Auditor

Requirements Reviewer is a read-only Reviewer specialization. Consistency
Analyzer is a read-only analysis specialization routed by the Orchestrator. Both
may write only approved evidence/report paths, cannot edit implementation source,
and cannot open the source write gate.

Evaluator is normally a read-only Verifier specialization. It may write only
approved evaluation plans/reports/events or other evidence paths. It cannot edit
implementation source, approve product scope, waive deterministic failures, open
authority/integration/deployment gates, or request hidden reasoning/private
chain-of-thought.

A drift audit is normally a read-only Reviewer or Verifier specialization using
`spec-drift-audit`. Add a permanent role only when the project requires a distinct
authority model.

## Runtime Binding

The active Work Block records how each logical function executes:

```yaml
function: requirements_quality_review
logical_role: reviewer
specialization: requirements_reviewer
runtime: codex
model_class: assurance
isolation: separate-subagent
authority: read-only-evidence
specification: docs/specs/feature-x.md
```

Valid runtimes are project-defined. Model or judge names must not be used as role
names. Requirements-quality, consistency, evaluation plans, and event-source
availability do not grant write authority.

## Isolation Levels

From weakest to strongest:

1. `same-context`
2. `separate-subagent`
3. `separate-session`
4. `separate-worktree`
5. `separate-runtime`
6. `independent-readonly-root`
7. `os-isolated`

The Work Block chooses the minimum sufficient level and records the actual
boundary. Different model names in one context do not establish independence.
Trajectory evaluation also records the actual observable-event source.

## Core Skill and Contract Routing

| Skill / contract | Route when |
|---|---|
| `architecture-discovery` | Architecture or subsystem boundary is unclear |
| `technical-discovery` | Repository structure/dependencies need inspection |
| `requirements-clarification` | Material specification ambiguity must be resolved before technical planning |
| `requirements-quality-review` | Formal specification needs read-only quality review before Critic/write gate |
| `task-decomposition` | A goal needs bounded Work Blocks/write-sets and optional REQ/AC/TASK traceability |
| `scripts/validate-define-traceability.py` | Formal stable-ID requirement/acceptance/task structure must be checked |
| `spec-consistency-analysis` | Specification, plan, tasks, dependencies, and write-set need read-only pre-execution alignment checking |
| `project-estimation` | Scope, risk, dependencies, verification/evaluation cost need classification |
| `critic-review` | Define-stage decisions require independent challenge after required Define-quality checks |
| `scoped-coder` | Approved file-changing implementation work |
| `reviewer` | Frozen diff requires independent implementation review |
| `verifier` | Acceptance criteria or technical contracts require evidence |
| `governance/evaluation.md` + `validate-evaluation.py` | Output or observable trajectory evaluation is required |
| `spec-drift-audit` | Spec, decisions, plans, code, tests/evals, and docs need post-implementation alignment checking |
| `systematic-debugging` | Root cause must be established before a fix |
| `ssot-sync-closeout` | Closeout must synchronize normative/derived artifacts |
| `merge-protocol` | Parallel results require consolidation/conflict handling |
| `subagent-mission-brief` | Work is delegated to another agent/session/runtime/team |
| `context-snapshot` | State must be frozen before parallel work/stage transition |
| `scoped-commit-guard` | Staging/commit scope must be protected |
| `shell-context-guard` | Shell location/target/side effects need explicit checking |
| `skill-library-maintenance` | GitHub source checks and safe skill adaptation |

## Define-Quality Routing Rules

For formal Managed/Assured/Distributed feature work:

1. draft the specification from Owner objective and authoritative evidence;
2. run `requirements-clarification` for material ambiguity;
3. run read-only `requirements-quality-review`;
4. produce architecture/implementation plan;
5. run `task-decomposition` with stable `REQ-*`/`AC-*`/`TASK-*` traceability where required;
6. run `scripts/validate-define-traceability.py` for structural coverage;
7. run read-only `spec-consistency-analysis`;
8. run Critic;
9. open the source write gate only when all applicable gates and Work Block authority permit it.

Resolve repository/discovery facts from evidence instead of asking the Owner.
Record reasonable non-material defaults as assumptions. Batch independent
material questions when safe and ask dependent questions sequentially. Missing
blocking decisions remain `BLOCKED`; a question budget is never permission to
guess.

Requirements-quality/consistency verdicts and structural validation are evidence.
They do not replace the approved specification, Critic, source Write Gate,
Reviewer, Verifier, evaluation, drift audit, or Hard Stops.

## Evaluation Routing Rules

Route evaluation when any condition applies:

- materially non-deterministic output;
- autonomous tool or path selection;
- trajectory compliance is an acceptance condition;
- consequential automation depends on process evidence;
- benchmark/dataset/rubric/LM judge is part of acceptance;
- Managed/Assured/Distributed profile requires it by risk.

Route deterministic criteria to code/rule checks. Route non-deterministic output
criteria to a human, rule-based evaluator, or approved LM judge. Route trajectory
criteria only when observable event sources exist. Missing event sources produce
`BLOCKED`/`UNVERIFIED`, never inferred pass.

## Domain Skill Routing

Domain skills are selected only when relevant. Catalog visibility does not grant
tool, file, runtime, data, deploy, evaluation, or Hard Stop authority.

Examples:

- frontend/design skills for UI work;
- security triage/hardening for security-sensitive work;
- MCP/handoff skills for integrations;
- media production skills for video/motion assets.

## Routing Priority

1. Owner instruction, authority, Hard Stops.
2. Approved specification and architecture decisions.
3. Work Block scope, write-set, risk, evaluation posture, isolation.
4. Clarification and requirements-quality review when required.
5. Task traceability and read-only pre-execution consistency analysis when required.
6. Critic gate.
7. Coder implementation and observable event capture.
8. Independent implementation Reviewer.
9. Verifier deterministic evidence.
10. Evaluator output/trajectory evidence when required.
11. Specification Drift Audit when triggered.
12. Consolidation and closeout.

## Degraded Execution

When a required capability or event source is unavailable:

1. preserve the logical function;
2. choose the strongest approved fallback;
3. record actual runtime, isolation, event source, and limitation;
4. label the result degraded, blocked, or unverified as applicable;
5. never upgrade a verdict because a preferred agent/model/judge was unavailable.