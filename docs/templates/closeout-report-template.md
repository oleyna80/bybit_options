# Closeout Report Template

## Closeout Report — [Work Block ID]

- **Date:** [YYYY-MM-DD]
- **Stage Execution State:** [completed]
- **Review Verdict:** [READY | CHANGES_REQUIRED | BLOCKED | UNVERIFIED | valid skip]
- **Verification Verdict:** [READY | BLOCKED | UNVERIFIED]
- **Evaluation Verdict:** [READY | BLOCKED | UNVERIFIED | NOT_REQUIRED]
- **Evaluation Plan / Report:** [paths | not required with reason]
- **Drift Verdict:** [ALIGNED | ALIGNMENT_REQUIRED | BLOCKED | UNVERIFIED | valid skip]
- **Closeout Classification:** [SUCCESS | REPORTING_ONLY]
- **Task Status:** [completed | blocked]

### Result
[Actual result compared with the expected final result.]

### Evidence
- **Frozen subject revision:** [commit/hash/version]
- **Provider-native check snapshot:** [artifact path and subject SHA | not applicable]
- **Deterministic checks:** [commands/results]
- **Output evaluation:** [criteria/results | not required]
- **Observable trajectory evaluation:** [event sources/results | not required]
- **Review / Verification / Drift:** [reports]
- **Inspection gaps:** [none | list]

Trajectory evidence references observable events only. Do not include private
chain-of-thought, hidden reasoning, model scratchpads, secrets, or protected data.
Do not copy dynamic Git commit counts, check counts, or CI counters into this
tracked report; use the SHA-bound provider snapshot artifact instead.

### Engineering Memory / Learning Review
- **Applicability:** [non-trivial learning review required | trivial with reason]
- **Lifecycle stages reviewed:** [Define, Execute, Assure, Close | not applicable with reason]
- **Material lesson candidates:** [candidate/evidence/disposition table or `none identified`]
- **Classification:** [promoted | operational-only | not-applicable]
- **Deduplication check:** [existing entries checked; updated/superseded/new | not applicable]
- **Entries Updated:** [docs/engineering-memory/* | none]
- **Promotion authority:** [target path already approved | no mutation; returned/follow-up to Define]
- **Reason:** [why reusable knowledge was or was not promoted]
- **Framework generalization:** [none | candidate only; separate framework Work Block required]

For a non-trivial Work Block, Learning Review is part of Close for both `SUCCESS`
and `REPORTING_ONLY`; it does not require a separate Owner reminder. Classification
is evidence/disposition only and never expands the Work Block write-set or other
authority. `none identified` is valid and preferable to manufacturing a lesson.

### Residual Risk
- [none | unresolved risk]

### Corrective Action or Unresolved Dependency
- [not applicable for passing required verdicts | required for BLOCKED/UNVERIFIED]

### Next Action
- [promotion/merge only for passing required verdicts | corrective Work Block/rerun]

`SUCCESS` and task status `completed` require Review and Verification to pass,
required Evaluation status/verdict `READY`, and required Drift `ALIGNED`.
`BLOCKED`, `UNVERIFIED`, or unresolved `CHANGES_REQUIRED` requires
`REPORTING_ONLY`, keeps the task blocked, and prohibits promotion, merge, deploy,
release-ready, or success claims.
