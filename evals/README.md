# Evaluation suite

This directory contains a 30-case synthetic benchmark for model-faithful business framing: 10 Operations Management (OM), 10 Information Systems (IS), and 10 Operations Research (OR) cases. Every example is original. Cases deliberately include appealing narratives that conflict with their mathematical model.

## What is deterministic

`tools/evaluate_benchmark.py` validates the committed case bank, rubric, and prompt configuration; prepares stable prompt packets; blinds condition identities; verifies judge totals and hard-failure caps; and aggregates results. These steps belong in deterministic checks. Language-model generation and judging do not.

Run the structural check:

```console
python tools/evaluate_benchmark.py validate
```

Prepare nine generator packets (three domains by three conditions) in an untracked run directory:

```console
python tools/evaluate_benchmark.py prepare --run-dir .local-eval/v0.1.0-alpha --seed v0.1.0-alpha
```

The preparation step creates 90 records and a `private-manifest.json`. Give each packet to an isolated forward-test agent. Baseline agents receive only their serialized prompt packet. The full-Skill agents may access `skills/frame-business-research-problem/`. Do not expose the private manifest or other conditions' outputs to generators or judges.

Save each generator result as one JSON file in the run's `outputs/` directory, conforming to `schemas/output.schema.json`. Then create domain-level, condition-blind judging packets:

```console
python tools/evaluate_benchmark.py judge-packets \
  --manifest .local-eval/v0.1.0-alpha/private-manifest.json \
  --outputs-dir .local-eval/v0.1.0-alpha/outputs \
  --packet-dir .local-eval/v0.1.0-alpha/judge-packets
```

Use an isolated judge for each domain and save one `schemas/score.schema.json` object per response in `scores/`. Judges see a blind ID, the case, response, and rubric, but not the generation condition. Aggregate only after judging:

```console
python tools/evaluate_benchmark.py aggregate \
  --manifest .local-eval/v0.1.0-alpha/private-manifest.json \
  --scores-dir .local-eval/v0.1.0-alpha/scores \
  --output-dir .local-eval/v0.1.0-alpha/report
```

The default commands reject incomplete sets. `--allow-partial` exists only for debugging; partial summaries are labeled `partial_not_publishable` and must not be presented as benchmark results. Keep raw outputs, private manifests, and judge working files outside the committed repository. Commit a result report only after all 90 outputs and scores have been independently audited.

## Scoring policy

The rubric totals 100 points. A judge awards an integer from zero through each category's weight, using the zero/half/full anchors and concise category rationales. The aggregator recomputes every total. Any listed hard failure caps the score at 69, below the passing score of 70, while retaining the uncapped raw score. It also reports category means, pass rates, hard-failure rates, and paired case deltas for full-Skill versus each baseline.

## Interpretation limits

Prompt packets and blind IDs are reproducible, but language-model sampling and judging remain nondeterministic. A judge from the same model family may favor familiar response patterns. Blinding removes explicit condition labels but cannot prevent a judge from inferring a condition from response style. Synthetic framing scores are not evidence of downstream commercial, causal, or welfare effects.
