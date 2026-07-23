# Skill 2.1 Direct Experimental Results

## Decision

The bounded canary completed all 24 authorized calls and **failed** its frozen
acceptance policy. Experimental merge is not authorized. This branch records
the Skill candidate and candid product-development evidence; it does not run
validation, open either holdout, modify evaluator artifacts, create a tag, or
create a release.

## Resource accounting

- Sixteen fresh generation calls used `gpt-5.6-terra` with high reasoning:
  eight tagged-v0.2 outputs and eight Skill 2.1 outputs.
- Eight fresh blinded pairwise calls used `gpt-5.6-sol` with high reasoning.
- Both variants are reported as same-family; independence is not established.
- No retries, replacements, adjudications, or additional model calls occurred.

## Frozen gate results

| Gate | Observed | Required | Result |
|---|---:|---:|---|
| New judged fidelity contradictions | 0 | 0 | pass |
| Frozen unsupported-fact flags | 6 | 0 | **fail** |
| Runtime-to-profit overclaims | 0 | 0 | pass |
| Post-deadline value overclaims | 0 | 0 | pass |
| Compact median word reduction | -2.67% | at least 30% | **fail** |
| Repeated-limitation reduction | 0% | at least 40% | **fail** |
| Profile compliance | 50% | at least 90% | **fail** |
| Visible nonapplicable-layer reduction | 100% | at least 75% | pass, vacuous because both conditions were zero |
| Compact/standard non-tied win rate | 60% (3/5) | at least 60% | pass |
| Full-audit safeguards noninferior | true | true | pass |

The frozen unsupported-fact detector counts any number outside a task allowlist.
It therefore flagged structured full-audit metadata such as schema and stage
numbers as well as one baseline-derived minute difference. This is an
overinclusive deterministic measure, but its specification was frozen before
generation; it is reported rather than repaired after seeing results.

## Output findings

Compact median length was 75 words for v0.2 and 77 words for Skill 2.1. The
candidate's three compact outputs were 25, 85, and 77 words, all below the
120–220-word contract. One standard output was 222 words, below the 250-word
minimum. The four full-audit and remaining standard outputs met their structural
profile checks.

The deterministic issue-marker count was 14 in both conditions. Candidate
outputs exposed no counted nonapplicable layer, but neither did v0.2, so that
gate contains no evidence of improvement.

The blinded judge preferred Skill 2.1 on OM-C01, OM-S02, and OR-C01; preferred
v0.2 on IS-S02, OR-S02, and XD-F01; and tied IS-C01 and XD-F02. No output was
assigned a material fidelity issue. The judge noted one perceived encoding
corruption in a v0.2 OR output; that observation is preserved and not used to
alter any artifact.

## Supported and unsupported conclusions

Supported within this eight-task canary:

- no judged material fidelity regression;
- no detected runtime-to-profit or post-deadline operational-value overclaim;
- full-audit safeguards were noninferior;
- Skill 2.1 achieved exactly the preregistered 60% non-tied win threshold on
  compact and standard tasks.

Not supported:

- compliance with the compact and standard word profiles;
- lower compact length than v0.2;
- reduced repetition under the frozen detector;
- an improvement in nonapplicable-layer suppression;
- general Skill superiority, evaluator validity, expert validation, or release
  eligibility.

## Product-owner review

Eight separately randomized pairs and a blank form are under
`evals/skill-2.1-canary/user-acceptance/`. The condition key remains ignored in
`.local-eval/skill-2.1-canary/uat-key.json` and must not be revealed until the
product owner records preferences. This is product-owner user acceptance
review, not expert review.

## Remaining work

A future, separately authorized development cycle may revise the rendering
instructions using these development findings and preregister a new canary.
Evaluator validation and automated-holdout testing remain prerequisites for a
performance claim or release tag. The expert holdout remains unopened.
