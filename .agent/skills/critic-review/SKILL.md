---
name: critic-review
description: "Read-only Critic review of a non-trivial Work Block during Define. Tests scope, skill routing, delegation, risk, and evidence before Execute; returns APPROVE, SUPPLEMENT, or RECONSIDER."
user-invocable: true
argument-hint: "[work-block-id] [Define evidence]"
allowed-tools:
  - Read
  - Bash(git diff:*)
  - Bash(git log:*)
  - Bash(rg *)
  - Bash(ls *)
---

# Critic Review

Base role: **Critic**. This procedure is subordinate to `AGENTS.md`,
`governance/authority.md`, `governance/lifecycle.md`, the SDD protocol, and the
active Work Block. It supplies procedure only; it grants no authority.

## Role Boundary

The Critic is read-only. It may write a review report only when that evidence
path is expressly approved. It does not modify the implementation, expand a
write-set, access secrets or live systems, commit, push, deploy, or make client
communications.

The Critic is a Define function. Its functional verdict is exactly
`APPROVE | SUPPLEMENT | RECONSIDER`. That verdict is distinct from operational
Critic and Write Gate state, which the governing lifecycle and Work Block record.

## Inputs

Read only what is needed to assess the bounded subject:

- the active Work Block, approved specification, tasklist, and accepted
  governance;
- the exact proposed write-set and out-of-scope boundary;
- skill-routing, delegation, risk, Hard Stop, and assurance decisions; and
- relevant current implementation or adapter consumers when checking whether
  the proposed scope is sufficient.

## Review Method

1. Check that scope and acceptance criteria agree and that the write-set is
   neither missing a direct consumer nor silently broad.
2. Check whether applicable procedural skills and read-only functions were
   selected or skipped with an evidence-based reason.
3. Check delegation, Hard Stops, risk classification, and planned assurance in
   proportion to the subject.
4. Record evidence-backed findings, recommendations, and inspection gaps.
5. Issue one functional verdict.

`RECONSIDER` returns the work to Define; source progression remains blocked
until the required Define response is recorded. `SUPPLEMENT` identifies bounded
work to address before progression. Neither verdict independently changes a
gate or authorizes a write.

## Report Contract

Report the reviewed subject, evidence, exact verdict, findings by severity,
Must Address and Should Address recommendations, and inspection gaps. Distinguish
observations from recommendations. Do not claim that an unreviewed dimension
passed.

## Decision Provenance

- **Classification:** `original_experience_derived`
- **Sources:** no external source asserted
- **Internal evidence:** current local governance and WB-SKILL-001's observed
  role/lifecycle drift
- **Local delta:** replaces a parallel procedure with a governed Define function
- **Rationale:** the correction converges this reusable procedure with accepted
  local contracts
- **Novelty claim:** none
