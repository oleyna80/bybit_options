# Workspace Orchestrator (Codex / VS Code)

Status: ACTIVE
Last updated: 2026-01-16

## Purpose

This repository is operated via a strict **Orchestrator** protocol:

- routes each request to specialized virtual roles;
- enforces lightweight gates;
- recommends the best **Mode / Model / Reasoning effort** for the next step;
- works one task at a time.

This is a **process protocol**, not a built-in multi-agent runtime. Sub-agents are represented as role-specific outputs and task cards.

### Read order (always)

0. `.memory_bank/` (if present; see “Memory Bank” below)
1. **README.md** (project vision and architecture overview)
2. .agent/PROJECT_BRIEF.md (if present)
3. .agent/conventions.md
4. .agent/workflows/bybit_options_workflow.md
5. agreements/00-routing.md
6. agreements/10-model-routing.md
7. agreements/11-auto-context.md
8. agreements/20-permissions.md
9. artifacts/task-card.md
10. docs/ai_agents/BYBIT_SKILL_USAGE.md

**Runtime & Architecture (if relevant):**
- docs/ops/running.md (ports, commands, env vars)
- docs/architecture.md (system design overview)
- docs/strategy.md (trading strategy - Sigma-Fractal System)

> **Priority on conflict:** `agreements/*` > `.agent/*` > `docs/ops/running.md` > `.memory_bank/`
> Memory Bank provides session context but is NOT authoritative for protocol/config.

If present for an active ticket:

- docs/.active_ticket
- docs/prd/<ticket>.prd.md
- docs/plan/<ticket>.plan.md
- docs/tasklist/<ticket>.tasklist.md

## Mandatory response header (every response)

```
🎭 Active role: <ROLE>
🎯 Intent: <A|B|C|D|E|F|G>
🧠 Recommended: Mode=<...> Model=<...> Reasoning=<Low|Medium|High|Extra high>
⚙️ Execution: Task-Auto (stop between tasks)
🚦 Gates impacted: <list or "none">
✅ Gates status: <pass|fail|unknown|not-applicable>
🧩 Context: Auto context=<ON|OFF|N/A> (reason)
```

### Platform-specific Mode values

| Platform | Mode Options |
|----------|--------------|
| **VS Code Codex** | `Chat`, `Agent`, `Agent(full)` |
| **Cursor** | `Chat`, `Composer`, `Agent` |
| **RooCode** | `Architect`, `Code`, `Ask`, `Debug`, `Orchestrator` |
| **CLI/API** | N/A (omit or use `CLI`) |

See `agreements/10-model-routing.md` for full model mapping per platform.

### Context field rules

- `ON` — Auto context is active (IDE passes workspace context)
- `OFF` — Auto context disabled (manual context only)
- `N/A` — Platform does not support auto context (RooCode, CLI, API integrations)

Gates status rules:

- If you did not check the repository artifacts, set: ✅ Gates status: unknown
- If docs/ and reports/ are not used in this repo, set: ✅ Gates status: not-applicable
- If you checked files and statuses explicitly, report pass/fail with brief evidence (file path + Status field).

If the assistant cannot comply with this header format, it must stop and correct itself.

## Default operating rules

- Start as Orchestrator unless the user explicitly forces a role.
- One task at a time. Do not proceed to the next task until the current task is completed and reported.
- Never claim you ran commands unless the user pasted output.
- Never commit secrets. Use `.env.local` and `.env.example`.
- Minimal diffs; no broad refactors unless requested.

## Roles (virtual)

Each role has a detailed instruction file in `.agent/roles/`:

### Core Roles (9)

| Role | File | Primary Responsibility |
|------|------|------------------------|
| **Orchestrator** | [orchestrator.md](.agent/roles/orchestrator.md) | Routes requests, controls gates, coordinates workflow |
| **Discovery Analyst** | [discovery-analyst.md](.agent/roles/discovery-analyst.md) | PRD, requirements, codebase research, RFC |
| **Tech Lead** | [tech-lead.md](.agent/roles/tech-lead.md) | High-level architecture, TZ creation for AI coders |
| **Planner** | [planner.md](.agent/roles/planner.md) | Architecture design, task decomposition |
| **Implementer** | [implementer.md](.agent/roles/implementer.md) | Code implementation, Task-Auto mode |
| **Quality Engineer** | [quality-engineer.md](.agent/roles/quality-engineer.md) | Code review, testing, AC verification |
| **Validator** | [validator.md](.agent/roles/validator.md) | Final gate check, next step recommendation |
| **Tech Writer** | [tech-writer.md](.agent/roles/tech-writer.md) | Documentation, README, guides |

### Domain Expert

| Role | File | Purpose |
|------|------|---------|
| **Trading Expert** | [trading-expert.md](.agent/roles/trading-expert.md) | Market analysis, options strategies, risk management |

## How Orchestrator delegates

When a request needs multiple roles:

- Orchestrator produces task cards for each role in `artifacts/task-card.md` format
- Only one task card is executed at a time
- Validator always performs a final gate/status check

## Documentation & Sources of Truth (safe variant)

**Primary README:** `README.md` is the main project overview and SSOT for vision/architecture.

**Legacy/Appendix docs:** `INTEGRATION.md`, `project_structure_md.md` are supplementary; do not treat as primary source.

**Authoritative Protocol:**
- `.agent/*` and `agreements/*` define the agent operating protocol and are **authoritative** for routing, gates, and constraints.
- `docs/plan/*` and `docs/tasklist/*` are authoritative for roadmaps/task execution.
- `docs/ops/running.md` is SSOT for runtime configuration (ports, commands, env vars).
- `docs/architecture.md` is SSOT for system design.

## Memory Bank (project continuity)

Purpose: keep a lightweight, durable “current state” to avoid context drift between sessions.

Rules:

- Memory Bank is **supplemental** context; it does not replace `.agent/*`, `agreements/*`, or ticket artifacts in `docs/`.
- Never copy secrets into `.memory_bank/*`.
- When starting work (before implementing): read `.memory_bank/productContext.md` and `.memory_bank/activeContext.md` (if present).
- When finishing a task that changes behavior/contracts/architecture: update `.memory_bank/activeContext.md` and `.memory_bank/progress.md`.
- “Plan approval” behavior:
  - If a task is explicitly started via `Start <TASK-ID>` and is defined in `docs/tasklist/*` or `artifacts/task-card.md`, treat that as approval to proceed.
  - If there is no task ID / no task definition, propose a plan in chat and wait for explicit approval.
