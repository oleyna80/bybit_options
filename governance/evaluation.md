# Runtime-Neutral Evaluation Contract

## Purpose

Evaluation measures whether an agent-produced artifact and the observable process
used to produce it meet an approved quality bar. Evaluation is assurance evidence.
It does not grant implementation authority, tool access, integration admission,
credentials, deployment permission, or an exception to Hard Stops.

Evaluation is separate from verification:

- **tests** demonstrate deterministic behavior;
- **output evaluation** scores the delivered artifact against an approved rubric;
- **trajectory evaluation** checks observable actions and required process events;
- **verification** synthesizes all applicable evidence against acceptance criteria.

A Work Block may require evaluation in addition to review, verification, and drift.

## No Hidden-Reasoning Requirement

Trajectory evidence is limited to observable events and artifacts, including:

- tool calls and normalized tool results;
- file, diff, command, test, and gate events;
- retries, failures, recoveries, and stopping conditions;
- side-effect attempts and Hard Stop decisions;
- produced reports, logs, and evidence references;
- timestamps, runtime, role, model class, and isolation boundary when available.

Evaluation must not require or claim access to private chain-of-thought, hidden
reasoning, model scratchpads, or internal deliberation. A system may record concise
user-visible rationales or decision summaries when intentionally produced, but those
are outputs, not privileged reasoning traces.

## Evaluation Types

### Deterministic Tests

Use deterministic tests for behavior with objectively checkable inputs and outputs:

- compilation and type checks;
- unit, integration, contract, property, and regression tests;
- schema and configuration validation;
- security scanners with explicit rules;
- reproducible commands and artifact hashes.

A deterministic requirement cannot receive a passing result solely from an LM judge.
If a deterministic test cannot run, record `blocked` or `not_run`, never `pass`.

### Output Evaluation

Output evaluation checks the final artifact against an approved rubric. Examples:

- requirement coverage;
- correctness of non-deterministic responses;
- groundedness and citation quality;
- usability, maintainability, accessibility, or policy compliance;
- absence of unsupported claims;
- consistency with approved architecture and conventions.

Every scored criterion requires:

- stable criterion ID;
- description and evidence source;
- scoring method and threshold;
- weight when an aggregate score is used;
- deterministic, human, rule-based, or LM-judge evaluator type;
- result and inspection gaps.

### Observable Trajectory Evaluation

Trajectory evaluation checks whether the agent followed the approved execution
contract. It may require evidence that:

- the correct logical role and Work Block were active;
- implementation remained inside the approved write set;
- required tools or checks ran;
- prohibited tools or side effects did not run;
- failures were observed and routed into a corrective loop;
- required review, verification, or drift evidence was produced;
- Hard Stops blocked unauthorized consequential actions;
- completion claims match the actual observable state.

Trajectory evaluation must not infer a pass from a fluent final response when required
observable events are absent.

## Evaluation Plan

When evaluation is required, an approved plan must identify:

- evaluation ID and Work Block;
- subject objective, specification revision, and frozen revision/diff;
- deterministic checks and expected evidence;
- output criteria and thresholds;
- trajectory requirements and event sources;
- benchmark or dataset revision where applicable;
- judge policy and permitted evaluator types;
- isolation and runtime assumptions;
- blocking conditions and aggregate verdict rule.

The plan must be approved before it is used as closeout evidence. Changing criteria,
weights, thresholds, datasets, or required trajectory events after observing results is
a plan revision and must be recorded.

## Evaluation Evidence

Evidence must be attributable and reproducible enough for the selected governance
profile. Record:

- exact subject revision;
- plan/rubric revision;
- commands, datasets, fixtures, event logs, and artifacts used;
- evaluator identity and version;
- runtime, model class, actual model when policy permits, and isolation boundary;
- per-check result matrix;
- retries and blocked checks;
- aggregate calculation;
- residual risks and inspection gaps.

Raw operational logs are evidence inputs, not authority. Sensitive values and secrets
must be redacted or referenced through protected storage.

## LM Judge Rules

An LM judge is allowed only when the plan defines a rubric for a genuinely
non-deterministic criterion.

Required controls:

- record judge provider/model or stable judge class according to disclosure policy;
- record judge prompt/rubric revision;
- use fixed examples or calibration cases when material;
- record temperature or reproducibility controls when available;
- separate judge output from deterministic evidence;
- report disagreement, instability, and inspection gaps;
- require human or deterministic confirmation for high-impact borderline results.

An LM judge cannot by itself:

- prove deterministic correctness;
- waive a failing test;
- approve architecture or product scope;
- open a write, integration, deployment, or Hard Stop gate;
- convert `BLOCKED` or `UNVERIFIED` evidence into `READY`.

## Result States and Verdicts

Per-check states:

- `pass` — required evidence demonstrates the criterion;
- `fail` — evidence demonstrates non-conformance;
- `blocked` — a required dependency or environment was unavailable;
- `not_run` — the check was not executed and no pass claim is allowed;
- `not_applicable` — explicitly excluded by the approved plan.

Evaluation verdicts:

- `READY` — every blocking requirement passed and thresholds were met;
- `BLOCKED` — one or more blocking checks failed or a required dependency blocked;
- `UNVERIFIED` — evidence is missing, unreliable, inconsistent, or insufficient.

There is no `CHANGES_REQUIRED` evaluation verdict. Corrective action returns to the
appropriate lifecycle stage and the evaluation is rerun against a recorded revision.

## Work Block Binding

The active Work Block evaluation state records:

```json
{
  "required": true,
  "status": "PENDING",
  "verdict": "PENDING",
  "plan": "docs/evals/example/plan.json",
  "report": "docs/reports/evaluations/example.md",
  "rubric_revision": "1",
  "benchmark_revision": "dataset-v1",
  "isolation": "unknown",
  "skip_reason": ""
}
```

Allowed status values are `PENDING`, `READY`, `SKIPPED`, `DEGRADED`, and
`BLOCKED`.

- Required evaluation cannot be `SKIPPED`.
- Optional skipped evaluation requires a non-empty reason.
- `READY`, `DEGRADED`, and `BLOCKED` require a non-empty report under
  `docs/reports/` and an actual isolation boundary.
- `READY` status requires verdict `READY`.
- Successful closeout requires required evaluation status/verdict `READY`.
- Reporting-only closeout may record `BLOCKED` or `UNVERIFIED`, but cannot claim
  merge-ready, deploy-ready, release-ready, or completed status.

## Governance Profile Guidance

- **Advisory:** evaluation is normally optional and read-only.
- **Controlled:** deterministic tests are required when applicable; focused output or
  trajectory evaluation may be selected by risk.
- **Managed:** evaluation plan and regression evidence are required for agent behavior,
  non-deterministic outputs, or consequential automation.
- **Assured:** independent output and trajectory evaluation, fixed rubric/benchmark
  revisions, and stronger isolation are required when applicable.
- **Distributed:** event-source provenance, cross-runtime handoff evidence, and
  consolidation rules are required.

The Work Block must state why evaluation is required or not required. Risk and
non-determinism, not the presence of a particular runtime or model, determine the need.

## Failure Rules

- Missing required evidence fails closed.
- A required failed or blocked check prevents verdict `READY`.
- An evaluator must not mark unavailable checks as passed.
- A changed subject revision invalidates prior evaluation until applicability is
  re-established.
- A changed rubric, threshold, dataset, judge policy, or trajectory requirement creates
  a new evaluation revision.
- Evidence from a runtime that cannot expose required observable events must be marked
  degraded or unverified; simulated independence must not be claimed as real isolation.
