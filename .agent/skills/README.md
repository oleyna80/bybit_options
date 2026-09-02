# Project Skills

Bootstrap copies the core framework skills into this directory for local agent
routing.

## Canonical installed skills

`.agent/bootstrap-profile.json` is the installation-evidence source for the
portable skill set. For the current `core` profile, canonical skills use the
folder form:

```text
.agent/skills/<skill-name>/SKILL.md
```

Examples include `task-decomposition/SKILL.md` and
`technical-discovery/SKILL.md`.

Flat project-local files such as `.agent/skills/task-decomposition.md` and
`.agent/skills/technical-discovery.md` predate the current portable skill format.
They may be useful as historical context, but they are **not canonical installed
skills** unless a future bootstrap profile explicitly lists them.

A skill provides method only. It never expands the active Work Block write-set,
role authority, runtime capability, integration admission, or Hard Stop
permissions.

Runtime-specific skill mirrors are governed by the resolved bootstrap profile.
Do not assume a `.claude/skills/`, `.codex/`, or other runtime mirror exists when
the profile does not select it.
