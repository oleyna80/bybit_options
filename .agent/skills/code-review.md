---
name: Code Review
description: Анализ кода на соответствие архитектуре, безопасность и качество
---

# Skill: Code Review

## Description
Детальный анализ кода на соответствие conventions, безопасность и maintainability.

## Triggers
- "ревью", "review", "audit", "security review"

## Inputs
- Измененные файлы (diff или полный код)
- `.agent/conventions.md`
- План/PRD для контекста

## Checklist

### Architecture
- [ ] Модули соблюдают boundaries (core pure, services async)
- [ ] Pydantic на публичных интерфейсах
- [ ] DI используется правильно
- [ ] Нет циклических зависимостей

### Code Quality
- [ ] Type hints везде
- [ ] Понятные имена
- [ ] DRY соблюдается
- [ ] Нет dead code

### Security
- [ ] Секреты только в .env
- [ ] Input validated
- [ ] Sensitive data не в логах

### Performance
- [ ] Async I/O правильно
- [ ] Нет N+1 queries
- [ ] Кэширование где нужно

## Output
Отчет `reports/review/<ticket>-code.review.md`:

```markdown
# Code Review: <TASK-ID>

## Summary
- Files reviewed: N
- Issues: X critical, Y warnings, Z suggestions
- Verdict: APPROVED | NEEDS_CHANGES | BLOCKED

## Critical Issues (must fix)
## Warnings (should fix)
## Suggestions (nice to have)
```

## Severity Levels
- **Critical** → BLOCKED
- **Warning** → NEEDS_CHANGES
- **Suggestion** → APPROVED (with notes)
