---
name: memory-bank-manager
description: Поддержание актуального состояния operational memory между сессиями.
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

# Memory Bank Manager

## Objective
Keep `memory_bank/` concise and current as operational context and logs.
Promote durable, cross-runtime engineering knowledge to
`docs/engineering-memory/` instead of burying it in local memory.

## Protocols
1. `context.md`: текущий фокус, рабочий scope, next step.
2. `progress.md`: что сделано, что в работе, что дальше; rolling window до 15 записей.
3. `decisions.md`: operational decision summaries and links to durable records.
4. `docs/engineering-memory/`: durable decisions, source-of-truth chains,
   temporary decisions, and reproducibility notes for all agents.

## No-Rot Rule
- Удалять устаревшие формулировки.
- Не дублировать один и тот же статус в разных местах.
- Не оставлять reusable engineering lessons только в `memory_bank/`; при
  closeout классифицировать их как `promoted`, `operational-only`, или
  `not-applicable`.

## Handoff
- **Success condition**: `memory_bank/context.md` и `progress.md` актуальны,
  durable lessons classified, нет отживших формулировок.
- **Next**: возврат Control Tower (продолжение pipeline)
- **Auto-proceed**: 🟢 YES
- **Hard stop**: NO
