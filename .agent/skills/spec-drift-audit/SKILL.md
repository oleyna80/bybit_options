---
name: spec-drift-audit
description: Compare approved specifications, architecture decisions, implementation plans, code, tests, and documentation after implementation. Use before successful closeout when public behavior, APIs, schemas, security boundaries, runtime configuration, or multi-file logic changed.
---

# Specification Drift Audit

## Purpose

Determine whether the implemented system still matches its approved specification
and architecture contracts. This skill does not replace code review or technical
verification:

- Reviewer checks the quality and risk of the diff.
- Verifier checks observable behavior and acceptance criteria.
- Drift Auditor checks agreement between normative intent and delivered artifacts.

## Triggers

Use this skill when any condition applies:

- public behavior, routes, API contracts, schemas, or persistence changed;
- authentication, authorization, payments, webhooks, external providers, or
  security boundaries changed;
- architecture or runtime configuration changed;
- 3 or more implementation files changed;
- the specification changed during implementation;
- implementation introduced behavior not explicitly covered by the approved plan;
- the Work Block uses the Assured governance profile.

It may be skipped for a documented Quick Fix with no behavior, contract, schema,
security, runtime, or governance impact.

## Inputs

Required:

- active Work Block;
- approved specification and its revision;
- relevant accepted architecture decisions;
- approved implementation plan;
- frozen implementation diff or changed-file list;
- review report;
- verification report;
- relevant user-facing or engineering documentation.

If an input is unavailable, record the inspection gap. Do not infer that missing
artifacts are compliant.

## Workflow

1. Identify normative requirements from the approved specification and decisions.
2. Map each requirement to implementation evidence and verification evidence.
3. Identify behavior or architecture added outside the approved specification.
4. Check whether plan deviations were formally accepted and synchronized.
5. Check whether tests prove the normative requirements rather than only the code path.
6. Check whether user-facing and engineering documentation match delivered behavior.
7. Classify every mismatch.
8. Produce a drift report using
   `docs/templates/spec-drift-report-template.md`.

## Classification

- `ALIGNED`: requirement, implementation, evidence, and documentation agree.
- `MISSING_IMPLEMENTATION`: an approved requirement is not delivered.
- `UNSPECIFIED_IMPLEMENTATION`: delivered behavior lacks approved specification.
- `STALE_PLAN`: implementation is valid against the spec, but the plan is outdated.
- `STALE_TEST`: implementation exists, but verification evidence does not prove it.
- `STALE_DOCUMENTATION`: documentation disagrees with delivered behavior.
- `SPEC_CHANGE_REQUIRED`: implementation revealed a legitimate requirement change
  that must be approved before closeout.
- `INSPECTION_GAP`: evidence was unavailable or inaccessible.

## Verdicts

Allowed verdicts: `ALIGNED | ALIGNMENT_REQUIRED | BLOCKED | UNVERIFIED`.

- `ALIGNED`: no material drift; successful closeout may proceed if other gates pass.
- `ALIGNMENT_REQUIRED`: correctable drift exists; update the appropriate normative
  or derived artifact and rerun the audit.
- `BLOCKED`: material requirement or architecture mismatch prevents successful closeout.
- `UNVERIFIED`: required artifacts or evidence were unavailable.

Only `ALIGNED` permits the drift gate to pass.

## Authority

Default authority is read-only for source code, runtime, infrastructure, and data.
The auditor may write only the approved drift report path. It must not silently
change the specification, code, tests, or documentation to make the result appear
aligned.

## Evidence Rules

- cite requirement identifiers or exact specification sections;
- cite implementation paths and symbols;
- cite test names, commands, or report paths;
- distinguish demonstrated evidence from assumptions;
- list uninspected areas explicitly;
- do not request or expose private chain-of-thought.

## Handoff

Return:

- verdict;
- coverage summary;
- drift matrix;
- required corrections;
- inspection gaps;
- residual risks;
- recommended owner for each correction.
