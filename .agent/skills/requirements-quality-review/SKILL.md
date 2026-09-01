---
name: requirements-quality-review
description: Read-only review of specification completeness, clarity, consistency, measurability, scenario coverage, assumptions, and traceability before implementation.
user-invocable: true
allowed-tools:
  - Read
  - Bash(git *)
  - Bash(ls *)
  - Bash(find *)
  - Bash(grep *)
  - Bash(cat *)
  - Bash(rg *)
---

# Skill: Requirements Quality Review

## Purpose

Review the **written requirements** before implementation. This is not code
review, runtime verification, or a test plan.

For Managed/Assured/Distributed formal specification work, run after
clarification and before Critic/write-gate completion.

## Review dimensions

Evaluate, when relevant:

- scope and exclusions are explicit;
- actors, permissions and ownership are unambiguous;
- required behavior is complete enough to implement without inventing product
  policy;
- requirements are internally consistent;
- vague language is quantified where objective verification requires it;
- acceptance criteria are measurable and map to required behavior;
- alternate/error/conflict/retry/recovery cases are covered when material;
- security/privacy/compliance/accessibility/operational requirements are present
  when the domain requires them;
- assumptions and external dependencies are explicit;
- requirement/acceptance identifiers are stable when traceability is required;
- unresolved decisions are visible and correctly blocking/non-blocking.

## Ownership

Preferred authority is read-only Reviewer/requirements-review specialization.
The specification author may self-check, but self-check evidence must not be
represented as independent review.

The review may write only its approved report artifact. It must not silently
edit the specification while evaluating it.

## Findings

Each material finding records:

- severity: `blocking | material | advisory`;
- requirement/section reference;
- quality dimension;
- precise gap or contradiction;
- why it matters for implementation/verification;
- owning remediation path: clarification/specification/architecture/Owner.

Do not turn implementation checks into requirements-quality findings. For
example, ask whether failure behavior is specified; do not claim that the code
already handles or fails to handle it.

## Verdict

Use exactly one:

- `READY`
- `CHANGES_REQUIRED`
- `BLOCKED`
- `UNVERIFIED`

`READY` is Define-stage evidence only. It cannot grant source-write authority or
replace Critic, Verifier, evaluation, drift audit, or Hard Stops.

## Output

Use `docs/templates/requirements-quality-review-template.md` and store the report
under the active Work Block's approved evidence path, normally
`docs/reports/requirements/<work-block-id>.md`.

## Provenance

- Classification: adapted
- Source: `github/spec-kit@bf88c9f9a82fa370c7a7257aa2b3cf10b457b65c`
- Local delta: reviewer-owned read-only gate, Agentic SDLC verdict/authority
  semantics, and explicit separation from implementation verification.
- Novelty claim: none
