# SDLC Protocol — Runtime-Neutral Stage Contract

> Canonical generated-project lifecycle. It defines management functions,
> evidence, gates, and state transitions independently of the agent runtime.

## Core Principle

The lifecycle requires functions and artifacts, not a fixed number of agents.
One capable runtime may execute several functions for low-risk work. Higher-risk
work requires stronger independence as recorded in the active Work Block.

```text
Stage 0 — Define
Stage 1 — Execute
Stage 2 — Assure
Stage 3 — Close
```

## State Model

Stage execution state:

```text
blocked -> ready -> in_progress -> completed
   ^                              |
   +------------- retry ----------+
```

Track evidence, prerequisites, gates, and outcomes separately:

- **Requirements-quality result:** `READY | CHANGES_REQUIRED | BLOCKED | UNVERIFIED | SKIPPED`
- **Define consistency result:** `READY | CHANGES_REQUIRED | BLOCKED | UNVERIFIED | SKIPPED`
- **Define-quality prerequisite:** `PENDING | READY | BLOCKED` plus an applicability flag and evidence bindings
- **Write gate:** `READY | BLOCKED`
- **Critic gate:** `READY | BLOCKED | SKIPPED | DEGRADED`
- **Review gate:** `READY | CHANGES_REQUIRED | BLOCKED | UNVERIFIED | SKIPPED`
- **Verification verdict:** `READY | BLOCKED | UNVERIFIED`
- **Evaluation verdict:** `READY | BLOCKED | UNVERIFIED | NOT_REQUIRED`
- **Drift gate:** `READY | BLOCKED | UNVERIFIED | SKIPPED`
- **Closeout mode:** `success-closeout | reporting-only`

Requirements-quality and Define consistency are pre-execution evidence. The one
aggregate Define-quality prerequisite makes their applicable readiness
machine-observable without granting source-write authority. The Write Gate remains
the source-write control point and Critic remains a separate function.

Only all required gates in a passing state permit `success-closeout`.
`BLOCKED`, `UNVERIFIED`, or unresolved `CHANGES_REQUIRED` permits diagnostics,
corrective planning, evidence capture, and reporting-only closeout. It does not
permit merge-ready, deploy-ready, release-ready, or completed-task claims.

Evaluation is assurance evidence. It does not grant source-write authority,
integration admission, credentials, deployment permission, or a Hard Stop exception.
Trajectory evaluation uses observable events only and must never request hidden
reasoning, private chain-of-thought, or model scratchpads.

Engineering Memory classification is also evidence/disposition only. It cannot
expand the approved Work Block write-set, specification, governance, Hard Stops,
or any external capability.

## Governance Profiles

The Work Block selects the smallest sufficient governance profile:

- **Advisory:** read-only analysis; no repository mutation.
- **Controlled:** one bounded executor, explicit scope/write-set, basic review and deterministic checks.
- **Managed:** approved specification and plan, formal Define-quality evidence/prerequisite, Critic, Reviewer, Verifier, and evaluation for non-deterministic or consequential agent behavior.
- **Assured:** stronger independence, fixed evaluation rubric/benchmark revisions, drift audit, runtime evidence.
- **Distributed:** multiple runtimes/worktrees/teams with explicit handoff, observable-event provenance, and consolidation.

Runtime choice is separate from governance profile.

### Narrow Deterministic Repair

NDR is a Controlled submode for deterministic, reversible low- or medium-risk
repairs only. The Work Block must define an exact CI/bootstrap/runtime-validation
allowlist, prohibited domains, root cause, deterministic verification commands,
and stop condition in one repair record. It excludes architecture, product, auth,
security-boundary, public API, schema, data, deploy, and dependency-upgrade work.

NDR has one implementation pass, at most one correction, and one independent
read-only combined assurance report covering review and verification. Integration
Stabilization may group at most three eligible repair records and two correction
rounds; a limit or eligibility failure returns to Owner decision.

---

# Stage 0 — Define

## Owner

Orchestrator. Architect, requirements-review, consistency-analysis, and Critic
functions may be delegated within their authority boundaries.

## Purpose

