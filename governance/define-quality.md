# Define-Stage Requirements Quality Contract

## Purpose

Stage 0 / Define must produce implementation-ready requirements without turning
an agent's guesses into silent product decisions.

This contract adds three quality functions before implementation:

1. **Clarification** — resolve material ambiguity before technical planning.
2. **Requirements-quality review** — evaluate the written specification as a
   requirements artifact, not as an implementation.
3. **Pre-execution consistency analysis** — compare specification, accepted
   architecture/plan, and task decomposition for gaps and conflicts.

These functions refine Define. They do not create new authority roles, a second
lifecycle, or a new source of truth.

## Authority and Source of Truth

The existing authority order remains unchanged:

```text
Owner instruction
  -> approved specification
  -> accepted architecture decisions / external contracts
  -> approved plan and write-set
  -> task decomposition
  -> assurance evidence
```

Clarification answers are authoritative only after they are recorded in the
approved specification or an Owner-approved change request.

A requirements checklist, consistency report, tasklist, validator result, or
external benchmark never overrides the approved specification and never opens a
write gate by itself.

## 1. Clarification Function

### Goal

Reduce ambiguity that would materially change behavior, architecture, data,
permissions, task decomposition, verification, operations, security, compliance,
or user experience.

### Resolution classes

Every unresolved item is routed to exactly one class:

- **evidence-resolvable** — answer from repository, accepted decisions, external
  contract, or other authoritative evidence; do not ask the Owner;
- **explicit assumption** — a reasonable, reversible, non-material default that
  does not change product scope or risk; record it visibly;
- **material independent ambiguity** — ask with other independent high-impact
  questions in a small bounded batch;
- **material dependent ambiguity** — ask sequentially because one answer changes
  the next decision;
- **blocking ambiguity** — no safe default or evidence exists; keep Define
  `BLOCKED` until resolved.

### Coverage scan

A formal clarification pass considers, when relevant:

- outcome, scope, and exclusions;
- actors, permissions, and ownership;
- domain entities, identity, state, and lifecycle transitions;
- primary, alternate, failure, retry, recovery, and conflict behavior;
- integrations and external contracts;
- performance, reliability, observability, security, privacy, compliance, and
  accessibility requirements;
- migration/compatibility expectations;
- terminology, assumptions, and measurable completion signals.

This is a coverage framework, not a requirement to ask about every category.
Questions are only justified when the answer materially changes downstream work.

### Interaction budget

Default behavior:

- resolve evidence-resolvable facts without Owner interaction;
- record non-material defaults as assumptions;
- batch up to three independent material questions when that reduces interaction
  without coupling answers;
- ask dependent questions one at a time;
- normally stop after five material Owner decisions in one clarification pass and
  surface any remaining blocking ambiguity explicitly.

The interaction budget is an efficiency rule, not permission to guess a blocking
requirement.

### Write-back rule

Accepted clarification must update the authoritative specification, including any
affected requirement, acceptance criterion, assumption, non-goal, risk, or open
decision. Do not leave contradictory stale wording in place.

## 2. Requirements-Quality Review

### Goal

Determine whether the specification is sufficiently clear, complete, consistent,
measurable, bounded, and traceable to support planning and implementation.

The review evaluates **requirements writing**, not code behavior.

Typical questions include:

- Is every material behavior explicitly required or explicitly out of scope?
- Are actors and permissions unambiguous?
- Are vague terms converted to objective criteria where necessary?
- Are failure, conflict, empty, retry, and recovery cases specified when material?
- Are security/privacy/operational constraints present when the domain requires
  them?
- Are assumptions and external dependencies explicit?
- Can each required behavior be connected to an acceptance criterion?

### Ownership

- Managed, Assured, and Distributed work with a formal specification require a
  requirements-quality review before Critic/write-gate completion.
- The preferred reviewer is a read-only function distinct from the specification
  author when the selected governance profile expects independence.
- Controlled work uses the review by risk.
- Quick Fix and eligible NDR follow their existing narrower contracts.

