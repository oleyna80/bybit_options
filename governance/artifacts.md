# Portable Artifact Contract

## Purpose

Artifacts are the interoperability boundary between humans, agent runtimes,
models, sessions, and machines. A future agent must be able to recover the
approved state without relying on hidden prompt history.

## Normative Chain

```text
Owner objective or approved change request
  → specification and acceptance criteria
  → architecture decisions
  → implementation plan, evaluation plan when required, and write set
  → frozen implementation diff
  → review report
  → verification report
  → evaluation report when required
  → specification drift report when required
  → closeout report and engineering-memory promotion
```

Operational logs, generated code maps, external reports, and agent memory may
provide evidence. They do not override approved normative artifacts.

## Minimum Artifact Metadata

Normative and assurance artifacts should expose machine-readable metadata, for
example YAML front matter:

```yaml
schema_version: 1
artifact_type: specification
artifact_id: feature-listing-publication
status: approved
owner_role: orchestrator
work_block_id: wb-042
revision: 3
supersedes: null
created_at: 2026-07-25
last_verified: 2026-07-25
```

Required concepts:

- artifact type and stable ID;
- lifecycle status;
- responsible role;
- Work Block association;
- revision or immutable source revision;
- supersession relationship;
- verification date or method where relevant.

## Artifact Status

Use explicit status values appropriate to the artifact:

- `draft` — proposed content, not authoritative;
- `review` — awaiting the required decision;
- `approved` — current authority for its scope;
- `superseded` — replaced by a named artifact/revision;
- `retired` — no longer applicable;
- `blocked` — incomplete because a dependency or gate failed;
- `generated` — derived context, never authority by itself.

## Specification

A feature or system specification defines:

- intended user or technical outcome;
- required behavior and contracts;
- acceptance criteria;
- constraints and non-goals;
- security, data, and operational requirements;
- compatibility and migration expectations;
- open decisions that block implementation.

For a small Controlled Work Block, the approved objective, constraints, and
acceptance criteria inside the Work Block may serve as the specification. A
separate specification file is required when behavior, public contracts,
architecture, security boundaries, schemas, migrations, external integrations,
or multiple work packages are involved.

Plans and tasklists are derived from the approved specification. If a plan or
implementation conflicts with the specification, the workflow must either
correct the derivative artifact or formally revise the specification.

## Implementation Plan

The plan defines:

- implementation sequence;
- approved write set;
- dependencies;
- runtime and topology selection;
- isolation requirement;
- risk and side-effect classification;
- verification plan;
- evaluation plan requirement and location when applicable;
- rollback/recovery strategy.

A plan may not silently change product or architecture requirements.

## Evaluation Plan

An evaluation plan is required when the Work Block selects output or observable
trajectory evaluation. It defines:

- stable evaluation ID, Work Block ID, and revision;
- objective, specification revision, and frozen subject revision;
- deterministic checks and expected evidence;
- output criteria, thresholds, weights, and evaluator types;
- trajectory requirements, event sources, required events, and prohibited events;
- rubric, benchmark, and judge-policy revisions;
- actual or required isolation boundary;
- blocking criteria and aggregate verdict rule.

Evaluation plans must not request private chain-of-thought, hidden reasoning,
model scratchpads, or internal deliberation. Trajectory criteria operate on
observable events and produced artifacts only.

## Review Report

The Reviewer reports:

- exact diff or revision reviewed;
- inspected files and omitted areas;
- defects and regressions;
- architecture and maintainability findings;
- security and side-effect findings;
- missing tests or evidence;
- isolation level and launch mechanism;
- verdict: `READY | CHANGES_REQUIRED | BLOCKED | UNVERIFIED`.

`SKIPPED` is a review-gate state, not a Reviewer verdict. It is valid only when
the selected governance profile and lifecycle explicitly allow a skip and the
Work Block records the reason.

## Verification Report

The Verifier reports:

