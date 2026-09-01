# Runtime Capability Negotiation

## Purpose

The Orchestrator selects a topology from declared capabilities and assurance
requirements. Provider or product names are descriptive metadata, not routing
rules by themselves.

## Capability State

A runtime adapter should publish a capability state using this shape or an
equivalent machine-readable contract:

```yaml
schema_version: 1
runtime: generic
adapter_version: 1
verified_at: 2026-07-25
verified_by: smoke-test-id

capabilities:
  native_subagents: unknown
  custom_agent_profiles: unknown
  separate_readonly_context: unknown
  workspace_write_sandbox: unknown
  hooks_or_policy_interception: unknown
  skills: unknown
  mcp: unknown
  plugins: unknown
  parallel_read: unknown
  parallel_write: unknown
  worktrees: unknown
  browser_or_runtime_testing: unknown
  structured_tool_output: unknown
  usage_reporting: unknown

limitations: []
```

Allowed capability values:

- `true` — demonstrated by the cited smoke test or authoritative runtime
  documentation;
- `false` — known unavailable;
- `conditional` — available only with named configuration or environment;
- `unknown` — not yet verified.

`unknown` must not be treated as `true`.

## Topology Inputs

Before execution, classify:

- governance profile;
- domains and blast radius;
- write sets;
- side-effect class;
- required reviewer/verifier independence;
- hard stops;
- available runtimes and capabilities;
- cost, usage, and time constraints;
- recovery requirements;
- secrets and credential boundaries.

## Selection Rules

1. Prefer the smallest topology that satisfies the selected governance profile.
2. Prefer native, supported runtime mechanisms over custom transports.
3. Prefer read-only parallelism before write parallelism.
4. Use one Coder per write set.
5. Require separate worktrees or equivalent isolation for parallel writes.
6. Do not select a cheaper model or weaker isolation for an authority-bearing
   decision unless the governance profile permits it.
7. Record the effective runtime, model class, isolation, and fallback rather than
   only the requested values.

## Fallback Ladder

When a required function cannot run in the preferred topology:

```text
native subagent
  → separate top-level session
  → approved external runtime or official integration
  → audited file-based handoff
  → same-context degraded pass
  → blocked / reporting-only closeout
```

The fallback ladder is not permission to reduce required assurance. If the
selected profile requires independent or OS-isolated verification, a
same-context pass remains insufficient.

## Example Routing Record

```yaml
work_block_id: wb-042
governance_profile: assured
function: verification
requested:
  role: verifier
  isolation: separate_session
  model_class: balanced_engineering
selected:
  runtime: codex
  agent_profile: verifier
  isolation: separate_subagent
  effective_model: recorded-by-adapter
fallback: true
fallback_reason: separate top-level session unavailable in active environment
assurance_result: degraded
promotion_blocked: true
```

## Smoke-Test Rule

Runtime capabilities that affect authority or assurance require a repeatable
smoke test before being marked `true` in a project profile. Examples:

- the requested custom agent actually starts;
- the effective model/profile is observable;
- read-only restrictions prevent writes;
- hooks reject a blocked write;
- separate worktrees do not overlap;
- reports preserve the artifact schema;
- failed or unavailable tools produce a blocked result rather than a false pass.

A runtime software update invalidates only the capabilities reasonably affected
by that update. Record the adapter version and last verification method.