Convert a request into an approved, bounded, auditable, implementation-ready Work
Block before source changes begin.

## Required Inputs

- current Owner instruction;
- repository state and relevant current source;
- applicable governance and runtime adapter documents;
- relevant accepted specifications and architecture decisions;
- current operational context when resuming work.

## Activities

1. **Frame the objective**
   - expected final result;
   - measurable done criteria;
   - in-scope and out-of-scope boundaries.

2. **Resolve source of truth**
   - identify or create the active specification;
   - record specification status and revision;
   - identify accepted architecture decisions;
   - treat plans and tasklists as derived artifacts.

3. **Clarify material requirements when needed**
   - use `requirements-clarification` for formal or materially ambiguous work;
   - resolve repository/discovery facts from evidence instead of asking the Owner;
   - record reasonable non-material defaults as explicit assumptions;
   - batch independent material questions when safe;
   - ask dependent material questions sequentially;
   - keep Define blocked when no safe answer exists.

4. **Run requirements-quality review when required**
   - Managed, Assured, and Distributed formal feature work requires a
     requirements-quality verdict before successful Define completion;
   - evaluate the written requirements, not implementation behavior;
   - use `requirements-quality-review` and record
     `READY | CHANGES_REQUIRED | BLOCKED | UNVERIFIED`;
   - Controlled work selects the review by risk; Quick Fix/NDR use their narrower
     contracts.

5. **Classify risk and authority**
   - side-effect class;
   - DB/data action mode;
   - Hard Stops;
   - rollback/recovery expectations;
   - required governance profile.

6. **Negotiate runtime capability**
   - active runtime and adapter;
   - subagent/session/worktree support;
   - hooks and sandbox availability;
   - model class and budget posture;
   - actual isolation available;
   - observable-event capability;
   - fallback path for missing capability.

7. **Define execution topology**
   - logical functions required;
   - runtime binding for each function;
   - one Coder per write-set;
   - parallel work only for independent scopes;
   - consolidation owner.

8. **Route skills**
   - checked;
   - matched;
   - used;
   - skipped with reason.

9. **Create implementation/assurance plans and traceable tasks**
   - ordered tasks;
   - explicit write-set;
   - dependencies and safe parallelization;
   - review and verification plan;
   - evaluation requirement and approved plan path;
   - drift triggers;
   - when durable learning is a credible closeout outcome, the exact Engineering
     Memory target path that may be updated during Close;
   - for formal Managed/Assured/Distributed tasklists, use stable `REQ-*`,
     `AC-*`, and `TASK-*` references for requirement implementation tasks;
   - classify setup/foundation, assurance, and documentation work honestly rather
     than inventing fake requirement IDs.

10. **Validate structural traceability when the stable-ID format is in use**
    - run `python3 scripts/validate-define-traceability.py --spec <spec> --tasks <tasklist>`;
    - orphan requirements, orphan acceptance criteria, unknown references,
      malformed requirement tasks, duplicate IDs, or missing task paths keep the
      structural check `BLOCKED`;
    - only `type=requirement` tasks satisfy REQ/AC implementation coverage;
    - the validator proves structure only, never product correctness.

11. **Run read-only pre-execution consistency analysis**
    - use `spec-consistency-analysis` to compare specification, accepted
      architecture/plan, tasks, dependencies, and write-set;
    - route fixes back to the artifact that owns the problem;
    - do not silently rewrite approved normative artifacts during analysis;
    - record `READY | CHANGES_REQUIRED | BLOCKED | UNVERIFIED`.

12. **Resolve the aggregate Define-quality prerequisite when applicable**
    - Managed, Assured, and Distributed require it by profile; mutable
      `required=false` cannot disable it;
    - Controlled selects it proportionally by risk/work mode; Quick Fix/NDR keep
      their narrower contracts unless escalated;
    - applicable readiness requires `status=READY` plus non-blank requirements-review,
      traceability, and consistency-analysis evidence bindings;
    - missing or malformed applicable state fails closed;
    - the aggregate is evidence only and does not open the Write Gate.

