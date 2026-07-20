# BusinessBrief Schema

Use schema version `2.0` for new work. The validator continues to accept version `1.0` with its original fields and rules.

## Version 2.0 shared envelope

| Field | Type | Rule |
|---|---|---|
| `schema_version` | string | Exactly `2.0`. |
| `mode` | enum | One of the eight supported modes. |
| `title` | string | Name the decision, not a broad topic. |
| `domain` | enum | `OM`, `IS`, `OR`, or `cross-domain`. |
| `model_supplied` | boolean | State whether a formal model or precise conceptual model was supplied. |
| `input_readiness` | object | Record `stage`, `basis`, `missing_information`, and `maturity_ceiling`. |
| `diagnosis_or_brief` | string | Give the concise result first. |
| `narrative` | string | Describe actor, decision, mechanism, stakes, and trade-off. |
| `decision_structure` | object | Supply all twelve DFC-12 fields. |
| `consistency_gates` | object | Supply all six gates with `status` and `reason`. |
| `eligibility_status` | enum | `eligible`, `ineligible`, or `not_assessed`. |
| `fidelity_audit` | audit | Explicit model-fidelity audit. |
| `managerial_framing_audit` | audit | Explicit managerial-framing audit. |
| `scholarly_positioning_audit` | audit | Explicit contribution and literature-positioning audit. |
| `evidence_audit` | audit | Explicit claim and attribution audit. |
| `prose_audit` | audit | Explicit clarity and presentation audit. |
| `model_mapping` | array | Nonempty when `model_supplied` is true. |
| `claims` | array | Label facts, assumptions, results, literature claims, inferences, and unsupported claims. |
| `boundaries` | array[string] | Give at least one scope limit or countercondition. |
| `primary_remaining_weakness` | string | Name the highest-priority unresolved weakness. |
| `mode_result` | object | Follow the selected v2 mode contract in [output-contracts.md](output-contracts.md). |

Do not add top-level fields to a v2 JSON brief. Keep extensions inside a documented mode result or revise the schema deliberately.

## Input readiness

`input_readiness.stage` and `maturity_ceiling` are integers from 1 through 4, following [input-readiness.md](input-readiness.md). `basis` is a nonempty explanation and `missing_information` is an array of strings. The current stage cannot exceed the maturity ceiling. Missing essential model information normally prevents a Stage 2 ceiling and requires untestable gates to remain `unknown` or `not_assessed`.

```json
{
  "stage": 2,
  "basis": "The supplied model identifies decisions, timing, information, constraints, objective, and mechanism.",
  "missing_information": ["No institutional evidence supports prevalence or magnitude."],
  "maturity_ceiling": 2
}
```

## Decision structure and gates

`decision_structure` requires `actor`, `trigger`, `choices`, `decision_time_information`, `stakes`, `frictions`, `mechanism`, `trade_off`, `counterfactual`, `model_mapping_summary`, `evidence_status_summary`, and `boundaries_summary`. Each value is a nonempty string; use `unknown: ...` rather than invention.

Each of `actor`, `timing`, `information`, `behavior`, `constraints`, and `objective` has this shape:

```json
{"status": "pass", "reason": "The retailer controls the assortment before demand realizes."}
```

Gate status is `pass`, `fail`, `unknown`, or `not_assessed`. Eligibility is deterministic:

- `eligible` if and only if all six gates pass;
- `ineligible` if and only if at least one gate fails;
- `not_assessed` when no gate fails and at least one gate is `unknown` or `not_assessed`.

The `fidelity_audit.status` must correspond: `pass` for `eligible`, `fail` for `ineligible`, and `not_assessed` for `not_assessed`.

## Layer audits

Every audit has exactly these fields:

```json
{
  "status": "pass",
  "findings": ["The decision sequence matches the model."],
  "required_actions": []
}
```

`status` is `pass`, `fail`, or `not_assessed`. `findings` must be nonempty. `required_actions` may be empty only when no revision or additional information is needed. Audit the five layers separately; polished prose cannot compensate for failed fidelity.

