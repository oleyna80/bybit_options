# Generic Runtime Adapter

## Purpose

This adapter defines the baseline for an agent runtime with no assumed native
subagents, hooks, plugins, MCP, worktrees, or provider routing.

It demonstrates that the governance contract remains usable through sequential
or manually coordinated sessions.

## Baseline Flow

1. The active Orchestrator reads the operating contract, active Work Block, and
   approved specification.
2. The Orchestrator records scope, risks, write set, and verification plan.
3. Critic work runs in a separate read-only session when possible; otherwise it
   runs in the same context and is labeled degraded.
4. One Coder performs the approved implementation.
5. The diff revision is frozen or recorded.
6. Reviewer and Verifier work run in separate sessions when available.
7. Reports use the portable artifact contracts.
8. The Orchestrator consolidates evidence and selects successful or
   reporting-only closeout.

## Minimum Capabilities

```yaml
runtime: generic
capabilities:
  read_repository: true
  write_approved_files: conditional
  run_project_checks: conditional
  produce_markdown_reports: true
  native_subagents: false
  custom_agent_profiles: false
  hooks_or_policy_interception: false
  parallel_write: false
```

## Enforcement Limit

Without hooks, sandboxing, or an external policy layer, authority is enforced by
process, repository protections, human review, and scoped credentials. The
adapter must state this limitation explicitly and must not claim technical
isolation that does not exist.

## Interoperability Test

A conforming generic runtime can:

- read the active specification and plan;
- report its role and authority;
- modify only the named write set;
- produce Reviewer and Verifier reports with accepted verdicts;
- distinguish blocked checks from passed checks;
- close the Work Block without hidden chat history.