13. **Run Critic function when triggered**
    - challenge scope, assumptions, authority, risk, topology, requirements-quality
      evidence, consistency evidence, verification, and evaluation design;
    - record `APPROVE`, `SUPPLEMENT`, or `RECONSIDER`;
    - rerun Define for material gaps.

## Formal Traceability Syntax

Specification:

```text
- REQ-001: Required behavior.
- AC-001 [req=REQ-001]: Measurable acceptance criterion.
```

Tasklist:

```text
- [ ] TASK-001 [type=requirement] [req=REQ-001] [ac=AC-001] [paths=src/a.py,tests/test_a.py] Implement behavior.
```

Allowed task types: `requirement`, `enabling`, `assurance`, `documentation`.
Non-requirement task types may use `req=-` and `ac=-` when no direct product
trace exists, but every task still declares explicit paths/write-set. Meaningful
references on non-requirement tasks remain structurally validated but do not count
as implementation coverage.

## Evaluation Triggers

Output or trajectory evaluation is required when any condition applies:

- output is materially non-deterministic;
- an agent selects tools or execution paths autonomously;
- consequential automation depends on process compliance;
- production users depend on agent-generated responses or decisions;
- an approved benchmark, dataset, rubric, or LM judge is part of acceptance;
- Managed, Assured, or Distributed governance requires it by risk classification.

When evaluation is not required, record the reason explicitly. Runtime or model name
alone neither requires nor waives evaluation.

## Exit Conditions

- active specification identified and approved or marked with explicit approval requirement;
- blocking ambiguity resolved or Define remains blocked;
- required requirements-quality evidence passing;
- architecture baseline identified;
- Work Block complete;
- traceable tasklist/write-set complete when required;
- deterministic traceability validation passing when required;
- Define consistency evidence passing when required;
- applicable aggregate Define-quality prerequisite `READY` with its evidence bindings;
- runtime capability and isolation recorded;
- verification/review/evaluation/drift plan recorded;
- Critic gate resolved when triggered;
- write gate `READY`.

No source changes are allowed while the write gate is `BLOCKED`.

---

# Stage 1 — Execute

## Owner

Coder. Exactly one write-capable Coder per write-set.

## Entry Conditions

- write gate `READY`;
- approved specification and implementation plan;
- applicable aggregate Define-quality prerequisite `READY` with required evidence bindings;
- explicit write-set;
- side-effect and Hard Stop classification;
- required runtime capability available or an approved degraded fallback recorded;
- approved evaluation plan available when evaluation is required.

Runtime-neutral policy does not imply identical enforcement mechanics. Runtime
adapters with source-write interception must enforce applicable Define-quality
fail-closed. Runtimes without equivalent interception must record that capability
limitation and must not claim machine-enforced prevention.

## Activities

1. Read the active specification, plan, acceptance criteria, and relevant source.
2. Implement only inside the approved write-set.
3. Preserve existing project patterns unless the specification approves a change.
4. Do not silently change requirements or architecture.
5. When a legitimate requirement change is discovered, stop and return to Define.
6. Run scoped self-checks.
7. Capture required observable tool, gate, check, retry, side-effect, and evidence events.
8. Redact secrets and protected data from operational evidence.
9. Freeze the implementation diff for assurance.
10. Report `DONE`, `DONE_WITH_CONCERNS`, `NEEDS_CONTEXT`, or `BLOCKED`.

## Exit Conditions

- planned changes implemented or blockers documented;
- no unapproved scope expansion;
- frozen diff or changed-file list available;
- self-check evidence recorded;
- required observable evaluation events attributable to the Work Block;
- implementation result handed to Stage 2.

A failed Execute stage blocks assurance from passing. Stage 2 may still inspect
partial work for diagnostics, but cannot produce a successful verdict.

---

# Stage 2 — Assure

Stage 2 contains four distinct functions:

```text
2A Independent Review
2B Technical Verification
2C Agent Evaluation
2D Specification Drift Audit
```

They may be executed by separate agents or by separate passes of one runtime,
but actual independence and limitations must be recorded.

Requirements-quality review is a Stage 0 review of the specification. It does not
replace Stage 2 review/verification of the delivered implementation.

## 2A — Independent Review

