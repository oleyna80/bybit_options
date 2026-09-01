# Mode / Model / Reasoning Strategy

Руководство по выбору режима, модели и уровня рассуждения для разных AI-инструментов.

**Поддерживаемые платформы:**
- VS Code Codex (OpenAI)
- RooCode (OpenAI)
- Google Antigravity (Gemini)
- Cursor (Claude)

---

## ⚠️ IMPORTANT: Recommendation vs Active Model

**Ключевое понимание:**

| Аспект | Описание |
|--------|----------|
| **🧠 Recommended: ...** | Это **рекомендация** агента — какая модель/настройки оптимальны для задачи |
| **Active Model** | Модель, которая **фактически работает** — определяется UI/настройками чата |
| **Agent capability** | Агент **НЕ МОЖЕТ** программно переключить модель — только рекомендовать |

### Как читать заголовок задачи:

```
🎭 Active role: Implementer
🎯 Intent: D (Implement)
🧠 Recommended: Mode=Agent Model=Gemini 3 Flash Thinking=Medium  ← РЕКОМЕНДАЦИЯ
⚙️ Execution: Task-Auto (в пределах HEDGER-006)
```

- `🧠 Recommended` = что **лучше** использовать для этой задачи
- Если текущая модель **отличается** от рекомендованной, агент должен сказать:
  > "Switch to: Model=Gemini 3 Flash" (одна строка)
- Затем продолжить работу с **активной** моделью

### Определение активной модели:

Агент не всегда знает, какая модель активна. Варианты:
1. **Пользователь сам указывает** в запросе ("сейчас в чате Claude Opus 4.5")
2. **Агент предполагает** на основе контекста (инструмент, стиль ответов)
3. **Агент спрашивает**, если критично для задачи

### Когда рекомендация критична:

| Сценарий | Действие |
|----------|----------|
| Простая задача (Low complexity) | Продолжить с любой моделью |
| Сложная архитектура (High) | Рекомендовать переключение, но продолжить |
| Критические изменения (Extra High) | Явно спросить пользователя о подтверждении модели |

---

## 🛑 Model Confirmation Pause

При начале новой задачи агент должен **остановиться** и дать пользователю возможность переключить модель.

### Шаблон заголовка задачи:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 Task: HEDGER-006 — Реализовать DeltaHedgerBot
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎭 Active role: Implementer
🎯 Intent: D (Implement)
🧠 Recommended: Model=Gemini 3 Pro, Thinking=Medium
🔌 Active: [определяется пользователем или предполагается]

⚙️ Execution: Task-Auto
🚦 Gates impacted: none
🧩 Context: Auto context=ON

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏸️ PAUSE: Проверьте настройки модели.
   Если нужно переключить — сделайте это сейчас.
   Напишите "Старт" или "Start" для продолжения.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Правила паузы:

| Условие | Действие |
|---------|----------|
| Новая задача (Start TASK-ID) | **ВСЕГДА** показать заголовок и ждать "Старт" |
| Продолжение задачи (тот же контекст) | Не нужна пауза |
| Переключение между ролями | Показать заголовок, ждать "Старт" |
| Простой вопрос (не задача) | Не нужна пауза |
| Ad-hoc задача без TASK-ID (Intent A/B/E/F) | Показать хедер, но Start не обязателен (см. `agreements/20-permissions.md`) |

### Что делать после "Старт":

1. Показать подтверждение: `✅ Начинаю выполнение TASK-ID...`
2. **Task-Auto активируется:** агент выполняет задачу без дополнительных подтверждений (см. `agreements/20-permissions.md`)
3. По завершении — показать результаты согласно Mandatory completion report
4. **STOP и ждать** следующую команду "Start <NEXT-ID>"

> **Связь с Task-Auto:** PAUSE обязателен **перед** началом каждой новой задачи.
> После "Старт" агент работает в Task-Auto режиме до завершения задачи.

### Определение активной модели:

Если пользователь не указал активную модель, агент может:
1. Спросить: "Какая модель сейчас активна?"
2. Предположить на основе инструмента (Antigravity → Gemini, Cursor → Claude)
3. Оставить `[не указано]` и попросить уточнить

## 🔷 VS Code Codex (OpenAI)

### Reality check

The agent cannot programmatically change Mode/Model/Reasoning in VS Code.
Therefore it MUST:

- always recommend Mode/Model/Reasoning in the response header
- if current UI settings are not suitable, ask the user to switch in ONE line
- never claim a switch happened automatically

### Available controls (user switches in UI)

- **Mode**: Chat | Agent | Agent(full access)
- **Model**: GPT-5.2-Codex | GPT-5.1-Codex | GPT-5.1-Codex-Mini | GPT-5 mini | Gemini 3 Flash | Claude Sonnet 4 | ...
- **Reasoning effort**: Low | Medium | High | Extra high

### Available models (January 2026)

