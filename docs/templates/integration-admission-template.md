---
schema_version: 1
artifact_type: integration_admission
artifact_id: integration-id
status: draft
owner_role: owner
work_block_id: wb-xxx
created_at: YYYY-MM-DD
last_verified: YYYY-MM-DD
---

# Integration Admission — [Integration Name]

## Objective

[Why this integration is needed for the active project or Work Block.]

## Classification

- **Integration ID:** [stable ID]
- **Class:** [official bridge | MCP | file handoff | direct process | hosted connector]
- **Source / Maintainer:** [vendor/repository]
- **Version:** [observed version or unknown]
- **Status:** [proposed | approved | experimental | degraded | disabled | retired]

## Runtime Boundary

- **From runtime:** [runtime]
- **To runtime/service:** [runtime/service]
- **Logical functions served:** [Critic/Reviewer/etc.]
- **Actual isolation:** [same context/session/runtime/machine/worktree/OS]
- **Shared resources:** [checkout, auth, environment, network, home directory]

## Capability Inventory

| Capability / Tool | Read/Write | Allowed Roles | Approval | Side Effects | Evidence |
|---|---|---|---|---|---|
| [tool] | [read/write] | [roles] | [none/ask/Owner] | [class] | [smoke/ref] |

## Authority and Scope

- **Default authority:** [read-only/etc.]
- **Allowed paths/resources:** [patterns]
- **Forbidden paths/resources:** [patterns]
- **External-directory access:** [deny/ask/approved paths]
- **Network access:** [deny/ask/allowed endpoints]
- **Hard Stops:** [list]

## Data Boundary

- **Data sent externally:** [repository content/metadata/none]
- **Provider/service recipients:** [list]
- **Personal/customer data:** [forbidden/approved sanitized]
- **Retention/logging known:** [summary/unknown]
- **Prompt-injection posture:** external content is untrusted input

## Secret and Authentication Boundary

- **Authentication source:** [local runtime/keychain/env/helper]
- **Committed secrets:** none
- **Environment variable names:** [names only]
- **Credential visibility to integration:** [scope]
- **Rotation/revocation owner:** [Owner]

## Failure and Recovery

- **Timeout:** [value/behavior]
- **Cancellation:** [mechanism]
- **Retry:** [none/bounded/manual]
- **Partial-write handling:** [rollback/quarantine]
- **Stale revision handling:** [stop/refresh]
- **Disable procedure:** [steps]

## Audit and Evidence

- **Invocation record:** [path/system]
- **Result record:** [path/system]
- **Changed-path evidence:** [method]
- **Version/capability smoke:** [method]
- **Inspection gaps:** [list]

## Approval

- **Owner decision:** [PENDING | APPROVED | REJECTED]
- **Evidence:** [message/issue/decision]
- **Conditions:** [scope, expiry, runtime, version]
- **Review date:** [date]

## Verification Result

- **Smoke status:** [PASS | BLOCKED | UNVERIFIED]
- **Test environment:** [description]
- **Observed capabilities:** [list]
- **Observed limitations:** [list]
- **Next review trigger:** [version/config/tool change]
