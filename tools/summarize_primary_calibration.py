#!/usr/bin/env python3
"""Summarize two primary public-synthetic judges before adjudication."""

from __future__ import annotations

import argparse
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path

import evaluator_calibration as core


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "evals/calibration/public-metadata/synthetic-suite-manifest.json"


def ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=values.__getitem__)
    output = [0.0] * len(values)
    index = 0
    while index < len(order):
        end = index + 1
        while end < len(order) and values[order[end]] == values[order[index]]:
            end += 1
        rank = (index + end - 1) / 2 + 1
        for item in order[index:end]:
            output[item] = rank
        index = end
    return output


def correlation(left: list[float], right: list[float]) -> float | None:
    if len(left) < 2 or len(left) != len(right):
        return None
    lm, rm = statistics.mean(left), statistics.mean(right)
    numerator = sum((x - lm) * (y - rm) for x, y in zip(left, right))
    denominator = math.sqrt(sum((x - lm) ** 2 for x in left) * sum((y - rm) ** 2 for y in right))
    return numerator / denominator if denominator else None


def load_scores(root: Path, judge_id: str, selected: set[str]) -> dict[str, dict]:
    scores = {}
    for case_id in sorted(selected):
        path = root / judge_id / f"{case_id}.json"
        if not path.is_file():
            raise core.CalibrationError(f"missing score: {path}")
        score = core.calculate_score(core.read_json(path))
        if score["case_id"] != case_id or score["judge_id"] != judge_id:
            raise core.CalibrationError(f"misidentified score: {path}")
        scores[case_id] = score
    return scores


def summarize(score_root: Path) -> dict:
    manifest = core.read_json(MANIFEST)
    metadata = {item["case_id"]: item for item in manifest["records"]}
    selected = {case_id for case_id, item in metadata.items() if item["split"] in {"development", "validation"}}
    first = load_scores(score_root, "judge_a", selected)
    second = load_scores(score_root, "judge_b", selected)
    rubric = core.load_rubric()
    reasons = Counter()
    triggered = 0
    applicability_equal = applicability_total = 0
    hard_positive = hard_positive_total = hard_negative = hard_negative_total = 0
    totals_a, totals_b = [], []
    absolute_differences = []
    categories: dict[str, tuple[list[float], list[float]]] = {
        category: ([], []) for category in core.CATEGORIES
    }
    distributions: dict[str, dict[str, list[float]]] = {
        judge: defaultdict(list) for judge in ("judge_a", "judge_b")
    }
    for case_id in sorted(selected):
        left, right = first[case_id], second[case_id]
        trigger_reasons = core.reconciliation_reasons(left, right, rubric)
        if trigger_reasons:
            triggered += 1
            reasons.update(trigger_reasons)
        if left["normalized_score"] is not None and right["normalized_score"] is not None:
            a, b = float(left["normalized_score"]), float(right["normalized_score"])
            totals_a.append(a)
            totals_b.append(b)
            absolute_differences.append(abs(a - b))
            group = metadata[case_id]["group"]
            distributions["judge_a"][group].append(a)
            distributions["judge_b"][group].append(b)
        for category in core.CATEGORIES:
            lcat, rcat = left["category_results"][category], right["category_results"][category]
            applicability_total += 1
            applicability_equal += lcat["applicability"] == rcat["applicability"]
            if lcat["score"] is not None and rcat["score"] is not None:
                categories[category][0].append(float(lcat["score"]))
                categories[category][1].append(float(rcat["score"]))
        judge_gold_path = next((ROOT / "evals/calibration").rglob(f"{case_id}.judge.json"))
        expected = core.read_json(judge_gold_path).get("contrast") or {}
        expected_failure = expected.get("expected_hard_failure")
        if expected_failure:
            hard_positive_total += 1
            hard_positive += expected_failure in left["hard_failures"] and expected_failure in right["hard_failures"]
        else:
            hard_negative_total += 1
            hard_negative += not left["hard_failures"] and not right["hard_failures"]
    distribution_summary = {
        judge: {
            group: {"count": len(values), "mean": statistics.mean(values), "median": statistics.median(values)}
            for group, values in groups.items()
        }
        for judge, groups in distributions.items()
    }
    return {
        "schema_version": "3.0.0",
        "status": "preliminary_primary_judges_failed_reliability_gate",
        "splits": ["development", "validation"],
        "holdout_opened": False,
        "cases": len(selected),
        "primary_scores": len(selected) * 2,
        "adjudication_triggered_cases": triggered,
        "adjudication_trigger_rate": triggered / len(selected),
        "adjudication_performed": False,
        "stop_reason": "The preregistered adjudication-rate gate (<=0.30) failed irreversibly; expert inputs are also absent.",
        "trigger_reasons": dict(sorted(reasons.items())),
        "applicability_agreement": applicability_equal / applicability_total,
        "normalized_score_spearman": correlation(ranks(totals_a), ranks(totals_b)),
        "normalized_score_mean_absolute_difference": statistics.mean(absolute_differences),
        "category_score_correlations": {
            category: correlation(*values) for category, values in categories.items()
        },
        "positive_hard_failure_agreement": hard_positive / hard_positive_total,
        "negative_hard_failure_agreement": hard_negative / hard_negative_total,
        "score_distributions": distribution_summary,
        "release_eligible": False,
        "limitations": [
            "Public cases are synthetic and have no real expert annotations.",
            "Primary judges are OpenAI model variants; independent model-family separation is not established.",
            "No authoritative reconciled score is reported because 107 cases required adjudication.",
            "Prestige and paraphrase fixtures were not empirically judged.",
            "Holdout, Skill revision, and production evaluation remain blocked."
        ]
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("score_root", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    report = summarize(args.score_root.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
