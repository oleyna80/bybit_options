# Runtime Adapters

Runtime adapters explain how a specific agent system implements the normative
contracts in `governance/`.

A runtime is the environment executing a logical function. An integration is an
optional bridge, tool protocol, hosted capability, process boundary, or
transport used by a runtime.

```text
Governance Core
  -> Runtime Adapter
      -> Integration Adapter (optional)
```

## Adapter Responsibilities

A runtime adapter may define:

- native agent and subagent configuration;
- project instructions and runtime entry points;
- runtime-specific skills, commands, hooks, and permissions;
- capability and limitation maps;
- model-routing examples without credentials;
- sandbox and isolation mechanisms;
- target-environment smoke tests;
- mappings from logical roles to runtime agents;
- supported integration mechanisms and degraded fallback.

A runtime adapter may not:

- redefine core authority or source-of-truth order;
- weaken Hard Stops;
- silently change artifact/gate verdict semantics;
- treat a model/provider/runtime as inherently authoritative;
- represent an unavailable check as passed;
- grant write or side-effect permission because a tool exists;
- automatically activate an external integration;
- claim stronger isolation than the observed runtime boundary.

## Current Adapters

| Adapter | Status | Purpose |
|---|---|---|
| `codex/` | implemented baseline | Project agents, machine write gate, shared Hard Stops, Codex wrappers, capability limits |
| `claude-code/` | implemented baseline | Logical-role agents, machine source/assurance gates, skills, memory, opt-in integrations |
| `opencode/` | implemented / smoke required | Project instructions, logical-role subagents, explicit permissions, inert plugin/MCP state |
| `generic/` | portable baseline | Sequential/manual execution without native orchestration assumptions |

## Integration Boundary

Integration adapters live under `integrations/`:

- `claude-code-codex-plugin/` — optional official bridge from Claude Code to
  local Codex;
- `mcp/` — MCP server and exact-tool admission;
- `file-handoff/` — audited runtime-neutral task/result transport.

The current `handoff/runner/` implementation targets Claude Code and is retained
as a compatibility transport. Its public task envelope is runtime-neutral.

A runtime's support for plugins, MCP, subprocesses, connectors, browser tools, or
hosted services is only a capability. Activation requires an integration
admission record and active Work Block binding.

## Selection

For each Work Block record separately:

```yaml
governance_profile: Managed
runtime_profile: claude-code
integration_profile: claude-code-codex-plugin
model_class: balanced_engineering
isolation: separate-runtime-same-machine-same-checkout
```

Choose the narrowest reviewed execution path:

1. native runtime capability;
2. official maintained integration;
3. reviewed MCP server/tool;
4. audited file handoff;
5. manual artifact exchange;
6. direct CLI/process only as an explicitly admitted exception.

Availability never implies permission.

## Capability Evidence

Before relying on an adapter, record:

- runtime/version/provider/model when observable;
- instructions and agent discovery;
- effective permissions and hook state;
- subagent/session/worktree behavior;
- plugin/MCP inventory;
- data, secret, network, and external-directory boundaries;
- allowed and denied smoke fixtures;
- actual isolation and shared resources;
- limitations and fallback.

Unknown capability remains `unknown` or `unverified`, not `available`.
