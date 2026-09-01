# Auto context Policy

> **Applies to:** VS Code Codex / Cursor / Similar IDE-integrated agents  
> **Does not apply to:** RooCode, CLI agents, API-only integrations

## What Auto context is
Auto context automatically attaches relevant IDE/workspace context (recent/open files, selections) to the prompt.

## Default
- Auto context: ON

Rationale: improves accuracy and reduces manual context wiring for typical dev tasks.

## Force OFF (mandatory)
Turn Auto context OFF when:
1) Handling secrets or credentials (API keys, service account JSON/private keys, tokens, .env.local contents).
2) Working on security-sensitive logic (auth, permissions, signing, encryption).
3) Copying/transforming private user data (real customer details, logs with PII).
4) Doing “clean-room” tasks where only specific files should be used (e.g., writing docs from a provided snippet, generating ADR from a known decision).
5) The repository is large and the agent started hallucinating or pulling unrelated modules into scope (context drift).

## Force ON (recommended)
Turn Auto context ON when:
1) Doing architecture/codebase planning that must reflect current repo structure.
2) Refactoring or implementing across multiple files.
3) Debugging where the agent benefits from surrounding code and related files.

## Manual Context requirement (when OFF)
If Auto context is OFF, the Orchestrator must request explicit context via:
- `@path/to/file` references OR
- user-pasted excerpts OR
- the user highlighting the relevant code blocks

The agent must NOT guess hidden code.

## Token / Noise control (when ON)
When Auto context is ON:
- Prefer Reasoning=Medium for routine tasks to limit token usage.
- If responses become verbose or irrelevant, instruct:
  - switch Reasoning down OR
  - disable Auto context and specify files explicitly.

## Safety reminder
Never paste secrets into chat. Use `.env.local` locally and keep `.env.example` with placeholders only.
