# DOC-SYNC: Синхронизация документации

Status: ✅ COMPLETED
Source: Tech Lead Review 2026-01-17
Created: 2026-01-17
Completed: 2026-01-17

---

## Overview

Устранение противоречий в документации проекта. Создание единой иерархии источников истины.

**Причина:** Аудит выявил 6 противоречий между `.clinerules`, `.agent/conventions.md`, и текущим состоянием репозитория.

---

## DOC-001: Создать docs/ops/running.md

**Status:** ✅ DONE

**Priority:** HIGH

**Description:**
Создать единый файл с runtime-конфигурацией: порты, команды запуска, health checks.

**Acceptance Criteria:**
- [x] AC1: Файл `docs/ops/running.md` создан
- [x] AC2: Таблица сервисов (Backend API, Frontend, Delta Hedger)
- [x] AC3: Актуальные порты (8000, 3002)
- [x] AC4: Команды запуска для каждого сервиса
- [x] AC5: Health check endpoints

**Completed:** 2026-01-17

---

## DOC-002: Обновить .agent/conventions.md

**Status:** ✅ DONE

**Depends on:** DOC-001

**Priority:** HIGH

**Description:**
Заменить hardcoded порты/команды на ссылку к `docs/ops/running.md`.

**Acceptance Criteria:**
- [x] AC1: Строка 49 обновлена — ссылка на `docs/ops/running.md`
- [x] AC2: Убраны конкретные порты из conventions.md

**Completed:** 2026-01-17

---

## DOC-003: Архивировать .clinerules

**Status:** ✅ DONE

**Priority:** MEDIUM

**Description:**
Переместить `.clinerules` в `docs/legacy/` с пометкой ARCHIVED.

**Acceptance Criteria:**
- [x] AC1: Директория `docs/legacy/` создана
- [x] AC2: Файл перемещён как `clinerules_december2025.md`
- [x] AC3: Добавлен header с статусом ARCHIVED и датой

**Completed:** 2026-01-17

---

## DOC-004: Создать docs/architecture.md

**Status:** ✅ DONE

**Priority:** MEDIUM

**Description:**
Единый документ архитектуры всей платформы (Risk Engine + Delta Hedger + Frontend).

**Acceptance Criteria:**
- [x] AC1: Файл `docs/architecture.md` создан
- [x] AC2: Описаны все 3 компонента (Risk Engine, Delta Hedger, Frontend)
- [x] AC3: Data Flow диаграмма (mermaid)
- [x] AC4: Список зависимостей

**Completed:** 2026-01-17

---

## DOC-005: Обновить AGENTS.md read order

**Status:** ✅ DONE

**Depends on:** DOC-001, DOC-004

**Priority:** LOW

**Description:**
Добавить новые документы в Read Order.

**Acceptance Criteria:**
- [x] AC1: `docs/ops/running.md` добавлен в read order
- [x] AC2: `docs/architecture.md` добавлен в read order

**Completed:** 2026-01-17

---

## Completion Summary

All 5 tasks completed. DOC-SYNC tasklist is **CLOSED**.

**Successor tasks:** See [`PRODUCT.tasklist.md`](PRODUCT.tasklist.md) for next phase.
