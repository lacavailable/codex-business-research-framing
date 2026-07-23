# Skill Development Without an Evaluator Freeze

## Decision

Experimental Skill development is permitted from `main` at
`c7a6e0245f682fc0f8609a69e546d7cb39f35e49` using known v0.2 product defects,
deterministic checks, and the bounded eight-task canary defined under
`evals/skill-2.1-canary/`.

This policy does not alter or reinterpret PR #5, PR #6, their failed evaluator
results, or any historical attestation. Evaluator calibration is advisory for
this product-development cycle, not a prerequisite for editing the Skill.

## Authorization boundary

Passing the canary may authorize merging an experimental Skill-development PR.
It does not authorize:

- a performance or superiority claim;
- evaluator-validity or expert-validation language;
- validation-split access;
- either automated or expert holdout access;
- a version tag or GitHub release.

Evaluator validation and the separately authorized automated holdout remain
required before any future performance claim or release tag. No human experts
participate in this development cycle. Automated model roles are not experts,
and their judgments are not gold labels.

## Preserved safeguards

The Skill continues to run readiness assessment, invariant freezing, DFC-12,
the actor, timing, information, behavior, constraint, and objective gates,
model-to-reality mapping, evidence auditing, and boundary auditing. Concision
may change visible rendering but may not weaken these checks.

## Failure policy

The canary specification, tasks, metrics, and acceptance thresholds are frozen
before any output is generated. A failed or incomplete gate produces a candid
development report. It does not trigger evaluator repair, threshold changes,
additional model calls, validation, holdout access, a tag, or a release.
