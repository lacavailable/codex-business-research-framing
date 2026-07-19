# Evaluation Rubric

Score the artifact as written. Do not award intent that is not visible in the output.

## 100-point rubric

| Category | Points | Full-credit standard |
|---|---:|---|
| Model fidelity | 25 | Actor, timing, information, behavior, constraints, and objective all match the research. |
| Decision specificity | 15 | The responsible actor, trigger, available choices, timing, and stakes are concrete. |
| Nontrivial trade-off | 15 | Competing consequences arise from a named constraint or mechanism. |
| Mechanism explanation | 10 | The path from choices and uncertainty to outcomes is accurate and understandable. |
| Evidence discipline | 10 | Facts, assumptions, inferences, and unsupported claims are correctly labeled and attributed. |
| Boundary conditions | 10 | Scope, omitted effects, external validity, and operational limits are explicit. |
| Model mapping | 10 | Material objects map consistently to business roles and decision-time status. |
| Managerial clarity | 5 | The narrative is concise, concrete, and readable without hype. |

Record an integer for every category, a `raw_score` from 0 to 100, detected hard failures, and a `reported_score`.

## Hard failures

Flag any of the following:

- invented company facts;
- unsupported market claims presented as facts;
- future or hidden information used at decision time;
- narrative and mathematical objectives mismatch;
- a state variable is treated as a decision;
- the model is changed to improve the story without declaring an extension;
- causal claims lack support;
- major assumptions are hidden;
- social-welfare improvement is claimed when only revenue is optimized.

Preserve the raw score even when a hard failure occurs. Set `reported_score = min(raw_score, 59)` when one or more hard failures are present; otherwise set `reported_score = raw_score`. Use 60 as the default passing threshold.

## Scoring procedure

1. Read the source research specification before the narrative.
2. Score each category independently and cite a short artifact-specific reason.
3. Detect hard failures separately; do not encode them only as point deductions.
4. Apply the cap after calculating the raw score.
5. Report the single most important improvement needed for fidelity.

For blind comparisons, remove condition labels and randomize output order. Use the same case specification for all conditions. Report category means, paired case differences, pass rates, and hard-failure rates; disclose judge model, prompt, run date, same-model judging, and residual contamination risks.