## Model mapping

Each v2 row has `model_object`, `model_role`, `business_meaning`, `decision_time_status`, `timing`, `units`, `horizon`, and `fidelity_note`. Use `unknown` or `not_applicable` when a supplied specification omits units or horizon.

Allowed roles are `decision_variable`, `auxiliary_variable`, `state_variable`, `parameter`, `uncertainty`, `observation`, `constraint`, `objective`, `outcome`, and `derived_variable`. Cover every material supplied role; do not invent an object merely to populate every role.

## Evidence claims

Each v2 claim has `statement`, `evidence_status`, `source`, `scope`, and `action`. Allowed evidence labels are `empirical_fact`, `model_assumption`, `simplifying_assumption`, `model_result`, `literature_claim`, `inference`, and `unsupported_claim`. Use `source: null` when support is unavailable. `empirical_fact` and `literature_claim` require a traceable source.

## Version 1.0 compatibility

Version `1.0` keeps the original envelope: `schema_version`, `mode`, `title`, `domain`, `model_supplied`, `diagnosis_or_brief`, `narrative`, `decision_structure`, `consistency_gates`, boolean `eligible`, `model_mapping`, `claims`, `boundaries`, `primary_remaining_weakness`, and `mode_result`. Its gates remain `pass` or `fail`; its mapping rows and five evidence labels remain unchanged; and its original mode-result contracts remain valid. Do not mix v1 and v2 fields.

## Minimal v2 skeleton

```json
{
  "schema_version": "2.0",
  "mode": "create",
  "title": "Synthetic retailer chooses an assortment under shelf capacity",
  "domain": "OM",
  "model_supplied": true,
  "input_readiness": {"stage": 2, "basis": "Model-grounded input.", "missing_information": [], "maturity_ceiling": 2},
  "diagnosis_or_brief": "A capacity-limited assortment decision made before demand realizes.",
  "narrative": "A synthetic retailer selects products before uncertain demand and substitution occur.",
  "decision_structure": {"actor": "...", "trigger": "...", "choices": "...", "decision_time_information": "...", "stakes": "...", "frictions": "...", "mechanism": "...", "trade_off": "...", "counterfactual": "...", "model_mapping_summary": "...", "evidence_status_summary": "...", "boundaries_summary": "..."},
  "consistency_gates": {"actor": {"status": "pass", "reason": "..."}, "timing": {"status": "pass", "reason": "..."}, "information": {"status": "pass", "reason": "..."}, "behavior": {"status": "pass", "reason": "..."}, "constraints": {"status": "pass", "reason": "..."}, "objective": {"status": "pass", "reason": "..."}},
  "eligibility_status": "eligible",
  "fidelity_audit": {"status": "pass", "findings": ["..."], "required_actions": []},
  "managerial_framing_audit": {"status": "pass", "findings": ["..."], "required_actions": []},
  "scholarly_positioning_audit": {"status": "not_assessed", "findings": ["Not requested."], "required_actions": []},
  "evidence_audit": {"status": "pass", "findings": ["..."], "required_actions": []},
  "prose_audit": {"status": "pass", "findings": ["..."], "required_actions": []},
  "model_mapping": [{"model_object": "x", "model_role": "decision_variable", "business_meaning": "offered products", "decision_time_status": "chosen", "timing": "before demand", "units": "binary by product", "horizon": "one selling period", "fidelity_note": "Not realized demand."}],
  "claims": [],
  "boundaries": ["Synthetic setting; no firm-specific claim."],
  "primary_remaining_weakness": "Demand parameters require empirical calibration.",
  "mode_result": {"readiness": "Stage 2 model-grounded framing.", "setting": "...", "managerial_question": "...", "significance": "...", "mechanism": "...", "structural_tension": "...", "evidence_needs": ["..."], "counterconditions": ["..."]}
}
```
