---
description: Research hygiene, signal validation, and anti-overfit discipline
---

# Skill: Signal Validation & Research Hygiene

## Назначение
Проверять торговые гипотезы и сигналы без data‑snooping и overfit.

## Принципы
- **No single-metric decisions**: минимум два независимых подтверждения.
- **Out-of-sample проверка**: отделять период теста от периода подбора.
- **Robustness**: устойчивость по рынкам/периодам/режимам.

## Проверки
1. **Hypothesis clarity**: что именно должно происходить и почему.
2. **Metric definition**: как измеряем успех/провал.
3. **Regime sensitivity**: в каких режимах сигнал ломается.

## Решения и действия
- Если сигнал нестабилен → снизить вес в решении или исключить.
- Если зависит от одного параметра → зафиксировать риск переобучения.

## Выходной артефакт
Короткий отчёт:
```
Hypothesis:
Evidence:
Failure modes:
Confidence (Low/Med/High):
```

## Ограничения
- Не «подгонять» метрику под желаемый результат.
