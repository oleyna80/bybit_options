# Engineering Memory

This directory stores durable project engineering memory that future humans and
agents should be able to trust without reading old chat history.

The framework also installs `engineering-decision-principles.md` as a baseline
reference linked from `AGENTS.md`. It is framework guidance, not evidence that a
project-specific decision has already been made.

## What Belongs Here

- Architecture, runtime, integration, delivery, and lifecycle decisions that affect future Work Blocks.
- Source-of-truth chains for important project questions.
- Temporary exceptions with expiry or review triggers.
- Reproducible setup, verification, and recovery procedures.
- Recurring failure patterns with evidence and future checks.
- Evidence-backed lessons from rejected/retired approaches that should change future engineering decisions.
- Decision rationale and lessons that should not inflate the always-on `AGENTS.md` contract.

A lesson is durable when it can materially change future planning, execution
strategy, review, verification, recovery, or invariant enforcement. Do not
promote an observation merely because it happened during a Work Block.

## What Does Not Belong Here

- Secrets, tokens, credentials, private keys, `.env` values, or unredacted client data.
- Raw transcripts or private chain-of-thought.
- One-off task noise or routine status chronology.
- Speculative observations without evidence.
- Code facts that are easy/cheaper to verify from the current tree.
- Git history that belongs in `git log`.
- Runtime-specific local memory from `.claude/agent-memory/`, `.codex/`, OpenCode, Antigravity, or local IDE state.

## Authority

Use this directory after current higher-authority task/spec/plan/report files and
before operational logs:

```text
current Owner instruction
AGENTS.md and accepted governance
approved specification and architecture decisions
approved Work Block / write-set
docs/tasklist, docs/plans, docs/reports
docs/engineering-memory
memory_bank and runtime logs
generated or external artifacts
```

If an entry here conflicts with current source files or an approved Work Block,
verify the current state and update, supersede, or retire the entry during
closeout.

Engineering Memory classification is a disposition, not a permission grant. A
promotion may modify only a memory path already authorized by the active Work
Block; otherwise return to Define.

## Files

- `engineering-decision-principles.md` - framework baseline for proportional, simple, evidence-driven engineering decisions.
- `lessons-learned.md` - project-local reusable lessons from completed or materially revised Work Blocks.
- `decision-record-template.md` - copy this shape for durable engineering decisions.
- `source-of-truth-chains.md` - map important questions to their highest authority.
- `temporary-decisions.md` - track time-boxed exceptions and revisit triggers.
- `reproducibility-log.md` - stable commands and evidence needed by future agents.

## Durable Lesson Shape

A promoted lesson should identify, as applicable:

```text
Decision, invariant, or lesson:
Status:
Scope:
Why this matters:
Evidence:
Reusable principle:
Replacement / mitigation / recovery:
Source-of-truth chain:
Authority boundary:
Temporary until / review trigger:
Last verified:
```

Before creating a new entry, search this directory for the same reusable
principle and update/extend/supersede the existing entry when appropriate.

## Closeout Rule

At the end of every non-trivial Work Block, including reporting-only closeout,
the Orchestrator MUST review material findings from **Define, Execute, Assure,
and Close**. No separate Owner reminder to "record the lesson" is required once
the Work Block/write authority is approved.

Classify reusable knowledge exactly as:

- `promoted`: update an already-authorized path in this directory.
- `operational-only`: keep it in `memory_bank/` or reports.
- `not-applicable`: no reusable durable memory was created.

Common candidates include recurring failure/recovery patterns, durable
invariants, source-of-truth lessons, lifecycle/process defects, verification
gaps, reusable operational patterns, and rejected approaches with important
evidence-backed reasons. `none identified` is valid; do not manufacture lessons.

## Project-to-Framework Boundary

Lessons in this directory are project-specific by default. Repetition or
successful generalization may create a candidate framework improvement, but it
must not automatically update framework governance, skills, or templates. Such a
promotion requires a separate evidence-backed framework Work Block with its own
Owner-approved scope and assurance.
