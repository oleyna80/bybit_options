# Evaluation Reports

Store machine-readable evaluation reports here. A report must identify the approved
plan revision, frozen subject revision, runtime, role, actual isolation boundary,
per-criterion evidence, inspection gaps, residual risks, and final evaluation verdict.

Validate a report against its approved plan with:

```bash
python scripts/validate-evaluation.py report \
  docs/reports/evaluations/<evaluation-id>.json \
  docs/evals/<evaluation-id>/plan.json
```

A `READY` evaluation report is assurance evidence. It does not replace the Verifier,
approve architecture, open implementation or deployment gates, or waive deterministic
failures.
