# Governance Core

This directory contains the runtime-neutral control contract for the Agentic
SDLC Framework.

The governance core answers these questions independently of Codex, Claude Code,
OpenCode, Antigravity, or any future agent runtime:

- What outcome is approved?
- Which artifacts are authoritative?
- Which role may decide, write, review, verify, evaluate, or approve?
- Which side effects require a hard stop?
- Are requirements sufficiently clarified, reviewable, and traceable before implementation?
- What deterministic, output, and observable trajectory evidence is required?
- Where did a reusable framework mechanism come from, and how was it changed locally?
- What happens when a capability, review, verification, or evaluation step is unavailable?
- When may a Work Block be declared successful?

## Normative Documents

| Document | Purpose |
|---|---|
| `authority.md` | Stable logical roles, authority boundaries, runtime/model/isolation separation |
| `lifecycle.md` | Runtime-neutral lifecycle functions, stage transitions, degraded paths |
| `artifacts.md` | Portable artifact chain, status, versioning, evidence, and SSOT rules |
| `define-quality.md` | Clarification, requirements-quality review, stable requirement/task traceability, and read-only pre-execution consistency analysis |
| `decision-provenance.md` | Adopted/adapted/experience-derived design provenance and source/attribution boundary |
| `evaluation.md` | Deterministic tests, output evaluation, observable trajectory assurance, judge limits, and verdicts |
| `runtime-capabilities.md` | Capability negotiation and topology selection |

## Boundary

Runtime-specific instructions, model names, plugins, hooks, MCP servers, CLI
commands, provider credentials, and transport mechanisms do not belong in this
directory. They belong under `runtimes/`, `integrations/`, user-level runtime
configuration, or project-local private configuration.

Requirements-quality evidence and traceability validation refine Stage 0. They do
not create a second source of truth, grant source-write authority, or replace the
Critic/Reviewer/Verifier/evaluation/drift/closeout contracts.

Evaluation governance defines observable evidence and verdict semantics. It does
not require or authorize access to private chain-of-thought, hidden reasoning,
model scratchpads, or internal deliberation.

Decision provenance records where reusable design mechanisms came from and how
they were changed locally. External sources remain research inputs rather than
authority, and provenance classification does not replace license review or
third-party attribution requirements.

## Core Principle

The SDLC manages the work. Agent runtimes execute the contracts.

A runtime may implement several logical roles in one process for low-risk work,
or distribute them across independent agents, sessions, worktrees, or machines
for higher assurance. The selected topology must preserve the authority,
artifact, evidence, evaluation, and closeout rules defined here.

## Migration Status

The runtime-neutral control plane, adapters, installation profiles, bootstrap
restore hardening, evaluation assurance, release-state assurance, and decision
provenance contract are implemented or under their separately governed changes.
`define-quality.md` adds a requirements-quality/traceability layer to Stage 0
without changing role authority or enabling external integrations.

See the accepted ADR:
`docs/architecture/decisions/2026-07-25-runtime-neutral-control-plane.md`.
