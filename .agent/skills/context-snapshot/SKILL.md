---
name: context-snapshot
description: "Freeze system state before parallel subagent spawning, Workflow tool runs, or stage transitions with incomplete subagent tasks. Captures memory bank, file state, agent topology, constraints, and recovery plan. Snapshot is read-only for subagents — only Control Tower creates and archives. Triggers: 2+ parallel subagents, Workflow tool launch, stage transition with pending subagents, session resume."
user-invocable: true
argument-hint: "[work-block-id] [stage] [purpose: parallel|recovery|handoff|transition]"
allowed-tools:
  - Read
  - Bash(git *)
  - Bash(ls *)
  - Bash(find *)
  - Bash(cat *)
  - Bash(date *)
---

# Skill: Context Snapshot

## Purpose

Freeze the current system state before non-trivial parallel work. Ensures all
subagents receive a consistent view of the project state — preventing
contradictory decisions from desynchronized context.

## When to Use (Triggers)

Control Tower MUST create a snapshot when:

- **Spawning 2+ parallel subagents** — each agent receives the same baseline
- **Launching a Workflow tool run** — parallel/pipeline stages need shared context
- **Stage transition with pending subagent tasks** — e.g., Stage 1→2 while a reviewer is still running
- **Resuming session after interruption** — capture what changed during the break

Skip when:
- Single subagent, sequential execution
- Trivial Work Block (at most 2 planned implementation files, lifecycle
  evidence excluded, no logic/route/schema/API/security/governance impact)

## When NOT to Use

- Single subagent dispatch
- Sequential stage execution with no overlap
- Trivial fixes with no parallelism

## Workflow

1. **Verify state** — confirm write gate status, git status, active agents
2. **Collect memory bank** — read context.md, progress.md, decisions.md, orchestrator-log.md
3. **Collect file state** — `git status --porcelain`, recent files (`git log --diff-filter=A --since="5 days ago" --name-only`)
4. **Map isolation zones** — for each parallel agent: which files it owns vs. shares
5. **Define constraints** — files not to touch, decisions not to reconsider, hard stops
6. **Define recovery plan** — per-agent timeout, conflict resolution, stale snapshot action
7. **Write snapshot** — `memory_bank/snapshots/snapshot-[wb-id]-[stage]-[date].md`
8. **Reference in mission briefs** — add snapshot path to each subagent's "Inputs / Files to Read"

## Snapshot Naming

```
memory_bank/snapshots/snapshot-[wb-id]-[stage]-[YYYY-MM-DD].md
```

Examples:
- `snapshot-wb-003-stage0-2026-06-12.md` — Stage 0 pre-parallel
- `snapshot-wb-003-pre-parallel-2026-06-12.md` — before parallel review
- `snapshot-wb-004-recovery-2026-06-12.md` — session resume

## What Subagents Do With Snapshots

- **Read** the snapshot to understand the frozen state
- **Reference** it when reporting findings (use snapshot ID for traceability)
- **Do NOT modify** the snapshot — read-only for subagents
- **Flag staleness** — if they detect the snapshot is outdated, report to Control Tower

## Snapshot Lifecycle

1. **Create** — before parallel dispatch
2. **Reference** — in each subagent's mission brief
3. **Archive** — after all parallel agents complete (move to `memory_bank/snapshots/archive/` or keep in place)
4. **Never delete** — snapshots are part of the audit trail

## Constraints

- **Control Tower only** — subagents never create or modify snapshots
- **Read-only for subagents** — enforced by convention (subagents have no write access to memory_bank)
- **Immutable after creation** — do not edit a snapshot once subagents are dispatched
- **Part of audit trail** — snapshots persist alongside orchestrator-log.md
- **No secrets** — never capture `.env` values, tokens, or credentials in snapshots

## Template

Use `docs/templates/snapshot-template.md` for the full structure. Key sections:

1. Current state (WB, stage, side-effect class, DB mode, write gate)
2. Agent topology (who runs, isolation zones, shared reads)
3. Memory bank state (summary of each file)
4. File state (git status, recent files)
5. Constraints (don't touch, don't reconsider, hard stops)
6. Recovery plan (hang, conflict, staleness)

## Relationship with Other Skills

| Skill | Relationship |
|---|---|
| `subagent-mission-brief` | Snapshot path is included in mission brief's Inputs section |
| `ssot-sync-closeout` | Snapshot provides the "before" state for sync verification |
| `orchestrator-log` | Log snapshot creation in orchestrator-log.md |
| `critic-review` | Critic reads the snapshot to understand pre-dispatch state |

## Handoff

- **Success condition:** snapshot written to `memory_bank/snapshots/`, referenced in all parallel mission briefs
- **Next:** proceed with parallel dispatch
- **Auto-proceed:** YES — snapshot is a pre-dispatch step, not a gate
- **Hard stop:** NO
