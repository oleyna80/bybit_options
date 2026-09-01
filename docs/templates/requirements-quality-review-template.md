---
schema_version: 1
artifact_type: requirements_quality_review
work_block_id: [WORK_BLOCK_ID]
specification: [SPECIFICATION_PATH_OR_ID]
specification_revision: [SPECIFICATION_REVISION]
reviewer_role: reviewer
isolation: [ISOLATION]
verdict: pending
---

# Requirements Quality Review — [TITLE]

## Subject

- Specification: `[SPECIFICATION_PATH_OR_ID]`
- Revision: `[SPECIFICATION_REVISION]`
- Work Block: `[WORK_BLOCK_ID]`
- Review boundary: written requirements only; implementation behavior is out of scope

## Result Matrix

| Dimension | Status | Evidence / references | Finding |
|---|---|---|---|
| Scope and exclusions | pending | | |
| Actors / permissions / ownership | pending | | |
| Requirement completeness | pending | | |
| Clarity / ambiguity | pending | | |
| Internal consistency | pending | | |
| Acceptance measurability | pending | | |
| Alternate / failure / recovery coverage | pending | | |
| Security / privacy / operational coverage | pending | | |
| Assumptions / dependencies | pending | | |
| Requirement / acceptance traceability | pending | | |

Use `READY`, `CHANGES_REQUIRED`, `BLOCKED`, or `UNVERIFIED` for material row status.

## Findings

### RQ-001 — [SHORT_TITLE]

- Severity: `blocking | material | advisory`
- Requirement/section: `[REFERENCE]`
- Quality dimension: `[DIMENSION]`
- Finding: [PRECISE_REQUIREMENTS_GAP]
- Why it matters: [DOWNSTREAM_IMPACT]
- Owning remediation: `clarification | specification | architecture | Owner`

## Remaining Owner Decisions

- [NONE_OR_DECISION]

## Inspection Gaps

- [NONE_OR_GAP]

## Verdict

`READY | CHANGES_REQUIRED | BLOCKED | UNVERIFIED`

This verdict is Define-stage evidence only. It does not grant source-write authority
or replace Critic, Reviewer-on-diff, Verifier, evaluation, drift, or Hard Stops.