### Purpose

Inspect the frozen diff for engineering quality and risk.

### Reviewer Checks

- defects and regressions;
- incorrect assumptions and edge cases;
- architecture and dependency violations;
- security and privacy risks;
- maintainability and unnecessary complexity;
- missing tests, evaluation evidence, or observability;
- scope expansion;
- unsafe generated boilerplate or prompt-shaped abstractions.

### Verdicts

- `READY`
- `CHANGES_REQUIRED`
- `BLOCKED`
- `UNVERIFIED`

`CHANGES_REQUIRED` returns the Work Block to Execute for correction, followed by
review of the updated frozen diff.

## 2B — Technical Verification

### Purpose

Demonstrate that acceptance criteria and observable contracts hold.

### Evidence Tiers

- **Lite:** changed-file scope, targeted types/lint/build, relevant tests, obvious regressions.
- **Standard:** Lite plus API/schema, positive/negative cases, runtime smoke, errors/logging, security baseline.
- **Full:** Standard plus threat model, security classification, auth/origin guards, migrations/rollback, independent runtime evidence, approved production-like smoke.

### Verdicts

- `READY`
- `BLOCKED`
- `UNVERIFIED`

Unavailable evidence is `UNVERIFIED`, not `READY`.

## 2C — Agent Evaluation

### Purpose

Evaluate the delivered artifact and observable agent trajectory against the
approved evaluation plan.

### Evidence Classes

- deterministic check results;
- output rubric results;
- observable trajectory events and event-source provenance;
- benchmark/dataset and rubric revisions;
- evaluator identity, judge policy, actual runtime, model class, and isolation;
- inspection gaps, blocked checks, and residual risks.

### Rules

- deterministic correctness cannot pass solely through an LM judge;
- trajectory pass requires all blocking required events and no prohibited event;
- missing or inaccessible event sources are `BLOCKED` or `UNVERIFIED`;
- a fluent final response is not trajectory evidence;
- private chain-of-thought and hidden reasoning are never required evidence;
- changing criteria, thresholds, datasets, or judge policy creates a new plan revision.

### Verdicts

- `READY`
- `BLOCKED`
- `UNVERIFIED`

Required evaluation cannot be skipped. Optional evaluation may be `SKIPPED` only
with a recorded reason in the active Work Block.

## 2D — Specification Drift Audit

### Purpose

Compare:

```text
Specification <-> Architecture decisions <-> Plan <-> Code <-> Tests/Evals <-> Documentation
```

Use `spec-drift-audit` and the standard drift report template.

### Required Triggers

- public behavior, route, API, schema, persistence, or runtime contract changed;
- auth, payment, DB, provider, webhook, security, or architecture changed;
- specification changed during implementation;
- behavior was added outside the approved plan;
- evaluation criteria or evidence reveal an undocumented contract;
- 3 or more implementation files changed;
- Assured or Distributed profile.

### Verdicts

- `ALIGNED` -> drift gate `READY`;
- `ALIGNMENT_REQUIRED` -> drift gate `BLOCKED` until corrected and rerun;
- `BLOCKED` -> drift gate `BLOCKED`;
- `UNVERIFIED` -> drift gate `UNVERIFIED`.

A Quick Fix may skip drift audit only when it has no behavior, contract, schema,
security, runtime, architecture, evaluation, or governance impact.

## Isolation Requirements

| Work type | Review / verification / evaluation expectation |
|---|---|
| Controlled, low-risk | separate pass; same-context allowed but recorded |
| Managed, non-sensitive | separate-subagent or separate-session preferred |
| Assured or sensitive | independent-readonly-root or separate-runtime preferred |
| credentials, live data, deploy mutation | OS-isolated where practical and no production credentials for read-only assurance |
| parallel writers | separate-worktree per write-set plus consolidation |

## Stage 2 Exit Conditions

- review gate resolved;
- verification verdict recorded;
- evaluation verdict recorded when required;
- drift gate resolved when triggered;
- findings include evidence and inspection gaps;
- corrections rerun through the applicable assurance functions;
- parallel results consolidated when relevant.

---

# Stage 3 — Close

