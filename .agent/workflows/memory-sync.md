---
description: Синхронизация Memory Bank между сессиями чатов
---

# Memory Bank Sync Protocol

## Назначение

Этот workflow обеспечивает сохранение контекста между разными чат-сессиями.
Без него информация о выполненных задачах теряется при смене чата.

---

## On Start (каждый новый чат)

**Перед началом любой работы прочитай:**

```
1. .memory_bank/activeContext.md — текущий фокус работы
2. .memory_bank/progress.md — что уже сделано
3. .memory_bank/techContext.md — технические решения (если нужно)
```

**Цель:** Понять, где мы остановились и что делать дальше.

---

## On Complete (после каждой задачи)

**После завершения задачи обнови `.memory_bank/progress.md`:**

Формат записи:

```markdown
## YYYY-MM-DD HH:MM — <ROLE>: <TASK-ID>

**Status:** ✅ Completed | ⚠️ Partial | ❌ Blocked

**Summary:** <краткое описание что сделано>

**Files changed:**
- Created: `path/to/new_file.py`
- Modified: `path/to/existing_file.py`

**Next:** <следующая задача или блокер>
```

---

## On Context Switch (при смене фокуса)

**Если меняется область работы, обнови `.memory_bank/activeContext.md`:**

```markdown
# Active Context

**Current focus:** <название модуля/фичи>
**Current task:** <TASK-ID>
**Current role:** <роль агента>

**Recent decisions:**
- <решение 1>
- <решение 2>

**Open questions:**
- <вопрос 1>
```

---

## Примеры

### Пример записи в progress.md

```markdown
## 2026-01-17 13:30 — Implementer: HEDGER-006

**Status:** ✅ Completed

**Summary:** Реализован DeltaHedgerBot с NEUTRAL mode логикой.
Бот мониторит дельту, размещает limit orders через OrderExecutor,
логирует действия в БД.

**Files changed:**
- Created: `bybit_options/services/hedger/bot.py`
- Created: `tests/test_hedger/test_bot.py`
- Modified: `bybit_options/services/hedger/__init__.py`
- Modified: `bybit_options/services/hedger/models.py`

**Next:** HEDGER-007 (entry point script)
```

### Пример activeContext.md

```markdown
# Active Context

**Current focus:** Delta Hedger Bot implementation
**Current task:** HEDGER-008 (SignalDetector)
**Current role:** Implementer

**Recent decisions:**
- PositionMonitor выбрасывает PositionFetchError вместо возврата 0.0
- OrderExecutor имеет TODO на рефакторинг abstraction leak

**Open questions:**
- Нужна ли таблица fractals_cache или использовать perpetual_ohlcv?
```

---

## Ответственность по ролям

| Роль | Читает | Пишет |
|------|--------|-------|
| Orchestrator | activeContext, progress | activeContext, progress |
| Implementer | activeContext, progress | progress |
| Reviewer | activeContext, progress | progress |
| QA | activeContext, progress | progress |
| Validator | activeContext, progress | progress |
| Planner | activeContext, progress | progress |
| Analyst | activeContext, progress | progress |
| Researcher | activeContext, progress | progress |
| Tech Lead | activeContext, progress, techContext | techContext |
| Tech Writer | activeContext, progress | progress |
| Task Planner | activeContext, progress | progress |

---

## Частые ошибки

1. **Забыл прочитать перед работой** → Дублирование работы
2. **Забыл записать после работы** → Потеря контекста в следующем чате
3. **Слишком длинные записи** → Сложно парсить, пиши кратко

---

## Turbo-режим

// turbo-all

Если workflow вызывается с turbo-all, агент автоматически:
1. Читает memory_bank при старте
2. Обновляет progress.md после каждой задачи