| Model | Status | Best for |
|-------|--------|----------|
| **GPT-5.2-Codex** | ✅ GA (Jan 14, 2026) | Complex tasks, large codebase refactoring, agent mode |
| **GPT-5.1-Codex** | ✅ GA | Standard coding tasks |
| **GPT-5.1-Codex-Mini** | ✅ GA | Fast small edits, quick iterations |
| **GPT-5.1-Codex-Max** | Preview | Long-context, complex analysis |
| **GPT-5 mini** | ✅ Included | General questions, no premium requests |
| **Gemini 3 Flash** | ✅ GA (Jan 6, 2026) | Multi-provider option |
| **Claude Sonnet 4** | ✅ Auto-select | Multi-provider option |

> ⚠️ **Deprecation notice (Feb 17, 2026):** GPT-5, GPT-5-Codex → use GPT-5.2-Codex instead

### Default baseline

- Use Agent(full access) ONLY when writing/changing files or running project workflows.
- For planning/review/discussion: Chat or Agent (non-full) is enough.

### Model selection (practical defaults)

| Task Type | Recommended Model | Reasoning |
|-----------|-------------------|-----------|
| Implementation in codebase | GPT-5.2-Codex | Medium |
| Review/QA/careful diff analysis | GPT-5.2-Codex | High |
| Fast small edits | GPT-5.1-Codex-Mini | Low |
| Deep architecture / risk trade-offs | GPT-5.2-Codex | High / Extra high |

### Reasoning effort guide

| Level | Use case |
|-------|----------|
| **Low** | Copy edits, formatting, small UI text |
| **Medium** | Normal coding tasks, wiring endpoints, scoped refactors |
| **High** | Architecture, security, integration design, complex debugging, ADRs |
| **Extra high** | High-stakes changes, multi-system integration, "unknown unknowns" |

---

## � RooCode (OpenAI)

### Reality check

RooCode использует свою систему промптов и ролей (modes).
Модель выбирается в UI, reasoning настраивается автоматически на основе mode.

### Available controls

- **Mode**: Architect | Code | Ask | Debug | Orchestrator | (custom modes)
- **Model**: GPT-5.2-Codex | GPT-5.2 | GPT-5.1-Codex-Mini | ...
- **Reasoning**: Определяется mode автоматически

### Mode → Task mapping

| RooCode Mode | Equivalent Role | Best for |
|--------------|-----------------|----------|
| **Architect** | Planner / Tech Lead | Проектирование, архитектура, ТЗ |
| **Code** | Implementer | Написание кода, рефакторинг |
| **Ask** | Discovery Analyst | Вопросы, исследование, объяснения |
| **Debug** | Quality Engineer | Отладка, поиск багов, тестирование |
| **Orchestrator** | Orchestrator | Координация задач, навигация |

### Model selection (practical defaults)

| Task Type | Recommended Model | RooCode Mode |
|-----------|-------------------|--------------|
| Implementation | GPT-5.2-Codex | Code |
| Architecture / Planning | GPT-5.2-Codex | Architect |
| Review / Analysis | GPT-5.2 | Ask |
| Debugging | GPT-5.2-Codex | Debug |

---

## 🟢 Google Antigravity (Gemini)

### Reality check

Antigravity agent работает в режиме full-access по умолчанию.
Модель выбирается автоматически или через настройки проекта.
Thinking budget контролируется системой.

### Available controls

- **Mode**: Agent (full-access by default)
- **Model**: Gemini 3 Pro | Gemini 3 Flash | Gemini 2.5 Pro (legacy)
- **Thinking budget**: Автоматически (1K-64K токенов)

### Available models (January 2026)

| Model | Status | Best for | Speed |
|-------|--------|----------|-------|
| **Gemini 3 Pro** | 🔜 Preview (Q1 2026) | Сложные задачи, PhD-level reasoning, архитектура | Медленнее |
| **Gemini 3 Flash** | ✅ GA (Dec 17, 2025) | Повседневные задачи, default модель | Быстрый |
| **Gemini 2.5 Pro** | ⚠️ Legacy | Если нужна стабильность | Средний |

> ⚠️ **Deprecation notice:** Gemini 2.5 Pro → use Gemini 3 Pro when available

### Model selection (practical defaults)

| Task Type | Recommended Model | Thinking Level |
|-----------|-------------------|----------------|
| Implementation in codebase | Gemini 3 Flash / Gemini 3 Pro | Medium |
| Review/QA/careful diff analysis | Gemini 3 Pro | High |
| Fast small edits | Gemini 3 Flash | Low |
| Deep architecture / risk trade-offs | Gemini 3 Pro | High / Extra high |
| Tech Lead / Planning | Gemini 3 Pro | High |

### Thinking budget guide

| Level | Budget | Use case |
|-------|--------|----------|
| **Low** | 1K-4K tokens | Простые правки, форматирование |
| **Medium** | 8K-16K tokens | Обычные задачи кодирования, рефакторинг |
| **High** | 24K-32K tokens | Архитектура, безопасность, сложный дебаг |
| **Extra High** | 48K-64K tokens | Критические изменения, multi-system интеграция |

---

## 🔶 Cursor (Claude / Anthropic)

### Reality check

Cursor использует Claude модели. Extended thinking доступен для Claude 3.5+ моделей.
Режим выбирается между Chat и Composer (agentic).

