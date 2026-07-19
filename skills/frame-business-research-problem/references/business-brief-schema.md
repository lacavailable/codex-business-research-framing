# BusinessBrief Schema

Use schema version `1.0`. Emit JSON when machine validation is requested; otherwise preserve the same fields in readable Markdown.

## Shared envelope

| Field | Type | Rule |
|---|---|---|
| `schema_version` | string | Exactly `1.0`. |
| `mode` | enum | One of the eight supported modes. |
| `title` | string | Name the decision, not a broad topic. |
| `domain` | enum | `OM`, `IS`, `OR`, or `cross-domain`. |
| `model_supplied` | boolean | State whether a formal model or precise model description was supplied. |
| `diagnosis_or_brief` | string | Give the concise result first. |
| `narrative` | string | Describe actor, decision, mechanism, stakes, and trade-off concretely. |
| `decision_structure` | object | Supply all twelve DFC-12 fields below. |
| `consistency_gates` | object | Supply all six gates with `status` and `reason`. |
| `eligible` | boolean | Equal `true` only when all gates pass. |
| `model_mapping` | array | Required and nonempty when `model_supplied` is true. |
| `claims` | array | Label factual claims and assumptions. |
| `boundaries` | array[string] | State nonempty limits on interpretation or use. |
| `primary_remaining_weakness` | string | Name the highest-priority unresolved weakness. |
| `mode_result` | object | Follow the selected mode contract. |

`decision_structure` requires: `actor`, `trigger`, `choices`, `decision_time_information`, `stakes`, `frictions`, `mechanism`, `trade_off`, `counterfactual`, `model_mapping_summary`, `evidence_status_summary`, and `boundaries_summary`. Use nonempty strings; use `unknown: ...` when the source is incomplete.

Each consistency gate—`actor`, `timing`, `information`, `behavior`, `constraints`, and `objective`—has this shape:

```json
{"status": "pass", "reason": "The retailer controls the assortment before demand is realized."}
```

Each model-mapping row has `model_object`, `model_role`, `business_meaning`, `decision_time_status`, and `fidelity_note`. Use one of these roles: `decision`, `state`, `parameter`, `random_variable`, `observation`, `constraint`, `objective`, `outcome`, `derived_quantity`.

Each claim has `statement`, `evidence_status`, `source`, and `action`. Use one evidence label: `empirical_fact`, `model_assumption`, `simplifying_assumption`, `inference`, or `unsupported_claim`. Use `source: null` if no source is available, and specify the needed verification in `action`.

## Mode result keys

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

For `compare-scenarios`, each scenario contains `name`, `eligible`, `failed_gates`, `model_fit`, `managerial_relevance`, `evidence_plausibility`, `boundary_transparency`, and `rank`. Set `rank` to a positive integer only for eligible scenarios; set it to `null` for ineligible scenarios.

## Minimal JSON skeleton

```json
{
  "schema_version": "1.0",
  "mode": "create",
  "title": "Synthetic retailer chooses an assortment under shelf capacity",
  "domain": "OM",
  "model_supplied": true,
  "diagnosis_or_brief": "A capacity-limited assortment decision made before demand realizes.",
  "narrative": "A synthetic retailer selects products before uncertain demand and substitution occur.",
  "decision_structure": {},
  "consistency_gates": {},
  "eligible": true,
  "model_mapping": [],
  "claims": [],
  "boundaries": ["No claim about a specific retailer."],
  "primary_remaining_weakness": "Demand parameters require empirical calibration.",
  "mode_result": {"business_problem": "Which assortment best uses scarce shelf capacity?"}
}
```

The skeleton shows field placement only; populate the empty required objects and mapping before validation.
