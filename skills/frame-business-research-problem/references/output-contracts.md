# Output Contracts

Use the shared envelope in [business-brief-schema.md](business-brief-schema.md)
for requested structured records. New structured work uses version `2.0`;
version `1.0` briefs retain the original contracts listed at the end. Ordinary
Markdown follows [response-profiles.md](response-profiles.md) and need not show
the envelope.

## Version 2.0 contracts

### `create`

Construct one setting without exceeding the readiness ceiling. Require `readiness`, `setting`, `managerial_question`, `significance`, `mechanism`, and `structural_tension` as nonempty strings, plus nonempty-string arrays `evidence_needs` and `counterconditions`. If fidelity cannot be assessed, return provisional framing with `eligibility_status: not_assessed`; if a gate fails, make the setting ineligible rather than polishing over the failure.

### `diagnose`

Return five separate objects: `fidelity`, `managerial_framing`, `scholarly_positioning`, `evidence`, and `prose`. Each contains `status`, `diagnosis`, and `repairs`. Use `pass`, `fail`, or `not_assessed`; make `diagnosis` nonempty and `repairs` an array of concrete revisions or information needs. Declare model-changing repairs as extensions.

### `rewrite`

Return `rewritten_text` and `changes`. `changes` contains arrays for `fidelity`, `evidence`, `scholarly_positioning`, `managerial_framing`, and `prose`. Put every substantive change in the correct layer; do not hide model changes as expression edits.

### `compare-scenarios`

Return `scenarios` and `ranking_basis`. Each scenario contains `name`, `eligibility_status`, `failed_gates`, `model_fit`, `managerial_significance`, `structural_tension`, `evidence_plausibility`, `scholarly_contribution_potential`, `boundary_transparency`, and `rank`. Score the six factors from 0 to 100 only after gating. An `ineligible` scenario has at least one failed gate and `rank: null`; an `eligible` scenario has none and a positive contiguous rank; a `not_assessed` scenario has no failed gate and `rank: null`. Rank eligible scenarios lexicographically by the six factors in the order shown, not by a compensatory weighted average.

### `map-model-to-business`

Return `mapping_table`, `mapping_gaps`, `timing_summary`, `units_summary`, and `horizon_summary`. Mirror `mapping_table` in the shared `model_mapping`. Cover supplied decision and auxiliary variables, parameters, states, uncertainty, observations, constraints, objectives, outcomes, and derived variables. Every row states decision-time status, timing, units, horizon, and a fidelity note; record absent or unresolved semantics as gaps.

### `audit-assumptions`

Return `assumptions` and `material_risks`. Each assumption contains `assumption`, `type`, `necessity`, `business_interpretation`, `tractability_role`, `evidence_status`, `sensitivity`, `boundary`, `model_effect`, and `narrative_effect`. Distinguish assumptions required by the model from claims added only by the story.

### `draft-introduction`

Return `introduction`, `architecture`, and `claim_checklist`. The flexible nine-part `architecture` records `decision_or_phenomenon`, `stakes`, `mechanism_or_tension`, `limitation`, `research_opportunity`, `research_question`, `method_or_model`, `bounded_contribution`, and `bounded_relevance`. Fields may be combined in prose but must remain explicit in the structured audit. Put externally checkable and causal claims in `claim_checklist`.

### `draft-managerial-implications`

Return `implications` and `qualification_checklist`. Each implication contains `actor`, `decision`, `condition`, `mechanism`, `model_supported_consequence`, `evidence_status`, `implementation_requirement`, `excluded_claim`, and `boundary`. If the operational pathway or pre-deadline authority is unresolved, say so rather than issuing a recommendation.

## Version 1.0 contracts

Preserve these keys for v1 briefs:

| Mode | Required keys |
|---|---|
| `create` | `business_problem` |
| `diagnose` | `verdict`, `failed_gates`, `repairs` |
| `rewrite` | `rewritten_text`, `fidelity_changes` |
| `compare-scenarios` | `scenarios`, `ranking_basis` |
| `map-model-to-business` | `mapping_table`, `mapping_gaps` |
| `audit-assumptions` | `assumptions`, `material_risks` |
| `draft-introduction` | `introduction`, `claim_checklist` |
| `draft-managerial-implications` | `implications`, `qualification_checklist` |

## Visible Markdown contract

Select the deliverable before the profile using
[adaptive-output.md](adaptive-output.md). Put the requested usable answer or
manuscript-ready prose first. A fidelity warning, evidence gap, mapping, or
boundary appears only when requested, needed to prevent a material
misunderstanding, or clearly useful for the deliverable. Do not require the
reader to pass through readiness, DFC-12, gate, or layer tables before reaching
the answer.

Use `supported`, `conditionally_supported`, `unsupported`, `contradicted`,
`not_supplied`, `not_assessed`, and `not_applicable` for visible support
statements. Do not use `fail` for missing or nonapplicable material; reserve it
for a material internal gate contradiction.

Give each substantive conclusion, limitation, unsupported pathway, evidence
need, and boundary one visible home. Full-audit and machine-readable records may
repeat a fact only where schema compatibility requires it.

Prefer short prose over marketing language. Make a material failure or
non-assessment visible without exposing every passing check.
