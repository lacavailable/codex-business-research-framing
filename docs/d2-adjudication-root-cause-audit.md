# D2 adjudication root-cause audit

## Status and handling constraints

This audit reconstructs the three sealed D2 adjudications from the ignored private role records and the committed public D2 result. It uses record identifiers, sanitized paraphrase, and evidence-span identifiers only. It does not reproduce source wording or private evidence spans.

The historical D2 result is unchanged: three of eight cases required conditional adjudication (`0.375`), exceeding the frozen `0.30` blocking threshold. D2 therefore remains failed, Skill development remains unauthorized by that run, and both holdouts remain unopened. The classifications below describe root cause; they do not retroactively alter the old metric, threshold, records, or result.

## Classification rule

Each adjudication receives exactly one primary class. A disagreement is semantic when it changes an applicable dimension, support status, denominator, material fidelity conclusion, or hard-failure conclusion. Evidence localization is procedural only when the roles already agree on the finding and status and a compatible span substitution can repair the citation without changing that finding.

## Finding-level reconstruction

### OM-P02 — `material_semantic_disagreement`

| Stage | Sealed conclusion | Localized support |
| --- | --- | --- |
| Role A (`LRA-d72fb33cc0824631`) | `structure_fidelity: supported`; all 15 atomic checks were negative, nonmaterial, and not hard failures. The seller/buyer roles, pre-choice sequence, private ranking, capacity, revenue objective, behavior, and assortment-to-mechanism mapping were treated as preserved. | `ES-001`–`ES-006`; mapping was principally localized to `ES-004`. |
| Role B (`LRB-d73452b900c8fa92`) | `managerial_framing: not_applicable`; `scholarly_positioning: not_applicable`; `evidence_discipline: supported`; `prose_usability: supported`. Role B concluded that the six spans anchored the extracted model claims. | `ES-001`–`ES-006`. |
| Role C (`LRC-17bac46f6be91ef5`) | Confirmed the overall structure result and both nonapplicability decisions. It raised two nonmaterial localization issues in Role A, then materially challenged Role B's evidence result because several substantive feasibility/domain restrictions were not directly localized by the cited spans. | Core structure: `ES-001`–`ES-005`; material evidence challenge: `ES-003`, `ES-004`. |
| Adjudicator (`LAD-80a4684fe8370c91`) | Sustained the material challenge and replaced the fully supported evidence-discipline result with an authoritative material claim-to-span localization gap. It narrowed one challenged subclaim as logically supported but retained the material evidence-coverage defect. It did not find the unlocalized claims false and did not disturb structure fidelity. | `ES-003`, `ES-004`. |

**Trigger:** Role C challenged Role B's `supported` evidence-discipline status, not merely the choice of an interchangeable span.

**Root cause:** Role B generalized from spans supporting the core mechanism to full support for a broader set of constraints and domain restrictions. Because the adjudicator changed the required dimension from supported to materially deficient, the disagreement changed claim-support status. It is therefore `material_semantic_disagreement`, even though the underlying defect concerned localization and no fidelity hard failure changed.

### MGMT-P02 — `applicability_boundary_disagreement`

| Stage | Sealed conclusion | Localized support |
| --- | --- | --- |
| Role A (`LRA-08168d73a0b59771`) | `structure_fidelity: supported`; all 15 atomic checks were negative, nonmaterial, and not hard failures. The actor was treated as the researcher developing an explanation from theory and study data, with bounded transfer to comparable settings. | `ES-001`–`ES-008`. |
| Role B (`LRB-a8a97d71fe5e76dd`) | Accepted all four predetermined dimensions as required and returned `supported` for managerial framing, scholarly positioning, evidence discipline, and prose usability. It treated the scholarly workflow as a decision-oriented practice. | Managerial applicability/finding: `ES-002`, `ES-004`, `ES-006`; other findings: `ES-001`, `ES-003`–`ES-008`. |
| Role C (`LRC-8d3ed4c51379bbd1`) | Confirmed Role A, evidence discipline, and prose usability. It materially challenged managerial-framing applicability because the spans described researcher actions rather than a manager, operating decision, or managerial action. It separately identified a nonmaterial scholarly-positioning localization overstatement. | Applicability challenge: `ES-002`, `ES-004`, `ES-006`; secondary localization issue: `ES-001`, `ES-004`, `ES-005`. |
| Adjudicator (`LAD-6a03de614914a18c`) | Sustained Role C and made managerial framing not required. The ruling left Role A's fidelity result intact. | `ES-002`, `ES-004`, `ES-006`. |

**Trigger:** Role C rejected the predetermined `required` value for managerial framing.

**Root cause:** Applicability was inferred from the practical character of a scholarly workflow rather than from the passage function, actor, intended task, or attempted managerial layer. The authoritative decision changed whether the dimension belonged in the assessment denominator. The primary class is therefore `applicability_boundary_disagreement`. The scholarly span overstatement is secondary and nonmaterial.

### IS-P02 — `applicability_boundary_disagreement`

