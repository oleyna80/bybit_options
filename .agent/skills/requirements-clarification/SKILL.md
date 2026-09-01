---
name: requirements-clarification
description: Resolve material specification ambiguity before technical planning without asking the Owner for repository-resolvable facts.
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

# Skill: Requirements Clarification

## Purpose

Turn an incomplete but usable specification into an implementation-ready one by
resolving only ambiguity that materially changes downstream work.

This skill is a Define-stage function. It does not approve architecture, open a
write gate, or replace the Owner.

## Inputs

- current Owner instruction/change request;
- active specification and revision;
- relevant repository evidence and accepted architecture/external contracts;
- active Work Block scope and exclusions.

## Workflow

1. Read the current specification and relevant evidence.
2. Scan for material ambiguity across:
   - outcome/scope/exclusions;
   - actors, permissions, ownership;
   - data identity/state/lifecycle;
   - alternate, error, conflict, retry and recovery behavior;
   - integrations/external contracts;
   - performance/reliability/observability/security/privacy/compliance/accessibility;
   - compatibility/migration;
   - assumptions, terminology and measurable completion signals.
3. Route every unresolved item:
   - evidence-resolvable -> answer from authoritative evidence; do not ask Owner;
   - reasonable non-material default -> record as explicit assumption;
   - material independent ambiguity -> ask in a bounded batch, normally <=3;
   - material dependent ambiguity -> ask sequentially;
   - no safe answer -> blocking ambiguity.
4. Prefer questions whose answers change behavior, architecture, data, task
   decomposition, acceptance tests, operations or risk.
5. Normally collect no more than five material Owner decisions in one pass.
   Never use the limit as permission to guess a blocker.
6. After each accepted decision, update the owning requirement, acceptance
   criterion, assumption, non-goal, risk or open-decision section. Remove stale
   contradictory wording.
7. Re-scan the affected areas and report remaining blockers.

## Question Contract

A question must state:

- the decision being requested;
- why it changes downstream work;
- a concise recommendation only when repository/project evidence supports one;
- mutually distinct options when options are useful.

Do not ask the Owner to repeat information already present in the repository or
current instruction.

## Result

Return:

- updated specification path/revision;
- evidence-resolved items;
- recorded assumptions;
- Owner decisions incorporated;
- remaining blocking ambiguities;
- status: `READY | BLOCKED | UNVERIFIED`.

`READY` means clarification is sufficient to continue Define. It does not grant
source-write authority.

## Provenance

- Classification: adapted
- Source: `github/spec-kit@bf88c9f9a82fa370c7a7257aa2b3cf10b457b65c`
- Local delta: evidence-first resolution, small batching for independent material
  questions, sequential handling only when answers are coupled, and explicit
  preservation of the Agentic SDLC authority/write-gate model.
- Novelty claim: none
