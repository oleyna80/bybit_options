---
name: spec-consistency-analysis
description: Read-only pre-execution analysis across specification, architecture/plan, task decomposition, and write-set to detect gaps and conflicts.
user-invocable: true
allowed-tools:
  - Read
  - Bash(git *)
  - Bash(ls *)
  - Bash(find *)
  - Bash(grep *)
  - Bash(cat *)
  - Bash(rg *)
  - Bash(python3 scripts/validate-define-traceability.py *)
---

# Skill: Specification Consistency Analysis

## Purpose

Before Execute, compare the approved specification with accepted architecture/
plan and task decomposition while changes are still cheap.

This function is read-only for normative artifacts. It reports inconsistencies;
it does not silently repair them.

## Inputs

- approved specification/revision;
- accepted architecture decisions and implementation plan;
- active tasklist and write-set;
- Work Block scope/exclusions;
- deterministic traceability result when the ID format is in use.

## Checks

Look for:

1. approved requirement without measurable acceptance criterion;
2. approved requirement without an implementation task;
3. unknown/stale requirement or acceptance references;
4. requirement task with no explicit write-set;
5. enabling/assurance/documentation task misrepresented as product requirement;
6. plan decision that contradicts or expands the approved specification;
7. task/write-set that implements unspecified behavior or omitted scope;
8. unresolved blocking ambiguity or assumption presented as settled fact;
9. dependency/parallelization claim inconsistent with overlapping write-sets;
10. acceptance criterion that the planned verification cannot demonstrate.

Run `scripts/validate-define-traceability.py` when the portable stable-ID format is
used. Treat the script as structural evidence only; perform semantic checks
separately.

## Mutation boundary

Do not modify the specification, architecture decision, plan, tasklist, Work
Block, or source while analyzing them.

Route remediation to the owner of the broken artifact:

- requirements gap -> clarification/specification revision;
- architecture contradiction -> architecture/plan revision;
- task coverage/dependency/write-set gap -> task decomposition revision;
- scope/authority issue -> Work Block/Owner decision.

After remediation, rerun the analysis against the new revisions.

## Result

Use exactly one:

- `READY` — no unresolved material inconsistency;
- `CHANGES_REQUIRED` — one or more owning artifacts need correction;
- `BLOCKED` — required decision/evidence is unavailable;
- `UNVERIFIED` — required artifacts could not be inspected reliably.

A `READY` consistency result is pre-execution evidence. It does not grant source
write authority and does not replace Critic review.

## Output

Return a compact matrix:

```text
Finding | Artifact owner | Evidence | Required correction
```

and the final verdict.

## Provenance

- Classification: adapted
- Source: `github/spec-kit@bf88c9f9a82fa370c7a7257aa2b3cf10b457b65c`
- Local delta: strict read-only behavior, explicit artifact ownership/remediation,
  deterministic traceability input, and preservation of the separate Critic gate.
- Novelty claim: none
