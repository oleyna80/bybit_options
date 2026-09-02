# Agent workflows

The canonical lifecycle workflow is:

- `.agent/workflows/sdd-protocol.md` — **normative** Define → Execute → Assure → Close contract.

The following project workflow is retained as legacy product/backend context:

- `.agent/workflows/bybit_options_workflow.md` — **legacy / non-authoritative** runtime and code-flow snapshot.

When the two disagree on permissions, roles, gates, source of truth, or lifecycle,
follow the current Owner instruction, `AGENTS.md`, `governance/`, the active Work
Block, and `sdd-protocol.md`. A workflow document never grants production, live
DB, secret, destructive Git, protected/default-branch, deployment, or live
trading authority.
