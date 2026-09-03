---
name: Testing
description: Разработка и выполнение test plans, верификация AC
---

# Skill: Testing

## Description
Верификация acceptance criteria, обнаружение регрессий, создание test plans.

## Triggers
- "проверь", "протестируй", "QA", "run tests"

## Test Types

### Unit Tests
- Файлы: `tests/test_*.py`
- Команда: `pytest tests/test_xxx.py -v`
- Фокус: чистые функции в `core/`

### Integration Tests
- Файлы: `tests/integration/`
- Мокирование: external APIs
- Фокус: взаимодействие сервисов

### Manual / Smoke Tests
- CLI: `python main.py`
- API: `curl http://localhost:8000/api/v1/health`

## Process
1. **Plan** — составь test plan по AC
2. **Execute** — выполни тесты
3. **Document** — запиши результаты
4. **Verdict** — QA_PASSED / QA_FAILED

## Output
Отчет `reports/qa/<ticket>.qa.md`:

```markdown
# QA Report: <TASK-ID>
Status: QA_PASSED | QA_FAILED

## Test Plan
### Test 1: <Description>
- Type: unit | integration | E2E
- Command: `pytest tests/...`
- Expected: ...
- Actual: ...
- Result: ✓ PASS | ✗ FAIL

## Acceptance Criteria Verification
| AC | Description | Status | Evidence |
|----|-------------|--------|----------|
| AC1 | ... | ✓/✗ | how verified |

## Issues Found
## Verdict
```

## Verification Checklist
- [ ] Все AC выполнены
- [ ] Happy path работает
- [ ] Edge cases обработаны
- [ ] Существующие тесты проходят
