#!/usr/bin/env python3
"""Prepare blinded v3 judge packets and aggregate public calibration scores."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import statistics
import sys
from pathlib import Path
from typing import Any

import evaluator_calibration as core


ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "evals" / "calibration"
RUBRIC = SUITE / "rubrics" / "business-framing-v3.json"
MANIFEST = SUITE / "public-metadata" / "synthetic-suite-manifest.json"
SEED = 20260720


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def indexed_cases() -> dict[str, tuple[dict[str, Any], dict[str, Any]]]:
    result: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    for generator_path, judge_path in core.case_files(SUITE):
        generator = core.read_json(generator_path)
        result[generator["case_id"]] = (generator, core.read_json(judge_path))
    return result


def judge_instructions(judge_id: str) -> str:
    return (
        "Act as a condition-blind rubric judge. Evaluate only the supplied synthetic passage and context; "
        "do not infer publication status, experimental outcomes, or missing facts. Independently determine "
        "passage function and category applicability. A category may be required, optional, or not_applicable. "
        "Score assessed applicable categories on their raw rubric weights; use null for nonapplicable categories. "
        "Use exact short passage excerpts as evidence_spans. Report only schema-valid JSON score records with "
        f"judge_id={judge_id!r}. Run tools/evaluator_calibration.py validate-score on every record."
    )


def prepare(run_dir: Path, chunk_size: int, splits: set[str]) -> dict[str, Any]:
    cases = indexed_cases()
    suite_manifest = core.read_json(MANIFEST)
    permitted = {
        record["case_id"] for record in suite_manifest["records"]
        if record["split"] in splits
    }
    cases = {case_id: value for case_id, value in cases.items() if case_id in permitted}
    if not cases:
        raise core.CalibrationError("selected splits contain no cases")
    rubric = core.read_json(RUBRIC)
    packet_root = run_dir / "packets"
    score_root = run_dir / "scores"
    packet_root.mkdir(parents=True, exist_ok=True)
    score_root.mkdir(parents=True, exist_ok=True)
    summary: dict[str, Any] = {"schema_version": "3.0.0", "seed": SEED, "splits": sorted(splits), "judges": {}}
    for judge_id, salt in (("judge_a", 11), ("judge_b", 29)):
        identifiers = sorted(cases)
        random.Random(SEED + salt).shuffle(identifiers)
        chunks = []
        for index in range(0, len(identifiers), chunk_size):
            selected = identifiers[index:index + chunk_size]
            packet = {
                "schema_version": "3.0.0",
                "judge_id": judge_id,
                "instructions": judge_instructions(judge_id),
                "rubric": rubric,
                "output_directory": str((score_root / judge_id).resolve()),
                "cases": [cases[identifier][0] for identifier in selected],
            }
            path = packet_root / judge_id / f"packet-{index // chunk_size + 1:02d}.json"
            write_json(path, packet)
            chunks.append({"path": str(path.resolve()), "case_ids": selected})
        summary["judges"][judge_id] = chunks
    write_json(run_dir / "packet-manifest.json", summary)
    return {"cases": len(cases), "packets_per_judge": len(summary["judges"]["judge_a"]), "run_dir": str(run_dir)}


def score_path(run_dir: Path, judge_id: str, case_id: str) -> Path:
    return run_dir / "scores" / judge_id / f"{case_id}.json"


def selected_case_ids(run_dir: Path) -> set[str]:
    manifest = core.read_json(run_dir / "packet-manifest.json")
    return {
        case_id for packet in manifest["judges"]["judge_a"]
        for case_id in packet["case_ids"]
    }


def load_primary_scores(run_dir: Path) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    cases = {key: value for key, value in indexed_cases().items() if key in selected_case_ids(run_dir)}
    result: list[dict[str, dict[str, Any]]] = []
    for judge_id in ("judge_a", "judge_b"):
        scores: dict[str, dict[str, Any]] = {}
        for case_id in cases:
            path = score_path(run_dir, judge_id, case_id)
            if not path.is_file():
                raise core.CalibrationError(f"missing {judge_id} score: {path}")
            score = core.calculate_score(core.read_json(path))
            if score["judge_id"] != judge_id or score["case_id"] != case_id:
                raise core.CalibrationError(f"misidentified score: {path}")
            scores[case_id] = score
        result.append(scores)
    return result[0], result[1]


def prepare_adjudication(run_dir: Path, chunk_size: int) -> dict[str, Any]:
    first, second = load_primary_scores(run_dir)
    cases = {key: value for key, value in indexed_cases().items() if key in first}
    rubric = core.load_rubric()
    records = []
    for case_id in sorted(cases):
        reasons = core.reconciliation_reasons(first[case_id], second[case_id], rubric)
        if reasons:
            records.append({
                "case_id": case_id,
                "generator_visible": cases[case_id][0],
                "primary_a": first[case_id],
                "primary_b": second[case_id],
                "adjudication_reasons": reasons,
            })
    packet_root = run_dir / "adjudication-packets"
    paths = []
    for index in range(0, len(records), chunk_size):
        packet = {
            "schema_version": "3.0.0",
            "judge_id": "adjudicator",
            "instructions": judge_instructions("adjudicator") + " Both primary rationales are evidence, not constraints; return an authoritative independent record.",
            "rubric": core.read_json(RUBRIC),
            "output_directory": str((run_dir / "scores" / "adjudicator").resolve()),
            "cases": records[index:index + chunk_size],
        }
        path = packet_root / f"packet-{index // chunk_size + 1:02d}.json"
        write_json(path, packet)
        paths.append(str(path.resolve()))
    write_json(run_dir / "adjudication-manifest.json", {"required": len(records), "packets": paths})
    return {"required": len(records), "packets": len(paths)}


def ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=values.__getitem__)
    result = [0.0] * len(values)
    position = 0
    while position < len(order):
        end = position + 1
        while end < len(order) and values[order[end]] == values[order[position]]:
            end += 1
        rank = (position + end - 1) / 2 + 1
        for item in order[position:end]:
            result[item] = rank
        position = end
    return result


def correlation(left: list[float], right: list[float]) -> float | None:
    if len(left) < 2 or len(left) != len(right):
        return None
    left_mean, right_mean = statistics.mean(left), statistics.mean(right)
    numerator = sum((x - left_mean) * (y - right_mean) for x, y in zip(left, right))
    denominator = math.sqrt(sum((x - left_mean) ** 2 for x in left) * sum((y - right_mean) ** 2 for y in right))
    return numerator / denominator if denominator else None


def hedges_g(high: list[float], low: list[float]) -> float | None:
    if len(high) < 2 or len(low) < 2:
        return None
    pooled_n = len(high) + len(low) - 2
    variance = ((len(high) - 1) * statistics.variance(high) + (len(low) - 1) * statistics.variance(low)) / pooled_n
    if variance <= 0:
        return None
    correction = 1 - 3 / (4 * (len(high) + len(low)) - 9)
    return correction * (statistics.mean(high) - statistics.mean(low)) / math.sqrt(variance)


def aggregate(run_dir: Path, output: Path) -> dict[str, Any]:
    first, second = load_primary_scores(run_dir)
    cases = {key: value for key, value in indexed_cases().items() if key in first}
    manifest = core.read_json(MANIFEST)
    metadata = {record["case_id"]: record for record in manifest["records"]}
    final: dict[str, dict[str, Any]] = {}
    adjudicated = 0
    for case_id in sorted(cases):
        reasons = core.reconciliation_reasons(first[case_id], second[case_id], core.load_rubric())
        adjudicator = None
        if reasons:
            path = score_path(run_dir, "adjudicator", case_id)
            if not path.is_file():
                raise core.CalibrationError(f"missing adjudication score: {path}")
            adjudicator = core.read_json(path)
            adjudicated += 1
        final[case_id] = core.reconcile_scores(first[case_id], second[case_id], adjudicator)
    groups: dict[str, list[float]] = {key: [] for key in ("positive", "intermediate", "negative", "contrast")}
    for case_id, score in final.items():
        if score["normalized_score"] is not None:
            groups[metadata[case_id]["group"]].append(float(score["normalized_score"]))
    group_stats = {
        key: {"count": len(values), "mean": statistics.mean(values), "median": statistics.median(values)}
        for key, values in groups.items()
    }
    ordered = localized = stable_ok = 0
    localized_total = stable_total = 0
    detection_hits = detection_total = 0
    for case_id, (_, gold) in cases.items():
        contrast = gold.get("contrast")
        if not contrast:
            continue
        original = final[contrast["original_case_id"]]
        variant = final[case_id]
        if float(original["normalized_score"]) > float(variant["normalized_score"]):
            ordered += 1
        for category, delta in contrast["expected_declines"].items():
            left = original["category_results"][category]["score"]
            right = variant["category_results"][category]["score"]
            if left is not None and right is not None:
                localized_total += 1
                localized += float(left) - float(right) >= delta
        for category, tolerance in contrast["expected_stable"].items():
            left = original["category_results"][category]["score"]
            right = variant["category_results"][category]["score"]
            if left is not None and right is not None:
                stable_total += 1
                stable_ok += abs(float(left) - float(right)) <= tolerance
        if gold["contrast"]["changed_construct"] in {"actor", "timing", "information", "objective"}:
            detection_total += 1
            expected = contrast["expected_hard_failure"]
            fidelity_decline = float(original["category_results"]["fidelity"]["score"]) - float(variant["category_results"]["fidelity"]["score"])
            detection_hits += expected in variant["hard_failures"] or fidelity_decline >= 9
    applicable_pairs = total_pairs = hard_positive = hard_negative = 0
    hard_positive_total = hard_negative_total = 0
    a_totals, b_totals = [], []
    for case_id in sorted(cases):
        a, b = first[case_id], second[case_id]
        if a["normalized_score"] is not None and b["normalized_score"] is not None:
            a_totals.append(float(a["normalized_score"]))
            b_totals.append(float(b["normalized_score"]))
        for category in core.CATEGORIES:
            total_pairs += 1
            applicable_pairs += a["category_results"][category]["applicability"] == b["category_results"][category]["applicability"]
        expected_failure = cases[case_id][1].get("contrast", {}).get("expected_hard_failure")
        if expected_failure:
            hard_positive_total += 1
            hard_positive += expected_failure in a["hard_failures"] and expected_failure in b["hard_failures"]
        else:
            hard_negative_total += 1
            hard_negative += not a["hard_failures"] and not b["hard_failures"]
    abc = groups["positive"] + groups["intermediate"] + groups["negative"]
    sorted_abc = sorted(abc)
    q1 = statistics.median(sorted_abc[:len(sorted_abc)//2])
    q3 = statistics.median(sorted_abc[(len(sorted_abc)+1)//2:])
    metrics = {
        "group_statistics": group_stats,
        "positive_at_least_85_rate": sum(value >= 85 for value in groups["positive"]) / len(groups["positive"]),
        "positive_intermediate_median_gap": group_stats["positive"]["median"] - group_stats["intermediate"]["median"],
        "positive_intermediate_hedges_g": hedges_g(groups["positive"], groups["intermediate"]),
        "positive_negative_median_gap": group_stats["positive"]["median"] - group_stats["negative"]["median"],
        "positive_negative_hedges_g": hedges_g(groups["positive"], groups["negative"]),
        "contrast_ordering_rate": ordered / len(groups["contrast"]),
        "fidelity_perturbation_detection_rate": detection_hits / detection_total,
        "category_localization_rate": localized / localized_total if localized_total else None,
        "stable_category_rate": stable_ok / stable_total if stable_total else None,
        "applicability_agreement": applicable_pairs / total_pairs,
        "primary_normalized_score_spearman": correlation(ranks(a_totals), ranks(b_totals)),
        "positive_hard_failure_agreement": hard_positive / hard_positive_total if hard_positive_total else None,
        "negative_hard_failure_agreement": hard_negative / hard_negative_total,
        "adjudication_rate": adjudicated / len(cases),
        "abc_at_least_95_rate": sum(value >= 95 for value in abc) / len(abc),
        "abc_interquartile_range": q3 - q1,
    }
    report = {
        "schema_version": "3.0.0",
        "suite": "public-synthetic-calibration-v3",
        "result_status": "preliminary_synthetic_only",
        "release_eligible": False,
        "release_blockers": [
            "No lawfully supplied private passage corpus.",
            "No real blinded expert annotations.",
            "No expert-equivalence review of source paraphrases.",
            "No validated model-family separation attestation.",
            "Locked holdout has not been opened after an evaluator-freeze commit."
        ],
        "fixed_seed": SEED,
        "score_file_hash": hashlib.sha256("".join(json.dumps(final[key], sort_keys=True) for key in sorted(final)).encode()).hexdigest(),
        "metrics": metrics,
    }
    write_json(output, report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare")
    prep.add_argument("run_dir", type=Path)
    prep.add_argument("--chunk-size", type=int, default=21)
    prep.add_argument(
        "--splits", nargs="+", choices=("development", "validation", "holdout"),
        default=("development", "validation"),
        help="Explicit split selection; locked holdout is never selected by default.",
    )
    adj = sub.add_parser("prepare-adjudication")
    adj.add_argument("run_dir", type=Path)
    adj.add_argument("--chunk-size", type=int, default=14)
    agg = sub.add_parser("aggregate")
    agg.add_argument("run_dir", type=Path)
    agg.add_argument("output", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            result = prepare(args.run_dir.resolve(), args.chunk_size, set(args.splits))
        elif args.command == "prepare-adjudication":
            result = prepare_adjudication(args.run_dir.resolve(), args.chunk_size)
        else:
            result = aggregate(args.run_dir.resolve(), args.output.resolve())
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except core.CalibrationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