- exact objective, specification revision, and diff verified;
- commands, tests, runtime checks, evaluation reports, and artifacts used;
- acceptance-criterion result matrix;
- inspection gaps and blocked checks;
- residual risks;
- isolation level and launch mechanism;
- verdict: `READY | BLOCKED | UNVERIFIED`.

A check that could not run is `blocked` or `not_run`, never `pass`.

## Evaluation Report

The evaluation report records:

- exact evaluation plan and subject revisions;
- runtime, logical role, model class, actual model when policy permits, and isolation;
- deterministic, output, and trajectory result matrices;
- observable event sources, missing events, and prohibited events observed;
- evaluator type, judge identity, rubric/prompt revision, and calibration evidence when used;
- blocked checks, inspection gaps, residual risks, and aggregate calculation;
- verdict: `READY | BLOCKED | UNVERIFIED`.

A deterministic criterion cannot pass solely through an LM judge. A trajectory
criterion cannot pass when required observable events are missing, prohibited
events occurred, or the event source is unavailable. Evaluation evidence does not
open authority or integration gates.

## Drift Report

Drift audit compares:

```text
specification ↔ architecture decisions ↔ plan ↔ code ↔ tests/evals ↔ documentation
```

Classifications:

- `ALIGNED` — requirement, implementation, evidence, and documentation agree;
- `MISSING_IMPLEMENTATION` — an approved requirement is not delivered;
- `UNSPECIFIED_IMPLEMENTATION` — delivered behavior lacks approved specification;
- `STALE_PLAN` — implementation matches the specification but the plan is outdated;
- `STALE_TEST` — implementation exists but evidence does not prove it;
- `STALE_DOCUMENTATION` — documentation disagrees with delivered behavior;
- `SPEC_CHANGE_REQUIRED` — a legitimate requirement change needs approval;
- `INSPECTION_GAP` — required evidence was unavailable.

Drift report verdicts are:

- `ALIGNED` — drift gate becomes `READY`;
- `ALIGNMENT_REQUIRED` — drift gate remains `BLOCKED` until corrected and rerun;
- `BLOCKED` — material mismatch prevents successful closeout;
- `UNVERIFIED` — evidence is insufficient to establish alignment.

`SKIPPED` is a drift-gate state, not a drift-report verdict. It is allowed only
under the documented Quick-Fix rule.

## Closeout Report

Successful closeout requires:

- review gate `READY`, or an explicitly allowed and documented `SKIPPED` state;
- verification verdict `READY`;
- required evaluation status/verdict `READY`;
- required drift gate `READY`, or an explicitly allowed and documented `SKIPPED` state;
- no unresolved `CHANGES_REQUIRED`, `BLOCKED`, or `UNVERIFIED` state;
- updated task and decision state;
- recorded residual risks;
- promoted durable knowledge when applicable.

Otherwise use reporting-only closeout and keep the Work Block blocked.

## Narrow Deterministic Repair Artifacts

An eligible Controlled NDR uses exactly one `repair record` and one independent
`combined assurance report` in place of separate review, verification, and drift
documents. The repair record must capture the deterministic root cause, exact
allowlist, prohibited domains, verification commands, correction count, and stop
condition. Combined assurance binds its review and verification observations to
the frozen subject revision and records its independent session/agent boundary.

NDR permits one implementation pass and at most one correction. Integration
Stabilization may contain at most three repair records and two correction rounds.
The ceiling is an escalation boundary, not a reason to omit evidence.

Tracked closeout reports must not copy dynamic Git or CI counters. CI state is
authoritative only from provider-native checks bound to the subject SHA; an
uploaded JSON snapshot is portable evidence and never release authority.

## Source-of-Truth Order

Resolve conflicts in this order:

1. Current explicit Owner instruction for the active Work Block.
2. Active project operating contract and approved governance policy.
3. Approved specification and acceptance criteria.
4. Accepted architecture decisions and external/public contracts.
5. Approved implementation and evaluation plans and write set.
6. Active task decomposition.
7. Review, verification, evaluation, drift, and closeout evidence.
8. Durable engineering memory.
9. Operational memory, runtime logs, and generated context.

Lower layers must not silently override higher layers.
