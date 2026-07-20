# Top-journal calibration results

Status: **blocked / preliminary infrastructure only**.

The v0.2 baseline was reproduced, v3 interfaces and scoring were implemented, and a public suite of 168 original synthetic cases was generated with 12 positive analogues, 12 intermediate analogues, 24 negative controls, and 120 one-construct contrasts. Generator records are separated from gold judge-only records and deterministic leakage validation passes.

No lawful private passages or real blinded expert annotations are present. Therefore no expert correlation, expert applicability agreement, paraphrase-equivalence, source-clustered holdout, or prestige-recognition result exists. Development and validation cannot pass the preregistered expert gates, the evaluator is not frozen for holdout, and holdout remains unopened.

Any automated public-synthetic scores are diagnostic only. They do not justify revising the Skill or claiming top-journal validity.

## Public synthetic primary-judge result

Two fresh automated judge variants scored the 112 unlocked development/validation cases, producing 224 schema-valid primary records. The locked 56-case holdout was excluded. The normalized-score Spearman correlation was 0.712, but applicability agreement was only 80.9%, negative hard-failure agreement was 60.0%, and 107 cases (95.5%) triggered adjudication. The preregistered adjudication-rate gate is at most 30%, so calibration failed before adjudication.

The run stopped at that irreversible gate failure. No authoritative reconciled result is reported. The score sets and [machine-readable primary summary](../evals/calibration/results/public-synthetic/primary-summary.json) are public for diagnosis, including the much stronger fidelity/evidence correlations and weaker managerial/scholarly applicability reliability.
