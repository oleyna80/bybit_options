---
description: Post-trade PnL attribution and structured learning for options
---

# Skill: Post‑Trade Attribution

## Назначение
Разбирать результаты сделок через факторную атрибуцию (direction/vol/time) и фиксировать уроки.

## Входные данные
- Сделка(и) + контекст входа/выхода
- Логи/заметки трейдера

## Атрибуция PnL
1. **Direction** (Δ) — движение базового
2. **Volatility** (ν) — изменение IV
3. **Time decay** (θ) — эффект времени
4. **Execution** — проскальзывание, спреды

## Выходной артефакт
Таблица:
```
| Trade | Direction | Vol | Theta | Execution | Net PnL | Lesson |
```

## Правила
- Если ошибка процесса → формализовать правило.
- Если нормальная дисперсия → указать, что это «ожидаемо».

## Интеграция
- Обновлять `docs/knowledge/ANTI_PATTERNS.md` или `WINNING_PLAYS.md`.
