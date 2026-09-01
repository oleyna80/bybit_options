# Task Lists

Store decomposed task lists, stage checklists, and Owner-visible work queues here.

For formal traceable work, use `docs/templates/traceable-tasklist-template.md`.
Requirement implementation tasks follow:

```text
- [ ] TASK-001 [type=requirement] [req=REQ-001] [ac=AC-001] [paths=src/a.py,tests/test_a.py] Implement behavior.
```

Use `type=enabling`, `type=assurance`, or `type=documentation` with `req=-` and
`ac=-` when work does not directly implement a product requirement. Do not invent
fake requirement IDs merely to satisfy traceability.

Before Execute, run:

```bash
python3 scripts/validate-define-traceability.py --spec <spec> --tasks <tasklist>
```

Then run the read-only `spec-consistency-analysis` skill before the applicable
Critic/write gate.

Suggested filename format: `YYYY-MM-DD-short-topic.md`.
