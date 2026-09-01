# Claude Code — Codex Plugin Integration

## Status

Preferred Codex-from-Claude Code integration when the Owner chooses a
same-machine, same-checkout bridge and the official plugin is available.

This adapter is optional. Generated projects do not install or enable it.

## Boundary

The official plugin delegates through the local Codex CLI and Codex app server.
It uses the same machine, checkout, local Codex authentication, and applicable
Codex configuration.

Therefore it provides a separate runtime/session, but not:

- a separate filesystem;
- a separate operating-system identity;
- a separate repository checkout;
- guaranteed network or credential isolation;
- authority beyond the active Work Block.

Record isolation as `separate-runtime-same-machine-same-checkout` unless a
stronger boundary is actually established.

## Installation

Installation is a human-operated, explicit action in Claude Code:

```text
/plugin marketplace add openai/codex-plugin-cc
/plugin install codex@openai-codex
/reload-plugins
/codex:setup
```

Codex CLI must be installed and authenticated separately. Do not commit Codex or
Claude credentials. Project-local Codex configuration is trusted-project state
and must be reviewed before use.

## Logical Function Mapping

| SDLC function | Plugin mechanism | Default authority |
|---|---|---|
| Independent Review | `/codex:review` | read-only |
| Adversarial Critic/Review | `/codex:adversarial-review` | read-only |
| Delegated investigation or bounded implementation | `/codex:rescue` | authority explicitly stated in mission brief |
| Job inspection | `/codex:status`, `/codex:result` | read-only metadata/result retrieval |
| Cancellation | `/codex:cancel` | job control only |

The plugin-installed rescue subagent is a runtime implementation detail. It does
not introduce a new governance role.

## Mission Contract

For every invocation provide:

- Work Block ID;
- logical function;
- objective;
- exact source revision or diff;
- in-scope and out-of-scope paths;
- read/write authority;
- prohibited side effects and Hard Stops;
- required evidence and output format;
- timeout/cancellation expectation;
- acceptance owner.

Example:

```text
Work Block: wb-042
Function: Reviewer
Mode: read-only
Reviewed revision: <commit-or-diff>
Scope: src/**, tests/**
Do not edit files, install dependencies, commit, push, deploy, access secrets,
or mutate runtime/data state.
Return findings, inspected and uninspected areas, evidence, residual risks, and
verdict READY | CHANGES_REQUIRED | BLOCKED | UNVERIFIED.
```

## Review and Delegation Rules

- Use review commands for read-only assurance.
- Use `/codex:rescue` for implementation only when the active Work Block grants a
  Codex Coder write-set and applicable Hard Stop approvals.
- Background jobs must be retrieved and incorporated into the Work Block before
  closeout.
- A plugin result is evidence, not automatic acceptance.
- Same-provider or same-machine independence limitations must be recorded.
- Do not claim OS-level isolation or independent credentials.

## Data and Secret Boundary

Repository content processed by Codex is sent according to the user's Codex
provider configuration. Before use, confirm that the project permits that data
boundary.

Never include:

- `.env` or secret values;
- private keys or access tokens;
- personal browser/session data;
- unrelated repository or home-directory content;
- production customer data.

## Fallback Order

When the official plugin is unavailable:

1. direct Codex runtime session with the same portable mission brief;
2. reviewed read-only Codex MCP adapter;
3. audited file handoff;
4. manual artifact exchange.

Record the chosen fallback and its limitations.

## Activation Evidence

Record at minimum:

```yaml
integration: claude-code-codex-plugin
status: available
plugin_version: observed-or-unknown
codex_cli_version: observed-or-unknown
setup_check: passed-or-blocked
runtime_boundary: separate-runtime-same-machine-same-checkout
authentication: local-codex-auth-no-secret-recorded
smoke:
  command: /codex:review
  result: passed-or-blocked
  date: YYYY-MM-DD
```

## Official References

- <https://github.com/openai/codex-plugin-cc>
- <https://developers.openai.com/codex/>
