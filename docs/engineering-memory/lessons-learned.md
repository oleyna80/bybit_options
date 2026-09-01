---
schema_version: 1
artifact_type: engineering_memory
artifact_id: lessons-learned
status: active
owner_role: orchestrator
last_verified: null
authority: lower_than_current_owner_governance_spec_and_active_work_block
review_trigger: new_evidence_supersedes_a_recorded_lesson_or_a_recurring_pattern_is_confirmed
---

# Lessons Learned

This project-local log records concise, evidence-backed engineering lessons from
completed or materially revised Work Blocks. It stores reusable principles, not
raw chat history or routine status chronology.

Framework example/history lessons are intentionally **not** copied into new
projects. Add only lessons evidenced by this project.

## Promotion Filter

A lesson belongs here only when it can materially change future planning,
execution strategy, review, verification, recovery, or invariant enforcement.
Common candidates include recurring failure/recovery patterns, durable
invariants, source-of-truth lessons, lifecycle/process defects, verification
gaps, reusable operational patterns, and rejected approaches with important
evidence-backed reasons.

Do not add one-off noise, speculation, raw transcripts, private chain-of-thought,
secrets/private data, routine status history, or facts cheaper to re-verify from
the current tree.

Before adding an entry, search existing Engineering Memory for the same reusable
principle. Prefer updating, extending, confirming, or explicitly superseding an
existing lesson instead of creating a duplicate.

## Entry Shape

```text
## LL-XXX — Short title

Status:
Scope:
Evidence:
Last verified:

### Why this matters

### What evidence changed the decision

### Replacement / mitigation / recovery

### Reusable principle

### Authority boundary

### Review trigger
```

A lesson never overrides current Owner instruction, governance, an approved
specification/architecture decision, or the active Work Block. Classification is
not permission: this file may be mutated only when its path is already authorized
by the current Work Block.

Project-specific lessons remain project-local. A possible generalization into
the Agentic SDLC Framework requires a separate evidence-backed framework Work
Block; there is no automatic project-to-framework promotion.

<!-- Add project lessons below this line. -->
