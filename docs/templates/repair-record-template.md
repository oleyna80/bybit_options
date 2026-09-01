# Repair Record — [Repair ID]

The fenced JSON object below is machine-readable and is the canonical input to
`scripts/repair-lifecycle.py`. Keep its `allowlist` exactly equal to the changed
paths; do not put dynamic Git/CI counters in this tracked record.

```json
{
  "mode": "NDR",
  "risk": "low",
  "deterministic": true,
  "reversible": true,
  "architecture_decision_required": false,
  "prohibited_domains": {
    "architecture": false,
    "product": false,
    "auth": false,
    "security_boundary": false,
    "public_api": false,
    "schema": false,
    "data": false,
    "deploy": false,
    "dependency_upgrade": false
  },
  "implementation_passes": 1,
  "correction_rounds": 0,
  "allowlist": ["scripts/example.py"],
  "problem": "[deterministic compatibility problem]",
  "root_cause": "[evidenced root cause]",
  "verification_commands": ["python scripts/example.py"],
  "stop_condition": "[ineligibility, scope expansion, or another correction requires Owner decision]",
  "integration_stabilization": {"items": [], "correction_rounds": 0}
}
```
