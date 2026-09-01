# Specs

Store feature specifications, acceptance criteria, assumptions, exclusions, and
Owner-approved scope decisions here before implementation starts.

For formal Managed/Assured/Distributed work that produces a tasklist, use stable
requirement and acceptance identifiers:

```text
- REQ-001: Required behavior.
- AC-001 [req=REQ-001]: Measurable acceptance criterion.
```

Requirements remain authoritative over plans, tasklists, requirements-quality
reports, validator output, and generated context.

Before technical planning when material ambiguity exists, use the
`requirements-clarification` skill. For formal feature work, run
`requirements-quality-review` before Critic/write-gate completion as required by
`governance/define-quality.md`.

Suggested filename format: `YYYY-MM-DD-short-topic.md`.
