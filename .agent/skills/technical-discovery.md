---
name: Technical Discovery
description: Технический анализ кодовой базы и исследование решений
---

# Skill: Technical Discovery

## Description
Анализ существующего кода, tech stack и исследование решений для новых фич.

## Triggers
- "исследуй", "проанализируй", "RFC", "audit tech stack"

## Inputs
- Task card или запрос
- `.agent/workflow/bybit_options_workflow.md`
- Целевые файлы для анализа

## Modes

### Mode A: Codebase Analysis
1. **grep_search** — поиск паттернов
2. **view_file_outline** — структура классов/функций
3. **view_code_item** — детали функций
4. **find_by_name** — поиск файлов

### Mode B: Solution Research
1. **Audit Tech Stack** — проверь `requirements.txt`, `.env`, existing DBs
2. **Web Search** — docs, GitHub, best practices
3. **Compare Options** — минимум 2 варианта (A vs B)

## Output
Файл `docs/research/RFC-<feature>.md` или `reports/agents/<task-id>/research-report.md`:

```markdown
# Research Report: <Topic>

## Context
Что исследовалось и почему.

## Findings
### 1. <Topic>
- File: `path/to/file.py`
- Observation: ...
- Evidence: (code snippet)

## Options Analysis
| Option | Pros | Cons |
|--------|------|------|
| A | ... | ... |
| B | ... | ... |

## Gaps / Risks
## Recommendation
```

## Constraints
- **No code changes** — только анализ
- **Evidence-based** — каждый finding с ссылкой на код
