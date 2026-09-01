# System Patterns

Architecture and key design decisions.

## 📐 Core Architecture

Refer to:
- `.agent/workflow/bybit_options_workflow.md` — Backend analysis flow
- `docs/plan/*` — Active plans
- `project_structure_md.md` — Directory layout

---

## 🛠 Agent Capabilities

### Roles (9 core + 1 domain expert)

| Role | Purpose | When to Use |
|------|---------|-------------|
| **Orchestrator** | Routes requests | Default entry point |
| **Discovery Analyst** | PRD, research | Intent A |
| **Tech Lead** | Technical specs | Architecture decisions |
| **Planner** | Design + tasks | Intent B/C |
| **Implementer** | Coding | Intent D |
| **Quality Engineer** | Review + test | Intent E or after D |
| **Validator** | Gate check | After each phase |
| **Tech Writer** | Documentation | Intent F |
| **Trading Expert** | Domain expert | Trading questions (Intent T) |

### Skills (12)

**Development:**
- `business-discovery` — PRD creation
- `technical-discovery` — Codebase/RFC research
- `task-decomposition` — Breaking plans into tasks
- `code-review` — Static code analysis
- `testing` — Dynamic verification
- `conduct-retro` — Post-mortem learning

**Trading:**
- `market-structure` — Price action, S/R levels
- `technical-indicators` — RSI, MACD, Alligator, Fractals
- `options-strategy` — Greeks, spreads, morphing
- `manage-options-portfolio` — Position analysis
- `risk-management` — Position sizing, hedging
- `trading-automation` — Pine Script, bots

### Rules

- `000-sdd-enforcer` — Spec-Driven Development: no code without approved spec

---

## 🔗 References

- **Routing:** `agreements/00-routing.md`
- **Permissions:** `agreements/20-permissions.md`
- **Conventions:** `.agent/conventions.md`

---

*Last updated: 2026-01-23*
