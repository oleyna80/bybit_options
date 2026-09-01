# OpenCode Runtime Adapter

## Status

Implemented generated-project baseline for project instructions, logical-role
subagents, explicit permissions, and opt-in plugins/MCP.

Target-environment smoke evidence is still required before using OpenCode for a
Managed, Assured, or Distributed Work Block.

## Logical Role Mapping

| Logical role | OpenCode implementation | Default authority |
|---|---|---|
| Orchestrator | main OpenCode session / selected primary agent | workflow coordination |
| Architect | `.opencode/agents/architect.md` | read-only |
| Critic | `.opencode/agents/critic.md` | read-only |
| Coder | `.opencode/agents/coder.md` | permission-prompted approved write-set |
| Reviewer | `.opencode/agents/reviewer.md` | read-only |
| Verifier | `.opencode/agents/verifier.md` | read-only plus approved reports |

The built-in Plan and Build agents may still be used, but the Work Block must
record which logical function they perform and their effective permissions.

## Authority Boundary

OpenCode implements the same schema-v3 model as the other supported runtimes:

```text
authority_mode = github_capability
```

Runtime permissions and project-local hooks are cooperative guardrails. They do
not create production authority and are not a cryptographic or OS security
boundary.

Per-Work-Block SSH signing is retired from the normal development path. A Coder
does not need an Owner signing key, `ssh-keygen`, an authorization record, or a
detached signature to edit approved source, create a local commit, or push a
normal feature branch.

Consequential authority belongs outside the mutable project: GitHub rules and
least-privilege tokens, Actions permissions, OS isolation, and separately held
production/VPS/database/secrets.

## Installed Project Files

```text
opencode.json
.opencode/
└── agents/
    ├── architect.md
    ├── critic.md
    ├── coder.md
    ├── reviewer.md
    └── verifier.md
```

No provider, model, plugin, MCP server, API key, production secret, or external
directory is enabled by the framework.

## Project Configuration

`opencode.json`:

- loads `AGENTS.md`, governance, lifecycle, roster, and this adapter as
  instructions;
- sets `default_agent: build`, `subagent_depth: 1`, `share: manual`,
  `snapshot: true`;
- explicitly denies common secret paths;
- denies external-directory access;
- requires approval for edits, most Bash, web, task delegation, MCP tools,
  question prompts, doom-loop recovery, and todo writes;
- allows harmless Git inspection and local `git commit` without a signature;
- prompts for `git push` so normal feature pushes are visible to the runtime;
- denies destructive Git and `rm` commands;
- starts with empty `mcp` and `plugin` collections;
- leaves provider selection unconfigured.

The shared governance contract still forbids direct protected/default-branch
mutation, force push, production/live infrastructure, live data, credential or
secret operations, irreversible external publish, and real client-facing
communication in the normal agent channel.

OpenCode's runtime permission result is one of `allow`, `ask`, or `deny`:

- `ask` is a runtime prompt, not Owner security authority;
- `allow` does not expand the Work Block write-set;
- `deny` is useful defense in depth;
- external GitHub/OS/credential controls remain authoritative for consequential
  actions.

## Permission Keys

The baseline explicitly configures safety-sensitive permissions.

| Key | Default | Guardrail purpose |
|---|---|---|
| `read` | `allow` with secret denies | File reads |
| `edit` | `ask` | File modifications |
| `bash` | `ask` with explicit Git/destructive rules | Shell commands |
| `list` | `allow` | Directory listing |
| `task` | `{ "*": "ask" }` | Subagent invocation |
| `skill` | `{ "*": "allow", "internal-*": "deny" }` | Skill loading |
| `question` | `ask` | Interactive questions |
| `doom_loop` | `ask` | Repetition recovery |
| `todowrite` | `ask` | Todo updates |
| `lsp` | `ask` | LSP queries |
| `webfetch` | `ask` | URL fetching |
| `websearch` | `ask` | Web search |
| `external_directory` | `deny` | Outside-project paths |
| `mcp_*` | `ask` | MCP invocation |

