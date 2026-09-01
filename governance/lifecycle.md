# Runtime-Neutral Lifecycle

## Purpose

The lifecycle defines control functions and evidence transitions. It does not
require one permanent agent per function and does not prescribe a specific
runtime topology.

The lifecycle is a process-control system, not the primary security boundary.
Work Blocks, write sets, Critic/Reviewer/Verifier gates, and project-local hooks
constrain normal agent behavior. Consequential authority is enforced externally
wherever practical through GitHub repository rules, least-privilege credentials,
workflow permissions, OS isolation, and separately held production credentials.

Per-Work-Block SSH signatures and authorization-bootstrap commits are not part of
the normal lifecycle. They were retired because the cryptographic local state
machine introduced circular bootstrap, replay, H0/H1/H2, expiry, digest, and
runtime-parity complexity while remaining dependent on project-local hooks that
are not an OS security boundary.

## Macro Stages

### Stage 0 — Define

Functions:

1. Intake and objective framing.
2. Discovery and repository orientation.
3. Architecture and dependency decisions.
4. Specification and acceptance criteria.
5. Implementation planning and write-set definition.
6. Critic review of scope, risks, topology, verification, and evaluation design.
7. Classification of consequential external capabilities and Hard Stops.

Required outcome:

- approved objective;
- authoritative specification or explicit quick-fix contract;
- implementation plan and write set;
- risk, side-effect, and external Hard-Stop classification;
- verification plan;
- evaluation plan when output or trajectory evaluation is required;
- resolved Critic gate or documented permitted fallback;
- explicit external capability path for any consequential action.

No implementation write may begin while Stage 0 is blocked.

Generated schema-v3 projects may open the local source scope after these Define
conditions are satisfied. Opening the local scope does not create production,
credential, live-data, destructive, protected-branch, or external-publish
authority.

When durable learning is a credible closeout outcome, Define should include the
exact Engineering Memory path in the approved Work Block/write-set rather than
relying on Close to invent new write authority.

### Stage 1 — Execute

Functions:

1. Scoped implementation by one Coder per write set.
2. Targeted self-checks.
3. Scope and side-effect re-evaluation when new information appears.
4. Observable event and evidence capture required by the approved evaluation plan.
5. Diff freeze for assurance.

Required outcome:

- implementation matches the approved write set;
- no unapproved side effect occurred;
- required observable trajectory evidence is attributable to the Work Block;
- the diff is frozen or its exact revision is recorded;
- implementation concerns and unresolved assumptions are reported.

Within approved scope, ordinary reversible development operations may include
staging, local commits, normal feature-branch pushes, and pull-request updates.
They do not require an Owner SSH signature merely because Git state changes.

Direct protected/default-branch mutation, force/history-rewriting operations,
production/live infrastructure, live data, credentials/secrets, irreversible
external publication, and real client-facing communication remain outside the
normal agent channel and require the separately controlled capability defined in
Stage 0.

A material scope, requirement, architecture, authority, or external-capability
change returns the Work Block to Stage 0.

### Stage 2 — Assure

Functions:

1. Independent code review of the frozen diff.
2. Technical verification against acceptance criteria and contracts.
3. Output and observable trajectory evaluation when required.
4. Specification drift audit when required.
5. Consolidation of findings and corrective-loop decision.

Review asks whether the change is safe and maintainable.

Verification asks whether the required behavior is demonstrated by evidence.

Evaluation asks whether the final artifact and observable execution events meet an
approved rubric and benchmark revision. Trajectory evaluation inspects tool, gate,
check, retry, side-effect, and evidence events; it never requires hidden reasoning or
private chain-of-thought.

Drift audit asks whether specification, architecture decisions, plan, code,
tests, evaluation evidence, and documentation still describe the same system.

Required outcome:

- review verdict;
- verification verdict;
- evaluation verdict when evaluation is required;
- drift classification when triggered;
- residual risks and inspection gaps;
- corrective action for blocking findings.

Passing local assurance does not grant an external Hard Stop capability. For
example, a `READY` verification may prove a deployable artifact while the actual
production deploy remains unavailable until the external Owner-controlled
workflow or credential boundary permits it.

### Stage 3 — Close

Functions:

1. Classify closeout.
2. Synchronize specifications, decisions, task state, and documentation.
3. For every non-trivial Work Block, review material findings encountered during
   Define, Execute, Assure, and Close for reusable engineering knowledge.
4. Classify reusable lesson candidates as exactly `promoted`, `operational-only`, or `not-applicable`; `none identified` is a valid result.
5. Deduplicate and promote evidence-backed durable knowledge into already-approved
   Engineering Memory paths when applicable.
6. Record residual risks and follow-up Work Blocks.
7. Produce an Owner-facing report.

The Orchestrator Learning Review is a normal non-trivial Close responsibility for
both successful and reporting-only closeout. It does not require a separate Owner
reminder such as "record the lesson" once the Work Block and relevant memory write
authority are approved.

A lesson is durable only when evidence shows that it can change future planning,
execution strategy, review, verification, recovery, or invariant enforcement.
Do not promote one-off noise, speculation, raw transcripts, hidden/private
reasoning, secrets/private data, routine status chronology, or facts cheaper to
re-verify live. Before creating a new lesson, compare existing Engineering Memory
and update/extend/supersede an existing reusable principle when appropriate.

