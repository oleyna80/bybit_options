---
description: Data sanity checks and stop-trading rules for options analysis
---

# Skill: Data Quality & Monitoring

## Назначение
Защитить торговые решения от ошибок данных, задержек и аномалий рынка.

## Проверки качества данных
- **Latency**: задержка котировок/обновлений.
- **Spread anomalies**: резкое расширение спредов.
- **Price jumps**: неконсистентные гэпы без событий.
- **Missing data**: нули/пустые поля в IV/Greeks.

## Правила stop‑trading
- При 2+ красных флагах → **PAUSE**.
- При сомнительном IV/skew → снижать размер или выходить.

## Выходной артефакт
Чек‑лист:
```
Latency: OK/ALERT
Spreads: OK/ALERT
Data completeness: OK/ALERT
Decision: TRADE/PAUSE
```

## Интеграция
- Указывать причины паузы в каждой рекомендации/команде.
