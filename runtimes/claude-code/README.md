# Claude Code Runtime Adapter

## Purpose

This adapter maps Claude Code capabilities to the runtime-neutral Agentic SDLC
contract. It implements shared governance; it does not redefine authority,
source-of-truth order, lifecycle gates, external Hard Stops, or completion.

Generated Claude-capable projects use a thin `CLAUDE.md` whose first instruction
is:

```text
@AGENTS.md
```

Claude Code therefore receives the canonical portable project contract from
`AGENTS.md`. `CLAUDE.md` contains only Claude-specific routing notes. Shared rules
must not be copied into both files.

This follows current Claude Code guidance for repositories that already use
`AGENTS.md`; see <https://code.claude.com/docs/en/memory>.

## Installed project surface

```text
CLAUDE.md                    # thin @AGENTS.md import shim
.claude/
├── settings.json
├── agents/
│   ├── solution-architect.md
│   ├── critic.md
│   ├── reviewer.md
│   ├── scoped-coder.md
│   └── verifier.md
├── hooks/
│   ├── assurance_gate.py
│   ├── critic-gate.sh
│   ├── hard-stop.sh
│   ├── typecheck.sh
│   ├── verification-gate.sh
│   └── work_block_gate.py
├── skills/
└── agent-memory/
```

When the optional `integration:mcp-config` component is installed, `.mcp.json`
is present and empty/inert by default. The `claude-code` profile itself does not
enable an MCP integration automatically. No plugin, MCP server, external runtime,
credential, watcher, or service is enabled automatically.

## Session bootstrap

1. Claude Code loads `CLAUDE.md`, which imports `AGENTS.md`.
2. Follow the progressive read strategy in `AGENTS.md` and
   `docs/session-bootstrap.md`.
3. Inspect `.agent/bootstrap-profile.json` when runtime/tool availability matters.
4. Identify the active Work Block, approved write-set, and required assurance.
5. Inspect actual Claude Code permissions, hooks, agents, plugins, MCP state, and
   isolation before relying on a capability.

Do not manually duplicate shared project policy in `CLAUDE.md` to make it more
visible. If a rule is cross-runtime, change its canonical shared source. If it is
a reusable procedure, route it to a skill/workflow. Keep only Claude-specific
mechanics here or under `.claude/`.

## Logical role mapping

| Logical role | Claude Code implementation | Default authority |
|---|---|---|
| Orchestrator | Main Claude Code session | workflow/coordination artifacts |
| Architect | `.claude/agents/solution-architect.md` | read-only plus approved drafts |
| Critic | `.claude/agents/critic.md` | read-only |
| Coder | `.claude/agents/scoped-coder.md` | approved write-set only |
| Reviewer | `.claude/agents/reviewer.md` | read-only |
| Verifier | `.claude/agents/verifier.md` | read-only plus approved reports |

Runtime agent names do not create new authority classes. The active shared
contract and Work Block determine authority.

## Hooks and permissions

Project hooks provide cooperative guardrails for consequential Bash operations,
Work Block/write-set checks, staged commit scope, targeted post-edit checks, and
assurance state. They are not an operating-system security boundary.

Effective permissions may combine user, enterprise, CLI, and project settings.
Inspect current runtime state rather than assuming the checked-in configuration
is the whole permission model.

If a required hook or permission boundary is unavailable:

- record the capability as degraded/unverified;
- use a narrower permission mode, separate worktree/session/runtime, or manual
  approval as appropriate;
- do not infer external authority from a Claude Code permission prompt.

Shared consequential-operation policy is defined outside this adapter by
`AGENTS.md`, governance, the active Work Block, and external repository/OS/
credential controls.

## Skills and memory

Portable skills are available through the generated skill surfaces selected by
the installation profile. Skills provide procedures, never scope or authority.

`.claude/agent-memory/` is runtime-local operational memory. It must not replace
approved specifications, Work Blocks, evidence, or durable engineering memory.
Promote reusable evidence-backed knowledge to `docs/engineering-memory/` through
normal closeout.

Do not store secrets, credentials, personal data, protected payloads, or hidden
reasoning in agent memory.

## Integrations

External plugins, MCP servers, Codex/OpenCode bridges, browser tools, and vendor
CLIs are integration capabilities, not governance roles. They require the
admission and Work Block binding defined by the shared framework.

Preferred Codex-from-Claude routes remain documented under:

- `integrations/claude-code-codex-plugin/`;
- `integrations/mcp/`;
- `integrations/file-handoff/`.

Availability never implies activation or permission.

## Capability snapshot

Record observed runtime evidence rather than assumptions. A typical snapshot may
include:

```yaml
runtime: claude-code
capabilities:
  project_instructions: observed
  custom_subagents: observed
  project_hooks: observed
  per_agent_tool_policy: observed
  plugins: unknown_until_inspected
  mcp: unknown_until_inspected
  os_isolation: false_unless_separately_configured
  production_authority: unavailable_by_design
```

Replace placeholders with actual version/config/smoke evidence when a Work Block
depends on the capability.

## Assurance and degraded mode

For low-risk work, separate Claude Code passes may be sufficient when the active
governance profile permits them. Stronger independence may require a separate
session, worktree, runtime, container, machine, account, or human review.

A different model name alone does not establish independence. Report actual
isolation and evidence limitations.

## Validation

After bootstrap or Claude Code runtime/configuration updates, verify as
applicable:

- generated `CLAUDE.md` still imports `@AGENTS.md` and remains a thin shim;
- `.claude/settings.json` parses;
- only expected logical-role agents are present;
- harmless hook fixtures behave as documented;
- scope/write-set guards match the active Work Block contract;
- selected integrations remain inactive unless explicitly admitted;
- no committed secret values were introduced;
- current runtime version and inspection gaps are recorded when material.

Use Claude Code `/memory` to inspect loaded instruction files and `/doctor` for
configuration diagnostics when available. These diagnostics provide evidence;
they do not alter framework authority.

## References

- Claude Code project memory and `AGENTS.md` import guidance:
  <https://code.claude.com/docs/en/memory>
- Claude Code configuration diagnostics:
  <https://code.claude.com/docs/en/debug-your-config>
- Shared project contract: `AGENTS.md`
