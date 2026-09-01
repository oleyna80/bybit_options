# Evaluation Plans and Observable Evidence

Store approved evaluation plans and non-sensitive observable trajectory evidence here.

Recommended layout:

```text
docs/evals/<evaluation-id>/plan.json
docs/evals/<evaluation-id>/events.jsonl
docs/evals/<evaluation-id>/fixtures/
```

Evaluation plans are assurance configuration, not implementation authority. Trajectory
evidence records observable events only. Do not store private chain-of-thought, hidden
reasoning, secrets, credentials, raw protected data, or unrestricted tool payloads.

Validate an approved plan with:

```bash
python scripts/validate-evaluation.py plan docs/evals/<evaluation-id>/plan.json --require-approved
```
