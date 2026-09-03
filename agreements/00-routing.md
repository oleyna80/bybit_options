# Routing & Gates

## Intent classification (priority-based)

Choose ONE primary intent using this priority order.

1. D) Implement / change code
   Triggers: "сделай", "реализуй", "добавь", "почини", "refactor", "implement", "code", "PR", "diff", "commit"

2. C) Break down into tasks
   Triggers: "разбей на задачи", "tasklist", "декомпозиция", "план работ по задачам", "backlog", "estimates", "acceptance criteria for tasks"

3. B) Architecture / design
   Triggers: "план", "архитектура", "workflow", "orchestrator", "BybitConnector", "MarketDataService", "RiskEngine",
   "грек", "portfolio risk", "опционная доска", "IV/HV", "серии/экспирации", "API дизайн"

4. A) Requirements / PRD
   Triggers: "PRD", "техзадание", "требования", "user stories", "NFR", "acceptance criteria (for the feature)"

5. E) Review / audit
   Triggers: "ревью", "review", "audit", "security review", "performance review"

6. F) Docs / guides
   Triggers: "README", "документация", "гайд"
7. G) Status / “what’s next?”
   Triggers: "что дальше", "статус", "next step", "gates"

Tie-break rule:

- If the user says "план" without mentioning docs/README/instruction, treat as **B (Architecture / design)**.
- If the user says "план" AND "разбей на задачи", primary intent is **C**.

## Role routing

| Intent | Route | Role File |
|--------|-------|-----------|
| A | → Discovery Analyst → Validator | `discovery-analyst.md` |
| B/C | → Planner → Validator | `planner.md` |
| D | → Implementer → Quality Engineer → Validator | `implementer.md` → `quality-engineer.md` |
| E | → Quality Engineer → Validator | `quality-engineer.md` |
| F | → Tech Writer → Validator | `tech-writer.md` |
| G | → Validator → next role | `validator.md` |
| T | → Trading Expert | `trading-expert.md` (domain expert) |

## Lightweight gates (only if the repo uses docs/reports)

- PRD_READY: docs/prd/<ticket>.prd.md (Status: PRD_READY)
- PLAN_APPROVED: docs/plan/<ticket>.plan.md (Status: PLAN_APPROVED)
- TASKLIST_READY: docs/tasklist/<ticket>.tasklist.md (Status: TASKLIST_READY)
- REVIEW_OK: reports/review/<ticket>-code.review.md exists and no blocking issues
- QA_PASSED: reports/qa/<ticket>.qa.md (Status: QA_PASSED)
- DOCS_UPDATED: docs/summaries/<ticket>-summary.md or README updated

If repo has no docs/ yet:

- Orchestrator must propose a minimal bootstrap step and proceed.

## Repo-specific gate paths (Bybit Options)

This project uses the following actual paths:

| Gate | Path Pattern | Notes |
|------|--------------|-------|
| PRD_READY | `docs/prd/<ticket>.prd.md` | Standard |
| PLAN_APPROVED | `docs/plan/<ticket>.plan.md` | Standard |
| TASKLIST_READY | `docs/tasklist/<ticket>.tasklist.md` | e.g., `HEDGER.tasklist.md`, `PRODUCT.tasklist.md` |
| REVIEW_OK | Root level `*_REVIEW.md` or `*_REPORT.md` | Legacy: `REVIEW_REPORT.md` |
| QA_PASSED | `reports/qa/<ticket>.qa.md` | Not yet used |
| DOCS_UPDATED | `README.md` or `docs/architecture.md` | SSOT docs |

> **Note:** Future reviews should use `reports/review/<ticket>-code.review.md` structure.
> Existing legacy files in root are acceptable for now.
