# Reports

Store requirements-quality reviews, implementation reviews, verification
summaries, evaluation evidence, release notes, and closeout evidence here.

Requirements-quality review is a **Stage 0 specification review**, not Stage 2
implementation assurance. A normal location is:

```text
docs/reports/requirements/<work-block-id>.md
```

Use `docs/templates/requirements-quality-review-template.md`. Its verdict is
Define-stage evidence only and never grants source-write authority.

Suggested filename format: `YYYY-MM-DD-short-topic.md`.

## Evidence lifetime

Reports are point-in-time evidence. They do not become current requirements,
permissions, or merge/deploy authority merely because they remain in the
repository.

For older root-level reports and `reports/**` material created before the current
SDLC migration:

- preserve the historical record;
- verify referenced files/tests/commands against current `main` before relying on
  a claim;
- do not treat `PASSED`, `APPROVED`, or “ready for merge/next stage” as a current
  verdict unless it is bound to the active Work Block/frozen revision;
- treat unverifiable current applicability as `UNKNOWN`;
- never copy historical credential or `.env` handling claims into current
  operational guidance.

The 2026-09-02 documentation audit is recorded in
`docs/reports/DOC-AUDIT-2026-09-02.md`.
