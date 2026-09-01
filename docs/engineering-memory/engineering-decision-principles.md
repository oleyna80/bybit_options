---
schema_version: 1
artifact_type: engineering_principles
status: framework_baseline
authority: subordinate_to_agents_governance_and_project_requirements
review_trigger: material_change_to_project_scale_risk_model_or_operating_context
---

# Engineering Decision Principles

This document expands the compact engineering posture in `AGENTS.md`. It is a
framework-supplied baseline for project decisions, not a replacement for current
Owner instruction, approved requirements, accepted architecture decisions, or
the active Work Block.

The objective is to choose the **simplest sufficient solution** for the actual
requirement, credible risk, and operating scale.

## 1. Prefer the simplest sufficient solution

Choose the simplest design that reliably satisfies the requirement and its
acceptance criteria. Do not add abstractions, services, gates, protocols,
configuration layers, or infrastructure unless they solve a concrete problem.

Simple does not mean careless. Tests, error handling, recovery, and real security
boundaries remain necessary where requirements or credible risk justify them.

## 2. Complexity must pay for itself

Before materially increasing complexity, identify:

- the concrete failure or risk being addressed;
- how likely and consequential it is in the actual environment;
- the simplest viable alternative;
- implementation, maintenance, debugging, cognitive, and operational cost;
- new failure modes introduced by the mechanism itself.

If the additional mechanism cannot be justified against those costs, prefer the
simpler solution.

## 3. Design for actual scale

Use the real number of users, developers, operators, deployers, deployment
frequency, exposure, data sensitivity, project lifetime, and threat model.

Do not build enterprise-scale controls merely for hypothetical future scale.
Increase architecture and governance when the project creates a real requirement
for them.

## 4. Make security proportional to credible risk

Protect meaningful boundaries such as secrets, authentication and authorization,
externally exposed services, destructive operations, production data, and
supply-chain integrity.

Strong security is appropriate when a credible threat and independent boundary
exist. Do not add elaborate ceremony to low-risk reversible development work
solely because it is theoretically stronger.

## 5. Prefer existing mechanisms

Prefer, in order:

1. an adequate platform/runtime/OS/repository capability;
2. simple configuration;
3. a small local implementation;
4. a custom framework or protocol only when necessary.

Do not rebuild a weaker project-local version of a boundary already enforced more
reliably elsewhere.

## 6. Add complexity incrementally

Start with the minimum reliable implementation. Observe real limitations, then
add controls or abstractions when evidence shows they are needed.

Prefer decisions that are easy to understand, test, debug, roll back, remove, or
replace.

## 7. Distinguish blockers from improvements

Classify findings before changing the system: blocker, material risk,
maintainability issue, optional improvement, or cosmetic preference.

Do not turn every possible improvement into a release blocker or perform a large
refactor solely to make an already sufficient implementation more elegant.

## 8. Optimize total engineering economics

Developer time, agent time, tokens, review effort, debugging effort, and
operational attention are finite resources. Evaluate total cost together with
technical benefit.

A technically valid improvement can still be the wrong decision when its cost is
disproportionate to the problem or risk it removes.

## 9. Every control creates a failure surface

A guardrail, validator, workflow, security gate, abstraction, or automation is
itself software and can fail. Evaluate whether it removes more meaningful failure
modes than it creates.

## 10. Stop when the requirement is satisfied

Once acceptance criteria, relevant security boundaries, and required assurance
are satisfied, prefer completion over additional sophistication.

Further complexity should require a concrete benefit, new evidence, or a new
requirement.

## Default decision rule

When uncertain, choose the simplest reliable and maintainable solution appropriate
to the project's actual scale and credible risk. Escalate complexity only when
evidence, a real boundary, or an explicit requirement justifies it.
