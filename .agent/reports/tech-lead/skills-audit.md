# Skills Audit Report

**Date:** 2026-01-23
**Author:** Tech Lead Agent

## Summary

| Category | Count | Location |
|----------|-------|----------|
| Roles | 9 | `.agent/roles/` |
| Skills | 12 | `.agent/skills/` |
| Rules | 1 | `.agent/rules/` |
| Workflows | 2 | `.agent/workflow/`, `.agent/workflows/` |

---

## 🎭 Roles (9)

| Role | File | Responsibility |
|------|------|----------------|
| Orchestrator | `orchestrator.md` | Request routing, gate control |
| Discovery Analyst | `discovery-analyst.md` | PRD, research, RFC |
| Tech Lead | `tech-lead.md` | Technical specs, architecture |
| Planner | `planner.md` | Architecture design, task decomposition |
| Implementer | `implementer.md` | Code implementation |
| Quality Engineer | `quality-engineer.md` | Code review, testing |
| Validator | `validator.md` | Gate checking, next step |
| Tech Writer | `tech-writer.md` | Documentation |
| Trading Expert | `trading-expert.md` | Domain expert: market analysis, options |

---

## 🛠 Skills (12)

### Development Skills

| Skill | File | Use When |
|-------|------|----------|
| Business Discovery | `business-discovery.md` | Creating PRD, user stories, requirements |
| Technical Discovery | `technical-discovery.md` | Codebase analysis, RFC, solution research |
| Task Decomposition | `task-decomposition.md` | Breaking plans into atomic tasks |
| Code Review | `code-review.md` | Reviewing code for quality, security |
| Testing | `testing.md` | QA, test plans, AC verification |
| Conduct Retro | `conduct-retro.md` | Post-mortem analysis, lessons learned |

### Trading Skills

| Skill | File | Use When |
|-------|------|----------|
| Market Structure | `market-structure.md` | Analyzing price action, S/R levels, trends |
| Technical Indicators | `technical-indicators.md` | Using RSI, MACD, Alligator, Fractals |
| Options Strategy | `options-strategy.md` | Designing option strategies, Greeks management |
| Portfolio Management | `manage-options-portfolio.md` | Analyzing positions, generating adjustments |
| Risk Management | `risk-management.md` | Position sizing, stop-loss, hedging |
| Trading Automation | `trading-automation.md` | Pine Script, bots, signals |

---

## 📋 Rules (1)

| Rule | File | Purpose |
|------|------|---------|
| SDD Enforcer | `000-sdd-enforcer.md` | Spec-Driven Development protocol |

---

## 🔄 Workflows (2)

| Workflow | File | Purpose |
|----------|------|---------|
| Bybit Options Workflow | `workflow/bybit_options_workflow.md` | Backend analysis flow |
| Memory Sync | `workflows/memory-sync.md` | Session memory synchronization |

---

## ⚠️ Recommendations

### Structure Compliance

Current structure follows best practice:
```
.agent/
├── roles/           ✅ 9 role definitions
├── skills/          ✅ 12 skill definitions
├── rules/           ✅ 1 rule (SDD enforcer)
├── workflow/        ⚠️ Rename to "workflows" for consistency
└── reports/         ✅ Created with this audit
```

### Action Items

1. **Merge `workflow/` into `workflows/`** — consolidate into single folder
2. **Add YAML frontmatter** to skills without it (e.g., `conduct-retro.md`)
3. **Create `skills/SKILL_INDEX.md`** — quick reference for all available skills

---

## Skill Usage Matrix

| Situation | Skill to Use |
|-----------|--------------|
| New feature request | `business-discovery` |
| Analyze existing code | `technical-discovery` |
| Break down plan | `task-decomposition` |
| Before merging code | `code-review` |
| Verify implementation | `testing` |
| Post-incident | `conduct-retro` |
| Analyze market conditions | `market-structure`, `technical-indicators` |
| Design option trade | `options-strategy` |
| Check portfolio health | `manage-options-portfolio` |
| Size position / set stops | `risk-management` |
| Create bot/indicator | `trading-automation` |
