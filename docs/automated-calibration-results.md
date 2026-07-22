# Automated calibration results

_Public status record for `v0.3.0-experimental.1` automated source-grounded triangulation_

---

## Current result

**Status: incomplete and not authorized.** The development run stopped when fresh-context automated-role execution became unavailable. This is an execution-capacity blocker, not a passed or failed calibration gate. Validation, evaluator freeze, both holdouts, Skill revision, production benchmarking, tagging, and release remain locked.

| Item | Current public status |
| --- | --- |
| Baseline commit | `540e72071ea35be228ef4c72c1b3276223631a44` |
| Existing Skill | v0.2 remains unchanged during PR A |
| Private corpus | 17 retained sources and 24 candidate passage notes; copyrighted text remains ignored |
| Earlier public-synthetic calibration | Failed its preregistered adjudication-rate gate; diagnostic only |
| Replacement automated development | Incomplete: 8 context packets, 15 of 64 primary role records, 1 fully role-annotated case |
| Private contrast construction | 14 one-construct variants completed for one development case; not scored |
| Silver labels | 0 high-confidence, 0 provisional, 0 unresolved decisions; meta-adjudication did not complete |
| Replacement automated validation | Not opened |
| Evaluator freeze | Not authorized |
| Automated holdout | Unopened |
| Original expert holdout | Unopened and unchanged |
| Human expert participation | None |
| Tier A release authorization | False until the canonical attestation proves every required gate |
| Tier B formal authorization | False; no real blinded expert annotations exist |

## Interpretation

The completed records establish that the packet, role, applicability, atomic-fidelity, and contrast interfaces can be exercised while private source text remains ignored. They do not estimate evaluator reliability. The public-safe partial export is recomputable from ignored records and deliberately reports completion counts rather than imputed scores.

Development cannot pass until every required fresh-context role, contrast assessment, and meta-adjudication is complete. No missing role is treated as agreement, no provisional record is promoted to `silver_high_confidence`, and no validation or holdout case is opened to compensate for incomplete development.

The current public status is stored in `evals/automated-triangulation/results/development-partial.json`. All findings remain labeled **automated source-grounded triangulation**.

## Claims not supported

The current work does not support claims of expert validation, scholar approval, external criterion validity, publication readiness, proven superiority, or independent model-family replication. Automated roles are not experts, silver labels are not expert labels, and private journal passages are anchors rather than a representative sample of academic quality.

Work may resume from the ignored role records when fresh-context execution is available. Until then, the Tier A attestation remains incomplete and no PR B, tag, or release is authorized.
