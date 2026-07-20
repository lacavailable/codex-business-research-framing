# Automated calibration results

_Public status record for `v0.3.0-experimental.1` automated source-grounded triangulation_

---

## Current result

**Status: not yet authorized.** No passing Tier A result is recorded at this stage. The replacement automated development and validation study, evaluator freeze, automated holdout, and production benchmark must complete before an experimental release can be eligible.

| Item | Current public status |
| --- | --- |
| Baseline commit | `540e72071ea35be228ef4c72c1b3276223631a44` |
| Existing Skill | v0.2 remains unchanged during PR A |
| Private corpus | 17 retained sources and 24 candidate passage notes; copyrighted text remains ignored |
| Earlier public-synthetic calibration | Failed its preregistered adjudication-rate gate; diagnostic only |
| Replacement automated development | Pending |
| Replacement automated validation | Pending |
| Evaluator freeze | Not authorized |
| Automated holdout | Unopened |
| Original expert holdout | Unopened and unchanged |
| Human expert participation | None |
| Tier A release authorization | False until the canonical attestation proves every required gate |
| Tier B formal authorization | False; no real blinded expert annotations exist |

## Interpretation

Infrastructure checks or synthetic fixture success do not count as calibration success. Source-grounded role records must produce enough `silver_high_confidence` cases, pass development and validation gates, and support an auditable freeze before the automated holdout can be opened.

When results exist, this document will report confidence counts, domain and split coverage, applicability agreement, atomic fidelity performance, contrast ordering and localization, paraphrase invariance, prestige and style effects, negative-control rejection, inter-run stability, evidence sufficiency, score distributions, adjudication rate, failures, and stop decisions. All findings will be labeled **automated source-grounded triangulation**.

## Claims not supported

The current work does not support claims of expert validation, scholar approval, external criterion validity, publication readiness, proven superiority, or independent model-family replication. Automated roles are not experts, silver labels are not expert labels, and private journal passages are anchors rather than a representative sample of academic quality.

If any preregistered gate fails, the failure result will replace this pending status, the automated holdout state will be preserved, and no `v0.3.0-experimental.1` tag or release will be created.
