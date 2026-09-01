# File Handoff Integration Adapter

## Purpose

File handoff is an audited transport for exchanging bounded tasks and results
between runtimes, sessions, machines, or users when direct integration is
unavailable, undesirable, or insufficiently observable.

It is direction-neutral:

```text
runtime A -> portable task envelope -> runner/manual transport -> runtime B
runtime B -> result envelope + logs/evidence -> runtime A
```

The current `handoff/runner/` implementation invokes Claude Code and is retained
as a compatibility transport. The public task contract is runtime-neutral.

## Appropriate Uses

- different machines or operating-system identities;
- long-running or recoverable jobs;
- observable queue and result state;
- strict scope audit around an external runtime;
- runtimes without native plugins or MCP support;
- explicit human review between task creation and execution;
- fallback after a preferred integration is unavailable.

Do not use file handoff merely to bypass runtime permissions, hooks, or Owner
approval.

## Portable Task Envelope

Use `handoff/templates/runtime-task-template.md`.

Required concepts:

- task and Work Block IDs;
- source and target runtime identifiers;
- logical function, not provider-named role;
- project root and source revision;
- objective and acceptance criteria;
- authority and side-effect class;
- allowed and forbidden scope;
- input artifacts;
- required checks and result contract;
- Hard Stops and approval evidence;
- timeout, cancellation, retry, and recovery;
- data/secret boundary;
- expected evidence and result destination.

## Result Envelope

A result must report:

- `DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED | FAILED`;
- source revision inspected and resulting revision if changed;
- actions taken at summary level;
- changed paths;
- checks and outcomes;
- review/verification/drift verdict when applicable;
- scope-audit result;
- inspection gaps and residual risks;
- session/job/log/result identifiers;
- suggested next action.

Do not return hidden reasoning or private chain-of-thought.

## Scope and Mutation Policy

- One write-capable executor per write-set.
- `allowed_scope` is required for state-changing tasks.
- `forbidden_scope` is evaluated before build-artifact exclusions.
- Secrets, credentials, `.env*`, private keys, and unrelated home-directory
  content are forbidden by default.
- Runner-owned volatile files must be distinguished from project files.
- A runtime's internal logs or memory are allowed only when explicitly included.
- Scope-audit failure blocks acceptance even when the runtime reports success.

## Concurrency

Parallel tasks require:

- non-overlapping project roots or separate worktrees;
- non-overlapping write-sets;
- bounded concurrency;
- one consolidation owner;
- review and verification of the consolidated result.

Sharing one mutable project root is denied by default.

## Recovery

The transport must define:

- atomic queue publication;
- active-job identification;
- lock ownership;
- stale-job recovery;
- timeout and cancellation;
- result and log retention;
- failed-task quarantine;
- idempotency or duplicate-task handling.

A recovered or retried task must not silently reuse stale approvals or an old
source revision.

## Compatibility Runner

`handoff/runner/handoff-runner.sh` currently executes Claude Code. Treat it as:

```yaml
integration: file-handoff
transport_implementation: claude-code-runner
status: compatibility
```

The runner may remain Claude-specific internally while the task/result envelope
and governance binding stay portable. Future runners may target Codex, OpenCode,
or other runtimes without changing the envelope.

## Activation

Do not enable watchers or systemd services automatically. A human must review:

- runner command and runtime binary;
- environment allowlist;
- project roots;
- scope-audit behavior;
- concurrency limits;
- logs and retention;
- service identity and permissions;
- shutdown and uninstall steps.

## Verification

Minimum smoke:

1. submit an atomic read-only task;
2. verify task movement through queue/active/done or failed;
3. verify status and result schema;
4. run an allowed-scope write fixture in a disposable project;
5. run an out-of-scope fixture and confirm `scope_failed`;
6. verify `.env` and secret paths remain inaccessible;
7. verify stale active-task recovery;
8. record runtime version and transport limitations.
