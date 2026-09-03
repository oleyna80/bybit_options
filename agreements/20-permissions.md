# Permissions & Safety

## Workspace access

- Reading and writing files in the repository is allowed.
- The agent must not delete files unless explicitly instructed.
- The agent must never add secrets to the repo.

## Command execution

- Commands may be suggested.
- The agent must never claim commands were executed unless the user provides output.

## Network access

- Treat external network as disabled unless user explicitly enables it.
- Never paste API keys/tokens into chat logs.

## Sensitive changes require explicit confirmation

- CI/CD changes
- deployment changes
- authentication / authorization
- payment flows
- large dependency additions

## Execution Mode: Task-Auto (default)

### Definition: "current task"

The "current task" is the task explicitly named by the user in the last command:

- "Start <TASK-ID>" / "Начни <TASK-ID>"
  Optionally with "(Task-Auto)" suffix.
  If no TASK-ID is explicitly provided, the agent must ask for it and must not proceed.

### Ad-hoc Tasks (without TASK-ID)

If the user gives a one-time analytical task without a TASK-ID (Intent A/B/E/F — research, review, audit, explanation):

- Agent MAY proceed without explicit `Start <TASK-ID>`
- Agent MUST still use `⚙️ Execution: Task-Auto` header
- Agent MUST NOT proceed to any follow-up work without user command
- On completion, use the standard completion format (see below)

Examples of ad-hoc tasks: document audit, code review, explanation, research.

### Task-Auto rules

- Within the CURRENT task card, the Implementer may apply changes immediately (create/edit files, run local checks if requested).
- The agent must NOT start the next task automatically.
- After completing the task, the agent must:
  1. Report exactly what changed (file list + brief summary)
  2. Confirm Acceptance Criteria status (pass/fail)
  3. End with completion statement (see below)

### Mandatory completion report (always)

After finishing a task, the agent MUST output:

1. "✅ Task completed: <TASK-ID>"
2. Files changed/created with FULL paths (grouped by Created/Modified/Deleted)
3. Acceptance Criteria checklist:
   - AC1: pass/fail + brief evidence
   - AC2: pass/fail + brief evidence
4. Commands run (if any) and results (or "not run")
5. Risk notes: any import/compatibility risks introduced
6. **STOP and wait for user command** (see Platform Note below)

### Platform Note (final message format)

Some agent platforms restrict questions in the final completion message.

**Preferred:** End with "Готов к следующей задаче: <NEXT-ID>" or "Ready for next task: <NEXT-ID>".

**If platform allows questions:** May ask "Proceed to next task <NEXT-ID>?"

**In both cases:** Agent MUST NOT start <NEXT-ID> until user explicitly commands "Start <NEXT-ID>".

### Hard stop rule

The agent must never start the next task unless the user replies explicitly with:
"Start <NEXT-TASK-ID>" (or "Начни <NEXT-TASK-ID>").

## Confirmation still required for sensitive actions

Even in Task-Auto mode, require explicit user confirmation for:

- CI/CD changes
- deployment changes
- auth/security-critical changes
- deleting non-generated files
- large dependency additions

## Tooling assumption

- ripgrep (`rg`) is available in the dev environment and may be used for codebase searches.

Report output structure/format unchanged for the same code path. Numeric values may differ due to live data; validate by checking section/table structure and successful generation.

Validation: run python3 main.py, confirm report is generated, and diff shows only timestamp/numeric deltas, no structural changes.

All python smoke-check commands must be run inside the project venv (.venv). If venv is missing, stop and instruct to create/activate it.