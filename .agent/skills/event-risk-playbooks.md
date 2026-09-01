---
description: Event-driven playbooks for options (IV crush/expand, timing, risk)
---

# Skill: Event Risk Playbooks

## Назначение
Структурировать подход к событийному риску (CPI/FOMC/экспирации/релизы) и IV‑динамике.

## Входные данные
- Календарь событий (если доступен)
- Контекст волатильности: `GET /api/v1/volatility/context`

## Типовые паттерны
1. **Pre‑event IV run‑up** → рост IV перед событием.
2. **Post‑event IV crush** → резкое падение IV после события.
3. **Directional gap** → разрыв цены после новости.

## Решения и действия
- До события: ограничить short gamma, избегать узких крыльев.
- После события: пересмотреть short vega (частичная фиксация).
- Всегда фиксировать **временное окно** (когда сценарий актуален).

## Выходной артефакт
```
Event: <name/date>
Expected IV behavior: <run-up/crush>
Strategy: <construction>
Invalidation: <criteria>
```

## Ограничения
- При высокой неопределенности — уменьшить размер или **PAUSE**.
