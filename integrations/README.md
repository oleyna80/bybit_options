# Integration Adapters

## Purpose

Integration adapters connect runtimes, external tools, transports, and services
to the Agentic SDLC. They are execution mechanisms. They do not define logical
roles, authority, lifecycle, source-of-truth order, Hard Stops, or completion.

```text
Governance Core
  -> Runtime Adapter
      -> Integration Adapter
          -> External runtime, tool, service, or transport
```

Examples:

- Claude Code invoking Codex through the official plugin;
- a runtime using an MCP server;
- two runtimes exchanging a task through audited files;
- a browser, issue tracker, database inspector, or deployment tool exposed as an
  external capability.

## Integration Classes

| Class | Examples | Default posture |
|---|---|---|
| native/official bridge | Codex plugin for Claude Code | preferred when reviewed and explicitly installed |
| tool protocol | MCP server | disabled until admitted and scoped |
| audited transport | file handoff / queue | disabled until configured |
| direct process/CLI | shell invocation, SDK subprocess | exceptional; document data and permission boundary |
| hosted connector | GitHub, browser, issue tracker, monitoring | read-only or ask by default |

## Selection Order

Choose the narrowest reviewed mechanism that satisfies the Work Block:

1. native runtime capability;
2. official maintained integration;
3. reviewed MCP server;
4. audited file handoff;
5. manual or sequential artifact exchange;
6. direct shell/process bridge only when explicitly approved.

Availability does not imply permission. A lower-priority mechanism may be used
when the preferred option is unavailable, but the Work Block must record the
fallback and residual limitations.

## Admission Contract

Before activation, record:

- integration ID and class;
- objective and logical functions served;
- runtime endpoints and trust boundary;
- exact tools/actions exposed;
- read, write, network, external-directory, and secret boundaries;
- side-effect class and Hard Stops;
- data sent outside the runtime or machine;
- authentication source without secret values;
- required human approvals;
- logging, result, and audit artifacts;
- timeout, cancellation, retry, and recovery behavior;
- version and capability evidence;
- disable/rollback procedure.

Use `template/docs/templates/integration-admission-template.md`.

## Default-Deny Rules

Generated projects must not automatically:

- install plugins or packages;
- enable MCP servers;
- grant MCP or external-tool permissions;
- authenticate another runtime;
- start queue watchers or system services;
- expose secrets through committed config;
- send repository content to another provider;
- enable external-directory access;
- commit live endpoints, tokens, cookies, or private environment values.

Examples may be committed only when inert, credential-free, and clearly marked
as opt-in.

## Authority Mapping

An integration invocation must bind to a logical function:

```yaml
integration: claude-code-codex-plugin
function: reviewer
runtime_from: claude-code
runtime_to: codex
authority: read-only
isolation: same-machine-same-checkout-separate-runtime
```

The integration name or provider does not become a role. `Codex Reviewer`, `GPT
Verifier`, or `Claude Critic` are implementation descriptions, not governance
authority classes.

## Evidence Contract

Every material integration result should expose:

- Work Block ID;
- requested logical function;
- runtime and integration used;
- source revision or diff reviewed;
- scope and authority;
- start/end state;
- commands, tools, or protocol actions used at summary level;
- changed paths, if writes were allowed;
- checks and evidence;
- inspection gaps and residual risk;
- verdict or delivery status;
- session, job, or artifact identifier when available.

Do not require or store private chain-of-thought.

## Adapters

- `claude-code-codex-plugin/` — official Codex plugin used from Claude Code.
- `mcp/` — generic MCP admission and permission boundary.
- `file-handoff/` — audited runtime-neutral task transport.
- `repository-graph/` — unadmitted, provider-neutral optional local derived-state
  capability; it is not an adapter installation or provider admission.