Learning classification is evidence/disposition, not permission. Candidate
discovery cannot expand the approved write-set, Hard Stops, specification, or
governance. If durable promotion needs a path or material framework change outside
the current Work Block authority, return to Define. A project-specific lesson may
suggest a framework improvement, but framework policy/template promotion requires
a separate evidence-backed framework Work Block.

Only a verification verdict of `READY` and every required evaluation verdict of
`READY` permit successful closeout.

`BLOCKED` or `UNVERIFIED` verification/evaluation permits diagnostics, corrective
planning, learning classification, and reporting-only closeout. It does not
permit merge-ready, deploy-ready, release-ready, or completed claims.

Successful process closeout also does not bypass an external repository or
production control. A protected merge, release, or deploy must still satisfy the
applicable GitHub/OS/credential boundary.

## Lifecycle State

Track execution state separately from assurance verdict:

```yaml
stage: define | execute | assure | close
execution_state: blocked | ready | in_progress | completed
verification_verdict: pending | READY | BLOCKED | UNVERIFIED
evaluation_verdict: pending | READY | BLOCKED | UNVERIFIED | not_required
closeout_mode: pending | success | reporting_only
external_capability_state: not_required | unavailable | pending_owner | available | consumed
```

A stage may be `completed` because its required activity finished while the
result remains `BLOCKED` or `UNVERIFIED`.

`external_capability_state` is evidence about a capability controlled outside the
mutable project. Editing project-local lifecycle state cannot create or expand
that capability.

## Local Work-Block Scope State

Generated schema-v3 projects use `authority_mode: github_capability`.

The local source gate has two relevant states:

- `BLOCKED`: source implementation is blocked; canonical coordination paths remain
  available for plans/specifications/evidence and coordination-only commits;
- `READY`: source mutations are allowed only inside the active write set after
  required Define/Critic conditions are resolved.

The recorded `base_commit` is the planning/evidence baseline. A normal feature
commit does not create a cryptographic `STALE`/renew cycle. If requirements,
scope, architecture, or authority materially change, return to Define and update
the Work Block explicitly.

Historical signed authorization records may remain for audit/reference. They do
not create current schema-v3 authority.

## Governance Profiles

### Advisory

- Read-only analysis.
- No implementation write.
- Same-context critique is acceptable when labeled.
- Evaluation is normally optional and cannot be represented as independent when it is not.

### Controlled

- One bounded executor.
- Explicit scope and write set.
- Basic review and verification may run sequentially.
- Deterministic tests are required when applicable; focused evaluation is selected by risk.

#### Narrow Deterministic Repair (NDR)

NDR is a mechanically constrained submode of `Controlled`, not a governance
profile. It is available only for a deterministic, reversible low- or
medium-risk repair with no architecture decision and an exact approved path
allowlist wholly inside CI, bootstrap, or runtime-validation surfaces. Product,
auth, security-boundary, public API, schema, data, deploy, and dependency-upgrade
changes are ineligible.

An eligible NDR has one repair record, one Coder implementation pass, and one
independent read-only combined assurance pass. The repair record names the root
cause, allowlist, prohibited changes, deterministic commands, and stop condition.
Combined assurance records logical review, deterministic verification, and its
final verdict. NDR allows at most one correction round; a failed eligibility
condition or second correction requires an Owner decision.

#### Integration Stabilization

Integration Stabilization is a bounded execution envelope, not a profile. It may
group at most three sequentially discovered eligible NDR items and at most two
correction rounds. Every item keeps its own exact CI/bootstrap/runtime-validation
allowlist. Exceeding either ceiling, changing a prohibited domain, or requiring an
architecture decision stops for Owner decision rather than creating another gate
cycle.

### Managed

- Approved specification and plan.
- Critic before execution.
- Reviewer and Verifier contracts after execution.
- Approved evaluation plan for non-deterministic outputs, agent behavior, or consequential automation.
- Evidence-based closeout.

### Assured

- Independent review and verification.
- Independent output and observable trajectory evaluation when applicable.
- Fixed rubric and benchmark revisions.
- Drift audit.
- Threat model or domain-specific assurance when relevant.
- Runtime evidence and stronger isolation.

### Distributed

- Multiple runtimes, sessions, worktrees, or external teams.
- Formal handoff, consolidation, conflict handling, recovery, and audit trail.
- Cross-runtime evaluation evidence records source runtime, role, event provenance, and actual isolation.

Governance profile and runtime profile are independent selections.

## Quick-Fix Path

A quick-fix path may be used only when all of the following are true:

- the objective is unambiguous;
- implementation scope is small and bounded;
- there is no material logic, API, schema, auth, security, database, runtime,
  deployment, provider, or governance impact;
- verification is cheap and deterministic;
- output/trajectory evaluation is not required by risk or non-determinism;
- no external Hard Stop is in scope.

The quick-fix contract still requires scope, an explicit result, checks, and a
truthful closeout. It does not exempt side-effect, secret, or external-capability
rules.

## Failure Rules

When a lifecycle function fails:

- downstream state-changing functions remain blocked;
- diagnostics and corrective planning may continue;
- reporting-only closeout may continue;
- a failed or unavailable review, verification, or evaluation step must not be represented as a pass;
- a required evaluation with missing observable events remains `BLOCKED` or `UNVERIFIED`;
- implementation may resume only after the controlling local scope/process gate is reopened through
  the documented corrective loop;
- missing external capability remains unavailable regardless of project-local
  text, local gate state, test results, or evaluation scores.