## Owner

Orchestrator.

## Activities

1. Determine closeout mode.
2. Synchronize derived artifacts with the approved specification and delivered state.
3. Update task status.
4. For every non-trivial Work Block, perform an Orchestrator Learning Review of material findings from Define, Execute, Assure, and Close.
5. Classify reusable lesson candidates as exactly `promoted`, `operational-only`, or `not-applicable`.
6. Deduplicate and promote evidence-backed durable knowledge into already-approved Engineering Memory paths when applicable.
7. Record operational results and residual risks.
8. Produce closeout report and Owner summary.

## Orchestrator Learning Review

Learning Review is required for both `success-closeout` and `reporting-only`
when the Work Block is non-trivial. It is part of normal Close and does not
require a separate Owner reminder after Work Block/write authority is approved.

1. Review material findings from **Define, Execute, Assure, and Close**.
2. Consider recurring failure/recovery patterns, durable invariants,
   source-of-truth lessons, lifecycle/process defects, verification gaps,
   reusable operational patterns, and rejected approaches with important
   evidence-backed reasons.
3. Promote only evidence-backed knowledge capable of changing future planning,
   execution strategy, review, verification, recovery, or invariant enforcement.
4. Exclude one-off noise, speculation, raw transcripts, private chain-of-thought,
   secrets/private data, routine status chronology, and facts cheaper to
   re-verify live.
5. `none identified` is valid; do not manufacture a lesson.
6. Before `promoted`, deduplicate against existing Engineering Memory and prefer
   updating/extending/superseding an existing reusable principle to creating a
   duplicate.
7. A promoted lesson records evidence, scope, reusable principle,
   replacement/mitigation/recovery, authority boundary, review trigger, and last
   verified.
8. Classification/candidate discovery is not permission. Promotion may mutate
   only a memory path already approved by the active Work Block; otherwise
   return to Define.
9. Project-specific lessons remain project-local. Framework generalization is a
   follow-up candidate only until a separate evidence-backed framework Work
   Block approves policy/template changes.

The closeout report records lifecycle-stage review coverage, material candidates
and dispositions (or `none identified`), deduplication/promotion result,
authority boundary, residual risk, and next action.

## Source-of-Truth Synchronization Order

1. current Owner instruction or approved change request;
2. approved specification;
3. accepted architecture decisions and external contracts;
4. approved implementation and evaluation plans;
5. tasklist;
6. review, verification, evaluation, drift, and closeout reports;
7. engineering memory;
8. operational memory and logs.

Plans, requirements-quality reports, consistency reports, validator results, and
tasklists never silently override an approved specification.

## Successful Closeout Conditions

- implementation completed inside scope;
- review gate `READY` or valid documented skip;
- verification verdict `READY`;
- required evaluation status/verdict `READY`;
- drift gate `READY` or valid documented skip;
- required Hard Stop actions either not performed or explicitly approved;
- residual risks documented;
- normative and derived artifacts synchronized;
- required non-trivial Learning Review recorded.

Otherwise use `reporting-only` and keep the task blocked or incomplete.

---

# Quick-Fix Path

A Quick Fix is allowed only when all are true:

- at most 2 implementation files;
- no behavior, route, API, schema, persistence, security, architecture, runtime,
  dependency, evaluation, governance, or public contract impact;
- no Hard Stop;
- rollback is trivial;
- targeted deterministic checks are available.

```text
Scope statement -> Implement -> targeted self-review/checks -> sync -> close
```

The Orchestrator must record why the full lifecycle and evaluation were not required.

---

# Failure and Degraded Modes

- A failed stage blocks downstream success claims.
- Work may continue for diagnostics, corrective planning, evidence capture, or reporting.
- Missing subagent/model/plugin capability does not remove the logical function.
- Use the strongest available fallback and record actual runtime and isolation.
- A degraded review or evaluation cannot upgrade a blocked verification result.
- Missing observable trajectory evidence cannot be described as a pass.
- Missing required Define-quality evidence or an unresolved applicable aggregate
  prerequisite cannot be described as a passing Define stage.
- No agent may grant itself authority because a tool is technically available.
