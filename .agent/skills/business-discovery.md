---
name: Business Discovery
description: Сбор и формализация бизнес-требований в PRD
---

# Skill: Business Discovery

## Description
Преобразование бизнес-запросов в структурированные PRD с четкими acceptance criteria.

## Triggers
- "PRD", "техзадание", "требования", "user stories", "NFR"

## Inputs
- Запрос пользователя
- `.agent/PROJECT_BRIEF.md`
- Существующие PRD в `docs/prd/`

## Process
1. **Clarify** — задай уточняющие вопросы
2. **Research** — изучи существующий код (grep/outline)
3. **Draft** — создай черновик PRD (Status: DRAFT)
4. **Review** — запроси подтверждение
5. **Finalize** — установи Status: PRD_READY

## Output
Файл `docs/prd/<ticket>.prd.md`:

```markdown
# PRD: <Feature Name>
Status: DRAFT | PRD_READY

## Problem Statement
## Goals
## Non-Goals
## User Stories
## Functional Requirements
## Non-Functional Requirements
## Acceptance Criteria (Given/When/Then)
## Dependencies
## Open Questions
## Risks
```

## Quality Gates
- [ ] Problem statement объясняет "почему"
- [ ] User stories покрывают основные сценарии
- [ ] AC тестируемы (Given/When/Then)
- [ ] Non-goals исключают scope creep
