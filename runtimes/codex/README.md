# Codex Runtime Adapter

## Status

Implemented generated-project baseline for project-scoped logical-role agents,
Codex hooks, cooperative Work Block/write-set guards, and explicit integration
admission.

This adapter implements the Governance Core. It does not redefine authority,
source-of-truth order, Hard Stops, artifact verdicts, or closeout.

## Logical Role Mapping

| Logical role | Codex implementation | Default sandbox |
|---|---|---|
| Orchestrator | main Codex thread | parent session policy |
| Architect | `.codex/agents/architect.toml` | read-only |
| Critic | `.codex/agents/critic.toml` | read-only |
| Coder | `.codex/agents/coder.toml` | workspace-write |
| Reviewer | `.codex/agents/reviewer.toml` | read-only |
| Verifier | `.codex/agents/verifier.toml` | read-only |

The built-in explorer may support read-heavy discovery. Temporary
specializations change focus, not authority.

## Installed Files

```text
.agent/
├── active-work-block.json
├── authorizations/          # legacy audit/history only
└── hooks/
    └── hard_stop_policy.py

.codex/
├── config.toml.template
├── hooks.json
├── agents/
│   ├── architect.toml
│   ├── critic.toml
│   ├── coder.toml
│   ├── reviewer.toml
│   └── verifier.toml
├── hooks/
│   ├── hard_stop_policy.py
│   ├── pre_tool_use_policy.py
│   ├── stage0_write_gate.py
│   └── subagent_context.py
└── scripts/
    ├── lifecycle.py
    └── doctor.py
```

- `.agent/hooks/hard_stop_policy.py` is the shared provider-neutral cooperative
  guard for consequential commands and external-runtime admission.
- `.codex/hooks/hard_stop_policy.py` is a Codex compatibility wrapper.
- `stage0_write_gate.py` is a deprecated compatibility entry point for the
  Codex write/scope policy.
- `config.toml.template` is not activated automatically.

## Authority Boundary

Schema v3 uses `authority_mode: github_capability`.

Project-local Work Block state and hooks are **process guardrails**, not the
security boundary. They enforce scope, write-set discipline, role separation,
and early denial of obvious dangerous commands.

Consequential authority belongs outside the mutable repository wherever
practical:

- GitHub rulesets/protected branches;
- least-privilege agent credentials;
- GitHub Actions permissions;
- OS/container/user isolation;
- separately held production, VPS, database, and secret credentials.

Per-Work-Block SSH signing is retired from the normal development path. A Coder
does not need `ssh-keygen`, an Owner private key, `allowed_signers`, an
authorization JSON, or detached `.sig` merely to edit, commit, or push a normal
feature branch.

The framework's public `main` branch is protected externally by the active
GitHub ruleset requiring pull requests and required checks while denying branch
deletion and non-fast-forward updates.

## Configuration

Project multi-agent settings belong under `[agents]`:

```toml
[agents]
enabled = true
max_concurrent_threads_per_session = 6
interrupt_message = true
```

The public framework does not pin models/providers. Keep authentication,
provider definitions, private endpoints, telemetry settings, concrete model
routing, and production credentials in user/private configuration.

Do not duplicate project hooks inline in `.codex/config.toml` when
`.codex/hooks.json` already declares them.

## Hook Layers

`.codex/hooks.json` registers:

1. shared Hard Stop guard for consequential Bash operations and direct external
   runtime CLI invocation;
2. Codex Work Block/write-set guard for Bash and edit/apply-patch paths;
3. bounded Work Block context on `SubagentStart`.

A command must pass every applicable local guard. These hooks are cooperative:
they may deny an operation early, but they are not a cryptographic or OS
security boundary and must not be relied on to protect production credentials.

Plugins, MCP tools, connectors, browsers, and other external capabilities
require separate admission and runtime permission.

## Machine Work Block

`.agent/active-work-block.json` starts fail-closed and records:

- `schema_version: 3`;
- `authority_mode: github_capability`;
- Work Block/governance profile;
- specification path/revision;
- planning baseline `base_commit`;
- local source write-gate state;
- Critic state/isolation/report;
- exact source and coordination write-sets;
- approved integration IDs and admission-record paths;
- Review, Verification, Evaluation, and Drift state/evidence;
- closeout mode;
- named external Hard Stops.

Source writes require:

- schema version 3 and `authority_mode=github_capability`;
- non-empty Work Block ID;
- specification path/revision;
- `write_gate.status: READY`;
- resolved required Critic;
- non-empty write-set;
- target path inside the write-set.

The recorded `base_commit` is a planning/evidence baseline. A normal feature
commit does not create a cryptographic STALE/renew cycle. Material requirement,
scope, authority, or architecture changes return the Work Block to Define and
must update the local scope explicitly.

Coordination paths needed to prepare specifications/plans/reports/gate state may
remain writable while source is blocked.

## Local Lifecycle Helper

`.codex/scripts/lifecycle.py` provides atomic local coordination state:

- `status` is read-only;
- `prepare` produces the canonical BLOCKED schema-v3 state;
- `open` records Work Block/specification/write-set/Critic context and the current
  Git HEAD planning baseline;
- `freeze` blocks further source work while preserving evidence;
- `close --mode success-closeout|reporting-only` blocks source work and records
  the selected closeout mode.

Example:

```bash
python3 .codex/scripts/lifecycle.py open \
  --work-block-id WB-EXAMPLE \
  --specification-path docs/plans/wb-example.md \
  --specification-revision <revision> \
  --write src/example.py \
  --write tests/test_example.py \
  --critic-status READY \
  --critic-verdict APPROVE
```

No signer environment or private key is involved.

`.codex/scripts/doctor.py` redacts sensitive field values and reports schema-v3
capability-mode readiness separately from CLI availability. Normal CI never
invokes Codex. Explicit `--live` performs only a local CLI version check in a
disposable Git repository; `AVAILABLE` means the CLI answered, not that hooks or
native smoke passed.

## Hard Stops

Normal reversible development operations are not Owner Hard Stops when Work
Block scope allows them:

- `git add`;
- local feature commits;
- normal feature-branch push;
- pull-request preparation.

The shared guard still rejects obvious attempts at:

- direct protected/default-branch push;
- force push/history rewriting;
- recursive destructive removal and destructive Git cleanup;
- live infrastructure operations including SSH/SCP and common deploy commands;
- direct live-data mutation;
- credential/secret operations;
- client-facing communications;
- direct external image publish.

These denials are defense in depth. The actual protection for consequential
operations should be external capability separation. For example, an agent that
must not deploy production should not receive GitHub Actions write/dispatch
permission or VPS/DB/production secrets.

## External Runtime Admission

Direct child-runtime commands cross an integration boundary:

| Command | Integration ID |
|---|---|
| `codex` | `codex-cli` |
| `claude` | `claude-code-cli` |
| `opencode` | `opencode-cli` |

They require the matching ID in `integrations.approved` and at least one concrete
path in `integrations.admission_records`.

Admission does not authorize child-runtime source writes. The mission/function
binding and Work Block write-set must separately permit them.

## Write and Bash Scope Policy

The Codex write/scope layer:

- denies source writes while the local gate is BLOCKED/invalid;
- validates schema v3, specification, Critic, and write-set;
- validates both the source and `*** Move to:` destination of `apply_patch`;
- handles `Edit`/`Write` path shapes explicitly;
- denies paths outside the write-set;
- fails closed on compound/unknown mutating Bash whose targets cannot be safely
  scoped;
- validates staged paths before a local commit;
- rejects broad implicit dependency-manager writes unless handled by an
  explicitly reviewed workflow;
- permits normal feature push to continue to the separate Hard Stop/external
  capability layer.

## Subagent Context and Isolation

`subagent_context.py` adds bounded operational context:

- logical agent type and permission mode;
- role authority;
- authority mode;
- Work Block/governance profile;
- specification/revision and planning baseline;
- local source gate and Critic state;
- source/coordination write-sets;
- external Hard Stop categories.

Context does not grant external authority.

Custom-agent sandbox defaults are defense in depth. The parent turn's live
sandbox/approval overrides may apply to children. Record actual isolation and
shared machine/checkout/auth resources. Use separate worktrees, roots, runtimes,
containers, users, machines, accounts, or human review when stronger assurance
is required.

Parallel writers require separate worktrees/non-overlapping write-sets, one
consolidation owner, and assurance of the consolidated result.

## Activation

1. Bootstrap the project.
2. Read `AGENTS.md`, Governance Core, and this adapter.
3. Review `.codex/agents/`, `.codex/hooks.json`, and shared/Codex hooks.
4. Copy `.codex/config.toml.template` to `.codex/config.toml` only when desired.
5. Create the Work Block while local source scope remains BLOCKED.
6. Record runtime/capability/isolation evidence and integration admission.
7. Resolve required Critic.
8. Open schema-v3 local source scope with the exact write-set.
9. Run safe fixtures/read-only smoke.
10. Use GitHub/OS/credential controls for consequential external actions.

## Validation

Framework CI runs, among other contracts:

```bash
python scripts/test-runtime-conformance.py
python scripts/test-integration-contracts.py
python scripts/test-integration-admission-evidence.py
python scripts/test-codex-adapter.py
python scripts/test-codex-hard-stops.py
python scripts/test-codex-control-plane.py
```

The disposable scaffold verifies agents, shared/Codex/Claude guards, machine
state, runtime/integration adapters, safe defaults, and templates.

## Degraded Mode

When custom agents/hooks are unavailable:

- preserve logical functions through separate sessions/runtimes/manual passes;
- record actual authority/isolation and missing enforcement;
- keep source blocked unless another approved process guard enforces scope;
- label same-context assurance degraded;
- never infer production authority from local state.

## Official References

- <https://developers.openai.com/codex/subagents>
- <https://developers.openai.com/codex/hooks>
- <https://developers.openai.com/codex/config-reference>
