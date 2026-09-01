---
schema_version: 1
artifact_type: tasklist
work_block_id: [WORK_BLOCK_ID]
specification: [SPECIFICATION_PATH_OR_ID]
specification_revision: [SPECIFICATION_REVISION]
status: draft
---

# Traceable Tasklist — [TITLE]

## Contract

Requirement implementation tasks use stable IDs and explicit requirement,
acceptance, and path/write-set references:

```text
- [ ] TASK-001 [type=requirement] [req=REQ-001] [ac=AC-001] [paths=src/a.py,tests/test_a.py] Implement behavior.
```

Allowed task types:

- `requirement` — implements approved requirements; `req` and `ac` are mandatory;
- `enabling` — setup/foundation work; use `req=-` and `ac=-` when not directly traced;
- `assurance` — tests/evidence support; use `req=-` and `ac=-` when not directly traced;
- `documentation` — derived documentation work; use `req=-` and `ac=-` when not directly traced.

Do not invent fake requirement IDs for enabling or assurance work.

## Setup / Enabling

- [ ] TASK-001 [type=enabling] [req=-] [ac=-] [paths=[PATHS]] [DESCRIPTION]

## Requirement Delivery

- [ ] TASK-010 [type=requirement] [req=REQ-001] [ac=AC-001] [paths=[PATHS]] [DESCRIPTION]

## Assurance

- [ ] TASK-090 [type=assurance] [req=-] [ac=-] [paths=[PATHS]] [DESCRIPTION]

## Documentation / Closeout

- [ ] TASK-100 [type=documentation] [req=-] [ac=-] [paths=[PATHS]] [DESCRIPTION]

## Dependencies and Parallelization

Record dependencies separately when ordering is not obvious:

```text
TASK-010 depends_on TASK-001
TASK-020 parallel_with TASK-030 only when write-sets are disjoint
```

Parallel markers never override one-Coder-per-write-set or isolation requirements.

## Pre-Execution Validation

Run:

```bash
python3 scripts/validate-define-traceability.py \
  --spec [SPECIFICATION_PATH] \
  --tasks [TASKLIST_PATH]
```

A `BLOCKED` result prevents successful pre-execution consistency completion.
