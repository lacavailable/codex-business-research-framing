# Evaluation methodology

## Purpose

The evaluation asks whether the Skill improves business framing while preserving the mathematical and informational structure of a research problem. It is not a test of prose preference alone.

## Benchmark design

The committed benchmark has 30 synthetic cases: 10 each for OM, IS, and OR. Each case records the prompt, model specification, decision-time facts, fidelity requirements, prohibited inferences, evidence needs, hard-failure traps, adversarial status, and tags. Adversarial cases pair an attractive commercial narrative with a mathematical inconsistency.

## Conditions

Each case is run under three isolated conditions:

1. **No Skill:** the agent receives only the serialized case and a request to frame it.
2. **Generic business writing:** the agent receives the same case and a fixed, domain-neutral clarity prompt.
3. **Full Skill:** the agent receives the same case and access to `frame-business-research-problem`.

Generation batches are separated by domain and condition. Prompts, model identifiers, generation settings, outputs, and run timestamps must be retained. Baseline prompts must not include Skill language or expected answers.

## Blinded scoring

Outputs are assigned randomized identifiers and stripped of condition labels before judging. Domain-level judging applies the committed 100-point rubric: model fidelity (25), decision specificity (15), nontrivial trade-off (15), mechanism (10), evidence discipline (10), boundaries (10), model mapping (10), and managerial clarity (5).

Judges preserve the raw category sum. If a hard failure occurs, the report names it and caps the reported score below the passing threshold; it never edits the raw score. Reports include category means and deltas, paired case comparisons, hard-failure counts and rates, and missing-output counts.

## Reproducibility and CI boundary

The comparison harness validates inputs, produces immutable condition prompts, and records raw artifacts. A committed report is valid only when its case and rubric identifiers resolve and aggregate values can be recomputed from its scores.

Deterministic schema and integrity checks run in CI. Generation and model-based judging do not: service changes, sampling, outages, and judge variance would make pull-request status unstable. Rerunning an evaluation therefore requires recording the environment and publishing new raw results rather than silently replacing prior results.

## Interpretation

Report uncertainty and individual failures alongside averages. A high clarity score cannot offset a fidelity hard failure. Results support claims only about the committed synthetic cases, prompts, model versions, and run settings. See [limitations](limitations.md).