The specification author may perform self-checks, but a self-check must not be
represented as independent review.

### Verdicts

Use:

- `READY` — no unresolved material requirements-quality blocker;
- `CHANGES_REQUIRED` — specification changes are required before implementation;
- `BLOCKED` — a dependency or Owner decision prevents completion;
- `UNVERIFIED` — required evidence was unavailable.

`READY` is evidence for Define. It does not grant source-write authority.

## 3. Stable Traceability

### When required

Use stable requirement/acceptance/task IDs for Managed, Assured, and Distributed
work when a formal tasklist is produced. Controlled work may use the same format
when it improves clarity. Do not force IDs into trivial quick fixes.

### Specification format

Portable minimum syntax:

```text
- REQ-001: Required behavior.
- AC-001 [req=REQ-001]: Measurable acceptance criterion.
```

An acceptance criterion may cover multiple requirements:

```text
- AC-010 [req=REQ-003,REQ-004]: Observable combined outcome.
```

### Task format

Portable minimum syntax:

```text
- [ ] TASK-001 [type=requirement] [req=REQ-001] [ac=AC-001] [paths=src/a.py,tests/test_a.py] Implement behavior.
```

Allowed task types:

- `requirement` — implements approved product/technical requirements and must
  reference at least one `REQ-*` and `AC-*`;
- `enabling` — setup/foundation work; requirement references may be `-`;
- `assurance` — tests/evidence/review support; requirement references may be `-`;
- `documentation` — derived documentation synchronization; requirement references
  may be `-`.

Every task declares explicit paths/write-set. Do not invent fake requirement IDs
for enabling or assurance work merely to satisfy a validator.

### Deterministic validation

`validate-define-traceability.py` checks structural coverage only. All task types
remain subject to syntax, duplicate-ID, explicit-path, and unknown-reference
validation when they carry references. **Only `type=requirement` tasks count as
implementation coverage** for `REQ-*` and `AC-*`.

An enabling, assurance, or documentation task may carry a meaningful requirement
or acceptance reference for context, but that reference cannot satisfy the
implementation-coverage requirement.

The validator may prove that IDs and references are complete and internally
consistent; it cannot prove that requirements are correct, sufficient, secure,
or valuable. A structural failure keeps the pre-execution traceability check
`BLOCKED` until corrected.

## 4. Pre-Execution Consistency Analysis

### Goal

Perform a read-only comparison before Execute while corrections are still cheap.

Compare:

```text
specification <-> architecture decisions / plan <-> tasks / write-set
```

Check for:

- approved requirement with no acceptance criterion;
- approved requirement with no implementation task;
- task referencing no approved requirement without an explicit enabling/
  assurance/documentation classification;
- unknown or stale requirement/acceptance IDs;
- plan decision that contradicts the specification;
- task or write-set that introduces unspecifed behavior or scope;
- unresolved blocking ambiguity or assumption presented as fact;
- dependency or parallelization claim inconsistent with write-set overlap;
- verification work that cannot demonstrate the stated acceptance criteria.

### Mutation rule

The analyzer is read-only for normative artifacts. It reports findings and routes
remediation to the owning artifact:

- requirement problem -> clarification/specification revision;
- architecture problem -> architecture/plan revision;
- decomposition problem -> regenerate/update tasks;
- authority/scope problem -> Work Block/Owner decision.

It must not silently rewrite the approved specification, plan, or tasklist.

### Result

Use:

- `READY` — no unresolved material cross-artifact inconsistency;
- `CHANGES_REQUIRED` — an owning artifact must be corrected;
- `BLOCKED` — required evidence/decision is unavailable;
- `UNVERIFIED` — the analyzer could not inspect required artifacts reliably.

## 5. Executable Define-Quality Prerequisite

The three Define-quality functions above remain separate evidence producers, but
they are represented at the source-transition boundary by **one aggregate
prerequisite** in the existing schema-v3 active Work Block. This is intentionally
not three additional gates.

Canonical aggregate shape:

