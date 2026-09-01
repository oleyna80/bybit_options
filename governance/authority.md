# Authority Model

## Purpose

Authority is structural. A runtime, model, plugin, tool, shell capability, or
project-local hook does not authorize an action by itself.

Every action must be permitted by all applicable dimensions:

1. logical role;
2. approved Work Block scope;
3. write set;
4. side-effect class;
5. external capability boundary when the action is consequential;
6. runtime capability and isolation level.

The framework deliberately separates **process guardrails** from **security
boundaries**. Work Blocks, write sets, Critic/Reviewer/Verifier roles, and local
hooks constrain normal agent behavior. GitHub repository rules, least-privilege
credentials, OS isolation, and secret ownership constrain what the agent can
actually do outside that cooperative process.

## Stable Logical Roles

| Role | Core responsibility | Default write authority |
|---|---|---|
| Owner | Approves objectives, exceptions, consequential external actions, and final business acceptance | Owner-controlled external capability surfaces |
| Orchestrator | Frames Work Blocks, selects topology, controls stage transitions, consolidates evidence, closes work | Governance and coordination artifacts inside scope |
| Architect | Produces architecture, discovery, specification, and plan proposals | Draft architecture/specification artifacts when approved |
| Critic | Challenges scope, assumptions, risks, topology, and verification before execution | Critic report only |
| Coder | Implements the approved change | Approved implementation write set only |
| Reviewer | Reviews the frozen diff for defects, regressions, security, architecture, and maintainability | Review report only |
| Verifier | Gathers evidence against acceptance criteria and contracts | Verification evidence only |

Roles describe authority and accountability, not mandatory separate processes.
One runtime may execute multiple roles when the selected governance profile
permits it. Higher-risk profiles require stronger separation.

## Separate Dimensions

Do not encode runtime or model names as authority-bearing roles.

```yaml
function: code_review
role: reviewer
runtime: claude-code
model_class: balanced_engineering
isolation: separate_session
authority: read_only
```

The same contract may be implemented by another runtime without changing its
authority:

```yaml
function: code_review
role: reviewer
runtime: codex
model_class: strong_reasoning
isolation: separate_subagent
authority: read_only
```

## Isolation Levels

| Level | Meaning | Typical use |
|---|---|---|
| `same_context` | Same active agent/context performs another function | Advisory or low-risk work only |
| `separate_subagent` | Separate delegated context in the same runtime/session | Read-heavy discovery, criticism, review |
| `separate_session` | Independent top-level session against the same repository state | Independent review or verification |
| `separate_worktree` | Independent branch/worktree and write scope | Parallel bounded implementation |
| `separate_runtime` | Different agent runtime or model family | Adversarial second opinion |
| `os_isolated` | Separate OS user, container, or equivalent security boundary | Credentials, live data, deploy, sensitive verification |

A declared isolation level is evidence, not self-authenticating proof. Runtime
adapters must record how it was achieved and any residual limitations.

## External Capability Boundary

For repositories hosted on GitHub, normal development may include, when allowed
by the Work Block and credential:

- editing approved paths;
- tests/builds;
- staging and local commits;
- normal feature-branch pushes;
- pull-request creation and updates;
- CI/review inspection.

Default/protected-branch and production authority should be enforced outside
mutable project state wherever practical. Use repository rules, least-privilege
credentials, workflow/environment permissions, OS isolation, and separately held
production/VPS/database/secret capabilities according to the actual risk.

Project-local text files, hooks, signatures, or approval state must not be treated
as an independent security boundary merely because they are verifiable. If a
stronger authorization boundary is required, place it in an independently
controlled capability appropriate to the threat model.

Protected-branch behavior is hosting-platform state and should be verified live
when it matters rather than copied as permanent policy text.

Historical rationale for retired authority mechanisms belongs in project
engineering memory or closeout evidence, not this normative contract.

## Non-Expansion Rule

Temporary specialization narrows focus but never expands authority.

Examples:

- `Reviewer / Security Analyst` remains read-only.
- `Coder / Backend Specialist` may write only the approved backend write set.
- `Verifier / Browser QA` may create only approved evidence artifacts.
- Access to GitHub, shell, Docker, database, browser, MCP, or provider APIs does
  not grant permission to use them for consequential side effects.

## Parallelism

- Parallel read-only roles may inspect the same frozen source state.
- Parallel write roles require non-overlapping write sets and separate
  worktrees/branches unless an adapter provides an equivalent isolation model.
- Use exactly one Coder for each write set.
- The Orchestrator must consolidate conflicts before verification or closeout.

## Failure and Degraded Assurance

If the required role or isolation level is unavailable:

1. do not silently omit the function;
2. select the narrowest documented fallback;
3. label the result as degraded;
4. record what could not be independently established;
5. keep downstream promotion blocked when the selected governance profile
   requires stronger assurance.

## Hard Stops

Hard Stops are consequential operations that the normal agent channel should not
be able to perform merely by editing project-local state:

- production deployment or live service restart;
- live database mutation or migration apply;
- credential or secret changes;
- destructive version-control/filesystem operations;
- direct push, deletion, or non-fast-forward update of protected/default branches;
- irreversible public/package publish where it changes external state;
- real client-facing communications;
- payment, order, stock, CRM, or other live business-data mutation outside an
  approved application execution path.

Enforce these with external capabilities wherever practical: GitHub rules,
least-privilege tokens, workflow permissions, protected environments where
available, OS users/containers, and separately held credentials. Project-local
hooks may deny obvious attempts early, but are cooperative guardrails only.