Project Bash policy intentionally uses:

```text
git commit*      allow
git push*        ask
git reset --hard* deny
git clean*       deny
rm *             deny
```

The Coder has the same normal Git posture. Architect, Critic, Reviewer, and
Verifier keep commit/push denied because their logical functions are read-only
apart from explicitly bounded evidence artifacts.

## Permission Boundary

The generated Coder uses `edit: ask`. The permission prompt gives the human or
runtime a visibility point; the active Work Block and write-set still define the
permitted source scope.

Do not use a runtime permission prompt to authorize a production deploy, secret
change, destructive operation, or protected/default-branch bypass. Those require
an externally controlled capability.

## Subagents

Project agents live in `.opencode/agents/` and use `mode: subagent`.

They omit concrete models so provider and model routing remain private/runtime
configuration. Agent permissions are stricter than or equal to project defaults:

- Architect, Critic, Reviewer, and Verifier deny source edits;
- Coder prompts for edits, allows local commits, and prompts for normal pushes;
- all roles deny destructive Git and `rm`;
- nested task delegation is denied for bundled subagents;
- external-directory access is denied;
- web and MCP capabilities require approval.

Record actual child-session IDs or other launch evidence when assurance
independence matters.

## Plugins and MCP

OpenCode supports project plugins and MCP servers, but both collections are empty
in the framework baseline.

Before activation:

1. complete the integration-admission record;
2. identify exact plugin/MCP tools and permission names;
3. add allow/ask/deny rules for each tool;
4. confirm secret and external-directory boundaries;
5. run safe and denied-action smoke fixtures;
6. record version, provider, model, and capability evidence.

Admission does not grant production authority.

## Capability Snapshot

Start with evidence-backed values:

```yaml
runtime: opencode
status: available_unverified
capabilities:
  project_instructions: configured
  project_subagents: configured
  granular_permissions: configured
  per_agent_permissions: configured
  skills: observed_or_unknown
  mcp: disabled
  plugins: disabled
  external_directory_guard: configured
  local_commit: configured
  feature_push_prompt: configured
  production_authority: unavailable_by_design
  worktrees: external_workflow
  os_isolation: false
limitations:
  - runtime permission prompts do not independently prove the Work Block write-set
  - provider/model availability depends on local configuration
  - plugins and MCP can add tools that need separate admission
  - same checkout and machine unless separately isolated
```

Upgrade `observed_or_unknown` only after target-environment smoke evidence.

## Activation

1. Bootstrap the project.
2. Review `opencode.json`, `.opencode/agents/`, `AGENTS.md`, and the active Work Block.
3. Confirm the runtime reads the committed operating contract.
4. Inspect effective provider/model and permissions.
5. Confirm read-only roles cannot write source.
6. Confirm Coder edits are restricted to the approved write-set by process and runtime prompts.
7. Confirm local Coder commit works without SSH signing.
8. Confirm normal feature push prompts rather than requiring a signed authorization.
9. Confirm force/default-branch/destructive/secret/external-directory operations remain denied by the applicable local/external boundaries.
10. Record the capability snapshot and limitations.

## Assurance and Isolation

A separate OpenCode child session improves context separation but does not by
itself establish a separate checkout, OS identity, credential store, or provider.
Use separate worktrees, containers, machines, accounts, or human review when the
governance profile requires stronger independence.

## Degraded Mode

When agents or permissions do not behave as documented:

- stop state-changing work;
- label the runtime adapter degraded;
- use Plan/read-only mode or a separate verified runtime;
- preserve the same artifacts and logical functions;
- do not infer production authority from local state;
- do not claim a passing assurance gate without evidence.

## Official References

- <https://opencode.ai/docs/>
- <https://opencode.ai/docs/agents/>
- <https://opencode.ai/docs/permissions/>
- <https://opencode.ai/docs/config/>
- <https://opencode.ai/docs/skills/>
- <https://opencode.ai/docs/plugins/>
- <https://opencode.ai/docs/server/>
- <https://opencode.ai/docs/cli/>
