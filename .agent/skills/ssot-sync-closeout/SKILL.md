---
name: ssot-sync-closeout
description: Точечный post-stage sync в docs, engineering memory, memory_bank и tasklist без переписывания истории.
user-invocable: true
allowed-tools:
  - Read
  - Bash(git *)
  - Bash(ls *)
  - Bash(find *)
  - Bash(grep *)
  - Bash(cat *)
  - Bash(npm *)
  - Bash(npx *)
  - Bash(curl *)
  - Bash(fuser *)
  - Bash(node *)
  - Bash(rg *)
  - Bash(jq *)
---

# Skill: SSOT Sync Closeout

## Triggers
- "обнови memory bank"
- "закрыть stage"
- "sync tasklist/context/progress"
- non-trivial Work Block closeout

## Objective
Поддерживать согласованность между:
- `docs/engineering-memory/*`
- `memory_bank/context.md`
- `memory_bank/progress.md`
- `docs/tasklist/*`

Для каждого non-trivial Work Block этот skill также выполняет Orchestrator
Learning Review. Отдельная команда Owner "запиши урок" не требуется, если
необходимый Engineering Memory path уже входит в утверждённую authority/write-set
текущего Work Block.

## Workflow
1. Сверить факт stage (что реально выполнено и проверено).
2. Проверить acceptance evidence: subagent `DONE` не равен принятию результата;
   нужен scope/AC/checks verdict от Control Tower или Verifier.
3. Классифицировать closeout: `success-closeout` только для `READY`;
   `reporting-only` для `BLOCKED` или `UNVERIFIED`.
4. При reporting-only оставить задачу `blocked`, записать corrective action или
   unresolved dependency и не использовать completed/release-ready/success
   формулировки.
5. Обновить `progress.md` новой записью (done + notes + checks).
6. Обновить `context.md` (current focus + next execution queue + date).
7. Для non-trivial Work Block просмотреть material findings из **Define, Execute, Assure и Close**. Рассматривать как lesson candidates, в частности: recurring failure/recovery patterns, durable invariants, source-of-truth lessons, lifecycle/process defects, verification gaps, reusable operational patterns и rejected approaches с важной evidence-backed причиной.
8. Применить utility filter. Candidate достоин durable promotion только если он
   evidence-backed и способен изменить future planning, execution strategy,
   review, verification, recovery или invariant enforcement. One-off noise,
   speculation, raw transcripts, private chain-of-thought, secrets/private data,
   обычный status history и code facts, которые дешевле проверить live, не
   promoted.
9. Классифицировать reusable knowledge ровно как `promoted`, `operational-only` или `not-applicable`. `none identified` является валидным результатом; не создавать lesson ради заполнения формы.
10. Перед `promoted` проверить существующий `docs/engineering-memory/` на
    дубликат. Если текущая entry уже выражает reusable principle, обновить или
    подтвердить её evidence/review trigger вместо создания новой параллельной
    записи.
11. Для `promoted` записать evidence, scope, reusable principle,
    replacement/mitigation/recovery, authority boundary, review trigger и last
    verified. Promotion разрешена только в Engineering Memory path, уже
    разрешённый текущим Work Block. Candidate discovery/classification не
    расширяет write-set; если нужный path не разрешён, вернуться в Define.
12. Project-specific lesson остаётся project-local. Повторяемость/generalization
    может создать follow-up candidate, но promotion в framework policy/template
    требует отдельного evidence-backed framework Work Block.
13. Если знание operational-only, оставить его в `memory_bank/` или reports.
14. Обновить `decisions.md` если в текущем stage принято архитектурное/runtime решение.
15. Обновить delivery notes в tasklist.
16. Прогнать `rg` на противоречивые старые формулировки.
17. Для local-only ignored SSOT проверить, что Git их действительно игнорирует:
   `git check-ignore -v <paths>`.
18. Прямо проверить новые маркеры статуса/evidence через `rg -n` или `sed -n`,
   потому что `git diff` может быть пустым для ignored files.

## Constraints
- Historical entries не переписывать; supersession/retirement оформлять явно.
- Если проверки не запускались — писать это явно.
- Не добавлять ADR без реального архитектурного решения.
- Не добавлять durable engineering memory без reusable evidence и clear
  future-use trigger.
- Engineering Memory classification не является permission grant и не может
  override Owner/spec/governance/Work Block authority.
- Не создавать automatic project-to-framework synchronization.
- В closeout явно указать, являются ли SSOT-изменения local-only/ignored и
  попадут ли они в публичную историю Git.

## Output
- 5-пунктовый stream summary
- Список измененных SSOT файлов
- Learning Review coverage: Define / Execute / Assure / Close
- Material lesson candidates и disposition либо `none identified`
- Engineering memory classification: `promoted`, `operational-only`, or `not-applicable`
- Updated/deduplicated Engineering Memory entries либо `none`
- Local-only/ignored статус SSOT файлов
- Residual risks

## Handoff
- **Success condition**: learning review выполнен для non-trivial Work Block,
  engineering memory classification recorded, memory_bank обновлён (context,
  progress, decisions при наличии ADR), tasklist обновлён, closeout mode
  соответствует verdict, нет противоречий.
- **Next**: Control Tower (closeout report to Owner)
- **Auto-proceed**: 🟢 YES внутри уже утверждённой closeout/write authority
- **Hard stop**: новый Engineering Memory path вне утверждённого write-set или
  material framework/generalization change -> Define / Owner decision
