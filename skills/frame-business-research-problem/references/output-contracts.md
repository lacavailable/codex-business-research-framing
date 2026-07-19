# Output Contracts

Use the shared envelope in [business-brief-schema.md](business-brief-schema.md) for every mode. Keep `diagnosis_or_brief`, `narrative`, claims, boundaries, and the primary weakness visible. Include a mapping whenever a model is supplied.

## `create`

Construct one eligible, fidelity-tested setting. Put the concise researchable problem in `mode_result.business_problem`. If no eligible setting can be created from the supplied invariants, return an ineligible brief and identify missing information instead of fabricating fit.

## `diagnose`

Audit an existing setting. Put `eligible` or `ineligible` in `mode_result.verdict`, list failed gates in `failed_gates`, and list narrative-only repairs in `repairs`. Mark model-changing repairs explicitly as proposed extensions.

## `rewrite`

Return the polished text in `mode_result.rewritten_text`. In `fidelity_changes`, list each substantive change and whether it corrected a mismatch, narrowed a claim, clarified a boundary, or only improved expression. Do not silently repair by changing the model.

## `compare-scenarios`

Evaluate all candidates through the six gates. Put structured candidates in `mode_result.scenarios`; assign `rank: null` to every ineligible candidate. Rank eligible candidates by model fit, then managerial relevance, evidence plausibility, and boundary transparency. State this order in `ranking_basis`; do not compute an compensatory weighted average across gate failures.

## `map-model-to-business`

Put one row per material object in `mode_result.mapping_table` and unresolved semantic conflicts in `mapping_gaps`. Mirror the rows in the shared `model_mapping`. Preserve decision timing, role, units, horizon, and objective scope.

## `audit-assumptions`

Put labeled assumptions in `mode_result.assumptions`. For each, state necessity, sensitivity, business interpretation, and evidence need. Put the assumptions most likely to invalidate the interpretation in `material_risks`.

## `draft-introduction`

Put a compact introduction in `mode_result.introduction`. Establish the actor and trigger, consequential decision, mechanism and trade-off, research gap, model contribution, and bounded managerial relevance. Put externally checkable or causal statements in `claim_checklist`. Avoid invented urgency or market statistics.

## `draft-managerial-implications`

Put model-supported actions and insights in `mode_result.implications`. For each implication, name the decision, condition, predicted consequence, and excluded claim. Put required qualifications in `qualification_checklist`. Do not turn comparative statics or computational speed into realized firm impact without an explicit link.

## Presentation order

When emitting Markdown, use this order:

1. Diagnosis or business brief.
2. Proposed narrative.
3. Mode-specific result.
4. Model-to-reality mapping, when applicable.
5. Unsupported or unverified claims.
6. Boundary conditions.
7. Most important remaining weakness.

Prefer short prose and tables over marketing language. Make failure visible rather than burying it in caveats.