### Available controls

- **Mode**: Chat | Composer (Agent)
- **Model**: Claude 3.5 Sonnet | Claude 3 Opus | Claude 3.5 Haiku | ...
- **Extended thinking**: Включается автоматически для сложных задач (Claude 3.5+)

### Available models

| Model | Best for | Context | Speed |
|-------|----------|---------|-------|
| **Claude 4.5 Sonnet** | Баланс качества и скорости, основная рабочая модель | 200K tokens | Быстрый |
| **Claude 4.5 Opus** | Сложные задачи, глубокий анализ, архитектура | 200K tokens | Медленнее |
| **Claude 4 Haiku** | Быстрые простые задачи, мелкие правки | 200K tokens | Очень быстрый |

### Model selection (practical defaults)

| Task Type | Recommended Model |
|-----------|-------------------|
| Implementation in codebase | Claude 4.5 Sonnet |
| Review/QA/careful diff analysis | Claude 4.5 Opus / Claude 4.5 Sonnet |
| Fast small edits | Claude 4 Haiku |
| Deep architecture / risk trade-offs | Claude 4.5 Opus |

### Reasoning notes

- Claude 4.5+ поддерживает extended thinking для сложных задач
- Для явного включения глубокого анализа: использовать structured prompts
- Для быстрых правок: прямые инструкции без лишних объяснений

---

## 🌐 Cross-platform mapping

Эквивалентные настройки между платформами:

| Task Complexity | VS Code Codex | RooCode | Antigravity | Cursor |
|-----------------|---------------|---------|-------------|--------|
| **Simple** | GPT-5.1-Codex-Mini + Low | GPT-5.1-Codex-Mini + Code | Gemini 3 Flash | Claude 4 Haiku |
| **Normal** | GPT-5.2-Codex + Medium | GPT-5.2-Codex + Code | Gemini 3 Flash (Medium) | Claude 4.5 Sonnet |
| **Complex** | GPT-5.2-Codex + High | GPT-5.2-Codex + Architect | Gemini 3 Pro (High) | Claude 4.5 Opus |
| **Critical** | GPT-5.2-Codex + Extra High | GPT-5.2-Codex + Architect | Gemini 3 Pro (Extra) | Claude 4.5 Opus + extended |

---

## Common rules (all platforms)

### Required behavior

- Every response MUST recommend Mode/Model/Reasoning (platform-specific).
- Every plan MUST include a line: "Recommended reasoning effort: low|medium|high|extra high".
- If settings differ, output exactly one instruction line:
  "Switch to: Mode=..., Model=..., Reasoning=..."
  then proceed.

### Task-Auto switching recommendation

If the user says "Start <TASK-ID>" or "Начни <TASK-ID>" and intent is D (Implement):

**Step 1: Show task header with PAUSE**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 Task: <TASK-ID> — <Task Title>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎭 Active role: Implementer
🎯 Intent: D (Implement)
🧠 Recommended: [see table below]
🔌 Active: [user's current model, if known]

⚙️ Execution: Task-Auto
🚦 Gates impacted: none
🧩 Context: Auto context=ON

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏸️ PAUSE: Проверьте настройки модели.
   Если нужно переключить — сделайте это сейчас.
   Напишите "Старт" или "Start" для продолжения.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Step 2: Wait for user confirmation**

- User says "Старт" / "Start" → proceed with execution
- User switches model and says "Старт" → proceed with new model
- User asks questions → answer, then re-show pause prompt

**Recommended settings by platform:**

| Platform | Recommended Settings |
|----------|---------------------|
| **VS Code Codex** | Mode=Agent(full access), Model=GPT-5.2-Codex, Reasoning=Medium |
| **RooCode** | Mode=Code, Model=GPT-5.2-Codex |
| **Google Antigravity** | Model=Gemini 3 Pro (or Gemini 3 Flash), Thinking=Medium |
| **Cursor (Claude)** | Mode=Composer, Model=Claude 4.5 Sonnet |

### Task-Auto applicability

- Task-Auto is primarily for intent D (Implement).
- For non-Implementer tasks (Discovery Analyst/Planner/Quality Engineer/Tech Writer/Trading Expert), the agent must still stop between tasks,
  but it should not modify repo files unless explicitly requested.
- **PAUSE is required** before starting any new task.

### Task selection rule (new chats)

If a user says "What next?" / "Что дальше?" the Orchestrator must:

1. Identify the active tasklist file (e.g., `docs/tasklist/HEDGER.tasklist.md`)
2. Propose the next task ID based on dependency graph
3. Show task header with PAUSE prompt (see above)
4. Wait for user to explicitly start it ("Старт" / "Start").

---

## Platform detection hints

Агент может определить платформу по:

| Hint | Platform |
|------|----------|
| Упоминание "Codex", "VS Code" в контексте | VS Code Codex |
| Упоминание "RooCode", наличие custom modes | RooCode |
| Упоминание "Antigravity", "Gemini", Google tools | Google Antigravity |
| Упоминание "Cursor", "Claude" | Cursor |

При неясности — спросить пользователя.
