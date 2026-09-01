# SYSTEM CRITICAL INSTRUCTION: SDD ENFORCER

You are operating in **Strict SDD Mode** (Spec-Driven Development) for the `bybit_options` project.

## 1. THE GOLDEN RULE
**⛔ DO NOT WRITE A SINGLE LINE OF PRODUCTION CODE without an [APPROVED] specification.**

Before you modify `.py`, `.js`, `.html` or any other source files, you MUST ensure there is a corresponding specification in `docs/specs/` that describes the change and has been explicitly approved by the user.

## 2. PRE-TASK CHECKLIST
Before starting ANY task, you MUST perform these read-only actions:

1.  **Read Context**: `view_file .memory_bank/activeContext.md`
    *   *Why?* To understand what we are doing right now.
2.  **Check Specs**: Look for the relevant spec in `docs/specs/`.
    *   If **NO SPEC**: Stop. Your only job is to create one using `docs/specs/TEMPLATE.md`.
    *   If **SPEC EXISTS** but not marked `[APPROVED]`: Stop. Ask user to review.
    *   If **SPEC APPROVED**: You may proceed to code.

## 3. EXCEPTION HANDLING
You may bypass the SDD process **ONLY** for:
*   **Exploration/Research**: Reading files to answer questions.
*   **Hotfixes**: Critical bug fixes (must be documented in `.memory_bank/activeContext.md`).
*   **Scaffolding**: Creating the `docs/` structure itself or updating `task.md`.

## 4. ROLE INTEGRATION
*   **Tech Lead**: Writes technical specs in `docs/specs/`.
*   **Discovery Analyst**: Researches codebase and creates PRD/RFC.
*   **Planner**: Creates architecture plans and task decomposition.
*   **Implementer**: Implements approved specs.
*   **Quality Engineer**: Reviews code and runs tests.

---
FAILURE TO FOLLOW THIS PROTOCOL WILL RESULT IN CHAOS. OBEY THE SPEC.
