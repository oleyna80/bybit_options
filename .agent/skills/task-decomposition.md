---
name: Task Decomposition
description: Декомпозиция планов на атомарные задачи
---

# Skill: Task Decomposition

## Description
Преобразование архитектурных планов в исполняемые задачи с AC и зависимостями.

## Triggers
- "разбей на задачи", "tasklist", "декомпозиция", "backlog"

## Task Structure Rules
1. **Atomic** — одна задача = одно изменение, 1 сессия
2. **Independent** — минимизируй зависимости
3. **Testable** — AC проверяемы
4. **Ordered** — зависимости явно указаны

## Naming Convention
- `CODEBASE-XXX` — структура кода
- `WEB-XXX` — веб-интерфейс
- `API-XXX` — API
- `DELTA-XXX` — Delta Analytics

## Output
Файл `docs/tasklist/<ticket>.tasklist.md`:

```markdown
# <Feature> Tasklist
Status: TASKLIST_READY

## Tasks

- <TICKET>-001: <Short description>
  Depends on: none
  Acceptance Criteria:
  - AC1: <testable condition>
  - AC2: <testable condition>

- <TICKET>-002: <Short description>
  Depends on: <TICKET>-001
  Acceptance Criteria:
  - AC1: ...
```

## Good AC Examples
- ✅ "Файл `path/file.py` существует и импортируется"
- ✅ "Тест `test_xxx.py` проходит"
- ✅ "Endpoint `/api/v1/xxx` возвращает JSON"

## Bad AC Examples
- ❌ "Код работает" (нетестируемо)
- ❌ "Быстрый" (неизмеримо)
