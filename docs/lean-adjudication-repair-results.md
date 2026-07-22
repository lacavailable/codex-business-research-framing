# Lean adjudication repair results

## Decision

D2R failed. Experimental Skill development is **not authorized**, no Skill file changed, validation and both holdouts remain closed, and no tag or release is permitted.

The five development cases completed all 20 required role records in 22 attempts. One IS-P02 Role A attempt was schema-valid but violated the sealed semantic invariant by marking an uncertain check as material; its dependent Role C record was invalidated, both attempts were preserved privately, and both roles were rerun in fresh contexts. No LLM semantic adjudicator was invoked.

## Gate results

| Metric | Observed | Gate | Result |
| --- | ---: | ---: | --- |
| Privacy and holdouts valid | true | true | pass |
| Required records schema-valid | 100% | 100% | pass |
| Valid evidence-span rate | 92.13% | at least 95% | **fail** |
| Applicability recovery | 100% | at least 95% | pass |
| Material-defect detection | 80% | at least 90% | **fail** |
| Material-fidelity ordering | 80% | at least 90% | **fail** |
| Fidelity false-positive rate | 0% | at most 5% | pass |
| Category localization | 80% | at least 80% | pass |
| Unresolved material-fidelity disagreements | 0 | 0 | pass |
| Material semantic adjudication rate | 0% | at most 30% | pass |
| Procedural corrections valid | true | true | pass |
| Clean controls without new material disagreement | 2 | 2 | pass |
| Combined D2/D2R domain coverage | 4 | 4 | pass |
| Production packets without prestige cues | 100% | 100% | pass |

Procedural correction rate was 40%: IS-P02 and IS-P01 each contained one nonmaterial prose-evidence localization challenge. Their deterministic records preserve the original assessments and citations and change no fidelity, hard-failure, applicability, contrast-ordering, or support-status result.

## Root causes

1. The strict evidence computation found seven assessed or verification records without a valid supporting span. Several concerned explicitly missing actor, timing, or constraint information. Those unknowns were correctly not imputed, but the preregistered 95% requirement was not met under the strict denominator.
2. The frozen contrast-output schema accepted arbitrary `item_id` strings. The MGMT-P02 contrast record used evidence IDs instead of construction item IDs, so its material and mechanism/evidence variants could not be deterministically joined to their preregistered identities. This produced 80% defect detection and 80% material ordering.
3. The exact metric summarizer was not present in freeze commit `817dfe2`; it was implemented after calls began. Thresholds and cases were frozen, but the absent executable denominator specification is a protocol deviation and independently blocks authorization.
4. OM-P02 received two original-passage hard failures (`material_constraint_removed` and `hidden_major_assumption`) although sealed D2 had assigned no original-passage hard failure. The registered false-positive metric covered contrast/paraphrase behavior and therefore did not count this regression; it remains an additional Skill-safety concern.

No result is rescued by changing the evidence denominator, remapping the malformed contrast after inspection, weakening a threshold, or relabeling a semantic disagreement as procedural.

## Resource and preservation accounting

- Five cases and 20 required records completed.
- Twenty-two attempts were used; three of the 25-call ceiling remain.
- One schema-semantic invalid attempt and one dependent invalid attempt were preserved.
- Zero conditional semantic adjudications were used.
- PR #5's D1/D2 records, hashes, 37.5% failure, and prestige diagnostic remain unchanged.
- The five prior prestige effects remain diagnostic: three ordinary unsupported-status penalties, one internal materiality-label inconsistency, and one confounded construction/mapping result.
- No private file is tracked. Production packets contained no source or prestige cues.
- Automated and expert holdouts remain unopened. No human experts participated.

## Next bounded action

A future repair may version the contrast schema to require construction item IDs and preregister the executable evidence denominator before any rerun. This branch records the failure only. It does not rerun D2R, create the Skill branch, open validation, or spend the remaining call capacity.
