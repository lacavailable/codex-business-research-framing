# Silver-label protocol

_Confidence-graded automated annotations for the no-human calibration pathway_

---

## Terminology

Silver labels are source-grounded automated decisions produced by multiple bounded roles and a separate meta-adjudicator. They are not expert annotations, gold labels, scholar judgments, or external criteria.

| Status | Meaning | Permitted use |
| --- | --- | --- |
| `silver_high_confidence` | Independent role records agree on the material interpretation, required evidence is present, alternatives were considered, and adjudication finds no unresolved conflict | Development, automated validation, or automated holdout subject to source-cluster rules |
| `silver_provisional` | The leading interpretation is supported, but evidence, context, applicability, or role agreement is insufficient for the strict status | Development and diagnostic analysis only |
| `unresolved` | Plausible interpretations remain materially inconsistent or the evidence needed to decide is unavailable | Exclusion from scoring; retain for audit and future review |

## High-confidence requirements

A case may receive `silver_high_confidence` only when:

- Source identity, version, checksum, and relevant context are verified privately
- The required passage function and applicable evaluation layers are explicit
- Model structure and decision-time facts are supported by the available source context
- Each assessed claim identifies a valid private evidence span or an explicit synthetic construction rule
- Atomic fidelity findings distinguish material errors from uncertainty
- The adversarial role addresses a plausible alternative interpretation
- Role disagreements are resolved with an evidence-based rationale
- No unresolved applicability challenge remains
- Anonymization and copyright checks pass

Publication prestige, fluent prose, citation counts, or unanimous unsupported model output cannot satisfy these requirements.

## Applicability challenges

Predetermined synthetic applicability is part of case construction. Private applicability is derived from the requested evaluation profile, passage function, context, and layers actually attempted in the passage.

An annotation role returns either:

- `accept`, preserving the supplied applicability decision; or
- `challenge_with_evidence`, naming the disputed category, proposed status, supporting span, and reason the attempted or required layer changes the decision.

A bare disagreement is invalid. The meta-adjudicator may revise applicability only from valid challenges and must preserve both the original decision and its authoritative rationale.

## Adjudication and provenance

Role outputs are created independently before the meta-adjudicator receives them. The adjudicator cannot invent missing evidence, convert `uncertain` to a material failure without support, or increase confidence solely because several roles use similar language.

Every final record retains role identifiers, exact model/settings metadata, prompt version, case hash, source-cluster identifier, evidence references, disagreement record, adjudication rationale, confidence status, and split assignment. Source-linked evidence remains private; public exports use sanitized IDs, hashes, counts, and aggregate statistics.

## Downgrades and exclusions

Downgrade to `silver_provisional` when the likely interpretation is usable for development but depends on incomplete context, disputed applicability, weak localization, or evidence that does not support materiality. Mark `unresolved` when competing interpretations would change a fidelity finding, passage function, required layer, or contrast expectation.

Only `silver_high_confidence` records may enter validation or holdout. The corpus is not padded to meet a target: insufficient high-confidence coverage blocks freeze.
