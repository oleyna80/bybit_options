# Specification Drift Report

## Metadata

- **Work Block ID:** [wb-xxx]
- **Date:** [YYYY-MM-DD]
- **Auditor role:** [Drift Auditor | Reviewer specialization | Verifier specialization]
- **Runtime:** [codex | claude-code | opencode | generic | other]
- **Isolation:** [same-context | separate-subagent | separate-session | separate-worktree | separate-runtime | os-isolated]
- **Specification:** [path]
- **Specification revision:** [commit/hash/version]
- **Implementation baseline:** [commit/diff/reference]
- **Verdict:** [ALIGNED | ALIGNMENT_REQUIRED | BLOCKED | UNVERIFIED]

## Inputs Inspected

| Artifact | Reference | Status | Notes |
|---|---|---|---|
| Work Block | [path] | inspected | |
| Specification | [path] | inspected | |
| Architecture decisions | [paths] | inspected / not applicable | |
| Implementation plan | [path] | inspected | |
| Implementation diff | [reference] | inspected | |
| Review report | [path] | inspected / unavailable | |
| Verification report | [path] | inspected / unavailable | |
| Documentation | [paths] | inspected / not applicable | |

## Alignment Matrix

| Requirement / Contract | Spec Evidence | Implementation Evidence | Test / Runtime Evidence | Documentation Evidence | Classification |
|---|---|---|---|---|---|
| [REQ-001] | [section] | [file:symbol] | [test/report] | [doc/path] | ALIGNED |

Allowed classifications:

- `ALIGNED`
- `MISSING_IMPLEMENTATION`
- `UNSPECIFIED_IMPLEMENTATION`
- `STALE_PLAN`
- `STALE_TEST`
- `STALE_DOCUMENTATION`
- `SPEC_CHANGE_REQUIRED`
- `INSPECTION_GAP`

## Unspecified Delivered Behavior

- [Behavior introduced without approved specification, or `none`]

## Missing Approved Behavior

- [Requirement not implemented, or `none`]

## Derived Artifact Drift

### Plan

- [Outdated or contradictory plan items, or `none`]

### Tests and Verification

- [Missing or stale evidence, or `none`]

### Documentation

- [Stale user or engineering documentation, or `none`]

## Required Corrections

| Priority | Classification | Required action | Owner role | Re-audit required |
|---|---|---|---|---|
| [P0/P1/P2] | [classification] | [action] | [role] | [yes/no] |

## Inspection Gaps

- [Artifact, environment, route, or evidence that could not be checked and why]

## Residual Risks

- [Known risk that remains after the audit]

## Closeout Decision

- **Drift gate:** [READY | BLOCKED | UNVERIFIED]
- **Successful closeout allowed:** [yes only when verdict is ALIGNED]
- **Next action:** [closeout | update derived artifact | change specification | corrective implementation | obtain missing evidence]
