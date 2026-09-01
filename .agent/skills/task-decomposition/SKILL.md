---
name: task-decomposition
description: Декомпозиция целей в атомарные задачи с проверяемыми AC и явной requirement/acceptance/write-set трассировкой.
user-invocable: true
allowed-tools:
  - Read
  - Bash(git *)
  - Bash(ls *)
  - Bash(find *)
  - Bash(grep *)
  - Bash(cat *)
  - Bash(rg *)
  - Bash(jq *)
  - Bash(python3 scripts/validate-define-traceability.py *)
---

# Skill: Task Decomposition

## Triggers
- "разбей на задачи", "сделай tasklist", "декомпозиция"

## Rules
1. Одна задача = один проверяемый результат.
2. Явные зависимости.
3. AC только измеримые.
4. Для formal Managed/Assured/Distributed work каждая implementation-задача должна ссылаться на стабильные `REQ-*` и `AC-*` из approved specification.
5. Не создавай фиктивные product requirement IDs для setup/foundation, assurance или documentation. Такие задачи помечай типом `enabling`, `assurance` или `documentation` и используй `req=-`, `ac=-`, если прямой trace отсутствует.
6. Каждая задача имеет явный path/write-set. Параллельность разрешена только для доказуемо непересекающихся write-sets.
7. Используй portable task syntax, когда включена формальная traceability:
   `- [ ] TASK-001 [type=requirement] [req=REQ-001] [ac=AC-001] [paths=src/a.py,tests/test_a.py] Result`.
8. Перед Execute запусти `python3 scripts/validate-define-traceability.py --spec <spec> --tasks <tasklist>` и не представляй `BLOCKED` как проход.
9. Для крупных approved Work Blocks явно задавай `Execution mode: End-to-end autonomous`.
10. Если ожидается большой review/implementation/verification output, явно разрешай subagents в Work Block и не возвращайся к Owner между внутренними стадиями без Hard Stop.
11. Начинай Work Block с `Expected Final Result`: конечного состояния, которое Owner сможет проверить.
12. Разделяй `Must Resolve Before Start` и `Can Resolve During Work`; второе не является BLOCK, если нет Hard Stop.
13. Явно указывай, нужен ли внешний team/runtime или отдельный critic/verifier, и почему.
14. Для значимых Work Blocks заранее задай `Retrospective Plan`: какие evidence, critic value, process misses и framework updates должны быть записаны в closeout.

## Output

Default: `docs/tasklist/<ticket>.tasklist.md`.

For formal traceable work use `docs/templates/traceable-tasklist-template.md`.

Tasklist content includes:
- Task ID
- Task type: requirement | enabling | assurance | documentation
- Requirement IDs / acceptance IDs where applicable
- Objective
- Scope
- Out of scope
- Approved path/write-set
- Depends on / safe parallelization
- Expected Final Result
- Done Criteria
- Acceptance Criteria
- Risk / mitigation
- Verification tier
- Assigned role
- Status
- Stop conditions
- Execution mode
- Subagent authorization
- Execution log requirement
- Retrospective plan and closeout notes requirement

For non-trivial work blocks, use `docs/templates/work-block-template.md`.

## Handoff
- **Success condition**: tasklist создан; implementation-задачи имеют stable TASK/REQ/AC trace, явный write-set и зависимости; enabling/assurance/documentation задачи классифицированы честно; deterministic traceability не BLOCKED.
- **Next**: `spec-consistency-analysis`, затем Critic/Write Gate; Coder только после их разрешения по выбранному profile.
- **Auto-proceed**: 🟢 YES внутри approved Stage 0 scope
- **Hard stop**: NO

## Provenance

- Existing task-decomposition mechanism: local framework capability.
- This traceability enhancement: **adapted** from the Spec Kit benchmark at `github/spec-kit@bf88c9f9a82fa370c7a7257aa2b3cf10b457b65c`, with framework-native stable IDs, explicit write-set validation, task-type exceptions, and existing authority gates retained.
- Novelty claim: none.