```json
"define_quality": {
  "required": false,
  "status": "PENDING",
  "requirements_review": "",
  "traceability": "",
  "consistency_analysis": ""
}
```

### Applicability

Applicability is derived fail-closed from governance profile where the profile
already requires formal Define discipline:

```text
Managed / Assured / Distributed -> required
Controlled                       -> selected proportionally by risk/work mode
Quick Fix / eligible NDR         -> normally not required unless escalated
```

For Managed, Assured, and Distributed work, mutable `required=false` is a
configuration contradiction; it cannot disable the prerequisite. A missing or
malformed aggregate is unresolved and blocks source execution rather than being
inferred as success.

For Controlled work, `required` remains a proportional selector. Quick Fix and
NDR retain their existing narrower eligibility and escalation contracts.

### Readiness and evidence binding

When the prerequisite is applicable, source execution requires:

```text
status == READY
trim(requirements_review) != ""
trim(traceability) != ""
trim(consistency_analysis) != ""
```

The evidence values are bindings, not authority grants. Hot-path source guards
validate that the aggregate is well formed, applicable, READY, and bound to
non-blank evidence. They do not recursively open or semantically re-run the
referenced reports. Dedicated validators and later assurance remain responsible
for evidence quality.

### Schema-v3 migration

This is an additive evidence prerequisite inside the existing schema-v3 Work
Block state. It does not change authority mode, roles, lifecycle, Hard Stops, or
the source Write Gate, so no schema-v4 bump is required.

Migration is fail-closed:

- new generated schema-v3 defaults contain `define_quality`;
- malformed aggregate -> `BLOCKED`;
- Managed/Assured/Distributed with missing aggregate -> `BLOCKED` / migration
  required;
- missing aggregate never implies `READY`.

`template/.agent/active-work-block.default.json` is the canonical portable tracked
default. A generated local `.agent/active-work-block.json` is operational state
restored only after the canonical default passes installation-profile validation.
The tracked template compatibility copy must remain aligned with the default at
scaffold time but does not become a second SSOT.

### Runtime capability boundary

The semantic rule is runtime-neutral: formal source execution is not authorized
until applicable Define-quality evidence is READY.

Runtime adapters that actually provide source-write interception, such as the
bundled Codex and Claude adapters, must enforce this prerequisite fail-closed.
A runtime without equivalent interception must report that capability limitation
truthfully and must not claim machine-enforced prevention. This contract does not
justify inventing a universal hook layer merely for surface symmetry.

### Authority boundary

The aggregate is evidence state only. It grants no source-write, Git,
integration, credential, deployment, publication, external-action, or Hard Stop
authority. Resolving it never replaces Critic. After it is READY, the existing
Critic -> Write Gate -> write-set path still applies in full.

## Stage 0 Integration

For Managed/Assured/Distributed formal feature work, the preferred Define order is:

```text
objective/discovery
  -> specification draft
  -> clarification
  -> requirements-quality review
  -> architecture / implementation plan
  -> traceable task decomposition + write-set
  -> deterministic traceability validation
  -> read-only consistency analysis
  -> aggregate Define-quality prerequisite READY
  -> Critic
  -> write gate READY
```

A valid smaller path may collapse functions for low-risk Controlled work, but no
profile may use this contract to weaken existing authority, Hard Stops,
evaluation, assurance, or closeout rules.

## Provenance

- **Classification:** `adapted`
- **Influential source:** `github/spec-kit@bf88c9f9a82fa370c7a7257aa2b3cf10b457b65c`
- **Local research:** `framework/research/spec-kit-gap-analysis-2026-08-14.md`, `framework/research/spec-kit-clarify-checklist-dry-run-2026-08-14.md`
- **Material local delta:** evidence-first clarification; bounded batching of
  independent questions; existing Agentic SDLC authority/write gate retained;
  reviewer-owned requirements gate separated from implementation verification;
  deterministic stable-ID traceability added; consistency analysis remains
  read-only and subordinate to specification authority; aggregate Define-quality
  evidence is machine-observable without becoming a parallel authority system.
- **Novelty claim:** none