| Stage | Sealed conclusion | Localized support |
| --- | --- | --- |
| Role A (`LRA-e0648599bce82194`) | `structure_fidelity: supported`; all 15 atomic checks were negative, nonmaterial, and not hard failures. It preserved the two maturity axes, four contexts, contribution objective, and boundaries, and identified the researcher as actor. | `ES-001`–`ES-008`; actor citations were `ES-002`, `ES-003`, `ES-006`. |
| Role B (`LRB-09689cc27c88815f`) | Accepted all four dimensions as required; returned `managerial_framing: not_supported` and `supported` for scholarly positioning, evidence discipline, and prose usability. | Managerial applicability: `ES-005`; managerial finding: `ES-005`, `ES-006`; other findings: `ES-001`–`ES-007`. |
| Role C (`LRC-5d72e985b4dd8e74`) | Confirmed overall structure fidelity and Role B's non-managerial findings. It materially challenged managerial-framing applicability because the objective was research-project contribution rather than a manager-facing decision. It also materially challenged Role A's actor localization and raised a nonmaterial constraints-versus-boundaries localization issue. | Applicability: `ES-005`; actor localization: `ES-002`, `ES-003`, `ES-006`; boundary issue: `ES-007`, `ES-008`. |
| Adjudicator (`LAD-b1e1bc662e69ed87`) | Made managerial framing not applicable, while noting that Role B's conditional `not_supported` observation remained substantively consistent if that dimension were scored. It also made the actor conclusion uncertain on the sealed span evidence without overturning overall structure fidelity. | `ES-002`, `ES-003`, `ES-005`, `ES-006`. |

**Trigger:** Role C disputed both the assessment denominator and actor-evidence localization.

**Root cause:** The predetermined applicability rule treated a research classification framework as managerially assessable merely because its usefulness could be discussed. The adjudicator changed managerial framing from required to not applicable, which changes the denominator. The primary class is therefore `applicability_boundary_disagreement`. Actor localization is a secondary evidence defect because the overall fidelity result remained supported.

## Prestige-effect reconstruction

The public D2 result reports five prestige effects. The table below identifies all five against their opaque batch order. “Magnitude” is the number of categories listed as affected in the sealed contrast record; no numeric score delta was produced. Contrast records contain no confidence field, so confidence is reported as `not_recorded`, not inferred.

| Case | Opaque arm and order | Returned label | Affected categories | Magnitude | Material-fidelity flag | Confidence | Audit interpretation |
| --- | --- | --- | --- | ---: | --- | --- | --- |
| IS-P01 | `ITEM-C` (3rd of 5) | `worse` | scholarly positioning; evidence discipline | 2 | `true` | `not_recorded` | A prestige/canonicity cue was penalized as unsupported. The record simultaneously declares structure fidelity stable but sets the material-fidelity flag, an internal labeling inconsistency. |
| OM-P01 | `ITEM-B` (2nd of 5) | `worse` | scholarly positioning; evidence discipline | 2 | `false` | `not_recorded` | A prestige/status cue was correctly localized to unsupported scholarly and evidentiary claims while structure remained stable. |
| OR-P01 | `ITEM-A` (1st of 5) | `worse` | scholarly positioning; evidence discipline; prose usability | 3 | `false` | `not_recorded` | The status cue was penalized as unsupported and less neutral; the decision structure remained stable. |
| OM-P02 | `ITEM-A` (1st of 5) | `worse` | structure fidelity; evidence discipline | 2 | `false` | `not_recorded` | The arm registered an omitted feasibility restriction even though construction metadata identifies it as prestige-label-only, intends only scholarly positioning to change, and declares fidelity/evidence stable. This is a construction-or-mapping confound, not clean evidence of prestige sensitivity. |
| OR-P02 | `ITEM-B` (2nd of 5) | `worse` | scholarly positioning; evidence discipline | 2 | `false` | `not_recorded` | A prestige/status cue was penalized as an unsupported scholarly claim while structure, managerial framing, and usability remained stable. |

For completeness, the other three prestige arms were returned `equivalent`: IS-P02 `ITEM-D` (4th), MGMT-P01 `ITEM-A` (1st), and MGMT-P02 `ITEM-C` (3rd). Each listed zero affected categories, no material fidelity change, and no recorded confidence.

### Prestige diagnostic conclusion

The five-effect count combines at least three phenomena: intended detection of unsupported status claims, one internal materiality-label inconsistency, and one likely one-construct construction or identity-mapping confound. It is therefore unsuitable as a unitary estimate of prestige bias. Future production packets must remove prestige and source-identity cues recursively; a separately constructed diagnostic arm must validate one-change integrity before judging and must record category effects, magnitude, fidelity status, opaque order, and judge confidence explicitly.

## Repair implications

1. Predetermine applicability before role execution from the requested task, attempted layers, passage function, supplied context, and response profile. Do not infer managerial applicability from general practical usefulness.
2. Permit deterministic span substitution only when roles agree on the dimension, finding, and support status and the replacement is compatible with the packet's `supports` mapping. OM-P02 would not qualify because its support status changed.
3. Separate procedural corrections from semantic adjudications prospectively. The three sealed D2 cases remain semantic under the new definitions.
4. Validate every contrast as a one-construct change before judging. Reject a prestige diagnostic when its observed content or affected categories depart from its construction metadata.
5. Add confidence to future contrast outputs rather than imputing it after the fact.

