#!/usr/bin/env python3
"""Validate v3 calibration records, detect leakage, and reconcile scores."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from collections.abc import Iterable
from decimal import Decimal, ROUND_HALF_UP
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, NamedTuple


ROOT = Path(__file__).resolve().parents[1]
CALIBRATION = ROOT / "evals" / "calibration"
RUBRIC_PATH = CALIBRATION / "rubrics" / "business-framing-v3.json"
GENERATOR_SCHEMA = CALIBRATION / "schemas" / "generator-visible.schema.json"
JUDGE_SCHEMA = CALIBRATION / "schemas" / "judge-only.schema.json"
SCORE_SCHEMA = CALIBRATION / "schemas" / "score-v3.schema.json"

CATEGORIES = (
    "fidelity",
    "managerial_framing",
    "scholarly_positioning",
    "evidence_discipline",
    "prose_clarity",
)
FORBIDDEN_GENERATOR_KEYS = {
    "applicable_categories",
    "gold_fidelity_facts",
    "acceptable_interpretations",
    "prohibited_model_changes",
    "evidence_boundaries",
    "expected_strengths",
    "expected_weaknesses",
    "case_specific_anchors",
    "expert_quality_level",
    "expert_review_status",
    "quality_level",
    "group",
    "split",
    "contrast",
    "hard_failure_traps",
    "fidelity_requirements",
    "prohibited_inferences",
}
SENSITIVE_JUDGE_FIELDS = (
    "prohibited_model_changes",
    "expected_strengths",
    "expected_weaknesses",
    "case_specific_anchors",
    "contrast",
)
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "in",
    "is", "it", "of", "on", "or", "that", "the", "their", "this", "to", "was",
    "when", "which", "with", "without",
}


class CalibrationError(ValueError):
    """Raised when a deterministic calibration invariant fails."""


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CalibrationError(f"{path}: cannot read UTF-8 JSON: {exc}") from exc


def validate_schema(instance: Any, schema_path: Path, label: str) -> None:
    try:
        import jsonschema
    except ImportError as exc:  # pragma: no cover - development dependency guard
        raise CalibrationError("jsonschema is required for calibration validation") from exc
    try:
        jsonschema.Draft202012Validator(read_json(schema_path)).validate(instance)
    except jsonschema.ValidationError as exc:
        location = "/".join(str(part) for part in exc.absolute_path)
        raise CalibrationError(f"{label}: schema failure at {location or '<root>'}: {exc.message}") from exc


def load_rubric(path: Path = RUBRIC_PATH) -> dict[str, Any]:
    rubric = read_json(path)
    if tuple(category["id"] for category in rubric.get("categories", [])) != CATEGORIES:
        raise CalibrationError("v3 rubric categories or order are invalid")
    for category in rubric["categories"]:
        if Decimal(str(category["minimum"])) > Decimal(str(category["weight"])):
            raise CalibrationError(f"{category['id']}: minimum exceeds weight")
    if rubric["hard_failure_cap"] >= rubric["passing_score"]:
        raise CalibrationError("hard-failure cap must be below the passing threshold")
    return rubric


def nested_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            keys.add(str(key))
            keys.update(nested_keys(child))
    elif isinstance(value, list):
        for child in value:
            keys.update(nested_keys(child))
    return keys


def flatten_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [text for child in value.values() for text in flatten_strings(child)]
    if isinstance(value, list):
        return [text for child in value for text in flatten_strings(child)]
    return []


def normalized_tokens(text: str) -> list[str]:
    return [token for token in re.findall(r"[a-z0-9]+", text.casefold()) if token not in STOPWORDS]


def ngrams(tokens: list[str], width: int = 5) -> set[tuple[str, ...]]:
    return {tuple(tokens[index:index + width]) for index in range(max(0, len(tokens) - width + 1))}


class LeakageFinding(NamedTuple):
    kind: str
    judge_field: str
    detail: str


def phrase_overlap(generator: dict[str, Any], judge: dict[str, Any]) -> list[LeakageFinding]:
    """Detect answer-like overlap while allowing shared factual context fields."""
    generator_text = " ".join(flatten_strings(generator))
    generator_tokens = normalized_tokens(generator_text)
    generator_ngrams = ngrams(generator_tokens)
    generator_content = set(generator_tokens)
    findings: list[LeakageFinding] = []
    for field in SENSITIVE_JUDGE_FIELDS:
        for phrase in flatten_strings(judge.get(field)):
            phrase_tokens = normalized_tokens(phrase)
            if len(phrase_tokens) < 5:
                continue
            common_ngrams = generator_ngrams & ngrams(phrase_tokens)
            if common_ngrams:
                sample = " ".join(next(iter(common_ngrams)))
                findings.append(LeakageFinding("token_5gram", field, sample))
                continue
            phrase_content = set(phrase_tokens)
            union = generator_content | phrase_content
            jaccard = len(generator_content & phrase_content) / len(union) if union else 0.0
            compact_generator = " ".join(generator_tokens)
            compact_phrase = " ".join(phrase_tokens)
            similarity = SequenceMatcher(None, compact_generator, compact_phrase, autojunk=False).ratio()
            if len(phrase_tokens) >= 8 and (jaccard >= 0.75 or similarity >= 0.88):
                findings.append(
                    LeakageFinding("semantic_phrase_overlap", field, f"jaccard={jaccard:.3f}; sequence={similarity:.3f}")
                )
    return findings


def validate_case_pair(generator: dict[str, Any], judge: dict[str, Any]) -> list[LeakageFinding]:
    validate_schema(generator, GENERATOR_SCHEMA, f"generator {generator.get('case_id')}")
    validate_schema(judge, JUDGE_SCHEMA, f"judge {judge.get('case_id')}")
    if generator["case_id"] != judge["case_id"]:
        raise CalibrationError("generator and judge records have different case IDs")
    if generator["domain"] != judge["domain"]:
        raise CalibrationError(f"{generator['case_id']}: domain differs across the split")
    forbidden = sorted(nested_keys(generator) & FORBIDDEN_GENERATOR_KEYS)
    if forbidden:
        raise CalibrationError(f"{generator['case_id']}: generator record leaks forbidden keys: {', '.join(forbidden)}")
    return phrase_overlap(generator, judge)


def category_policy(rubric: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {category["id"]: category for category in rubric["categories"]}


def decimal(value: Any) -> Decimal:
    return Decimal(str(value))


def display_number(value: Decimal | None) -> float | None:
    return None if value is None else float(value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP))


def calculate_score(score: dict[str, Any], rubric: dict[str, Any] | None = None) -> dict[str, Any]:
    rubric = rubric or load_rubric()
    validate_schema(score, SCORE_SCHEMA, f"score {score.get('case_id')}/{score.get('judge_id')}")
    policies = category_policy(rubric)
    earned = Decimal("0")
    available = Decimal("0")
    required_missing = False
    required_minimum_failed = False
    for category_id in CATEGORIES:
        result = score["category_results"][category_id]
        applicability = result["applicability"]
        status = result["assessment_status"]
        raw_score = result["score"]
        weight = decimal(policies[category_id]["weight"])
        minimum = decimal(policies[category_id]["minimum"])
        if applicability == "not_applicable":
            if status != "not_applicable" or raw_score is not None or result["evidence_spans"]:
                raise CalibrationError(f"{category_id}: nonapplicable result must have null score and no evidence spans")
            continue
        if status == "not_applicable":
            raise CalibrationError(f"{category_id}: applicable category cannot use not_applicable assessment status")
        if status == "not_assessed":
            if raw_score is not None or result["evidence_spans"]:
                raise CalibrationError(f"{category_id}: unassessed result must have null score and no evidence spans")
            required_missing = required_missing or applicability == "required"
            continue
        if raw_score is None:
            raise CalibrationError(f"{category_id}: assessed category requires a score")
        value = decimal(raw_score)
        if value < 0 or value > weight:
            raise CalibrationError(f"{category_id}: score {value} is outside 0..{weight}")
        earned += value
        available += weight
        if applicability == "required" and value < minimum:
            required_minimum_failed = True
    normalized = (Decimal("100") * earned / available) if available else None
    failures = score["hard_failures"]
    unknown_failures = sorted(set(failures) - set(rubric["hard_failures"]))
    if unknown_failures:
        raise CalibrationError(f"unknown hard failures: {', '.join(unknown_failures)}")
    capped = min(normalized, decimal(rubric["hard_failure_cap"])) if normalized is not None and failures else normalized
    if required_missing or normalized is None:
        status = "incomplete"
    elif failures or required_minimum_failed or capped < decimal(rubric["passing_score"]):
        status = "fail"
    else:
        status = "pass"
    expected_normalized = display_number(normalized)
    expected_capped = display_number(capped)
    if score["normalized_score"] is None:
        reported_normalized = None
    else:
        reported_normalized = display_number(decimal(score["normalized_score"]))
    if score["capped_score"] is None:
        reported_capped = None
    else:
        reported_capped = display_number(decimal(score["capped_score"]))
    if (reported_normalized, reported_capped, score["overall_status"]) != (expected_normalized, expected_capped, status):
        raise CalibrationError(
            f"reported score does not reconcile; expected normalized={expected_normalized}, capped={expected_capped}, status={status}"
        )
    return {
        **score,
        "normalized_score": expected_normalized,
        "capped_score": expected_capped,
        "overall_status": status,
    }


def reconciliation_reasons(first: dict[str, Any], second: dict[str, Any], rubric: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if first["passage_function_interpretation"] != second["passage_function_interpretation"]:
        reasons.append("passage_function_disagreement")
    if set(first["hard_failures"]) != set(second["hard_failures"]):
        reasons.append("hard_failure_disagreement")
    policies = category_policy(rubric)
    for category_id in CATEGORIES:
        left = first["category_results"][category_id]
        right = second["category_results"][category_id]
        if (left["applicability"], left["assessment_status"]) != (right["applicability"], right["assessment_status"]):
            reasons.append(f"applicability_disagreement:{category_id}")
            continue
        if left["score"] is not None and right["score"] is not None:
            difference = abs(decimal(left["score"]) - decimal(right["score"]))
            threshold = decimal(policies[category_id]["weight"]) * decimal(rubric["adjudication"]["category_fraction"])
            if difference > threshold:
                reasons.append(f"category_difference:{category_id}")
    if first["normalized_score"] is not None and second["normalized_score"] is not None:
        if abs(decimal(first["normalized_score"]) - decimal(second["normalized_score"])) > decimal(rubric["adjudication"]["normalized_total_points"]):
            reasons.append("normalized_total_difference")
    return reasons


def reconcile_scores(
    first: dict[str, Any],
    second: dict[str, Any],
    adjudicator: dict[str, Any] | None = None,
    rubric: dict[str, Any] | None = None,
) -> dict[str, Any]:
    rubric = rubric or load_rubric()
    first = calculate_score(first, rubric)
    second = calculate_score(second, rubric)
    if first["case_id"] != second["case_id"]:
        raise CalibrationError("primary scores refer to different cases")
    reasons = reconciliation_reasons(first, second, rubric)
    if reasons:
        if adjudicator is None:
            raise CalibrationError("adjudication required: " + ", ".join(reasons))
        final = calculate_score(adjudicator, rubric)
        if final["case_id"] != first["case_id"]:
            raise CalibrationError("adjudicator score refers to a different case")
        primary_totals = [value for value in (first["normalized_score"], second["normalized_score"]) if value is not None]
        if primary_totals and final["normalized_score"] is not None and final["normalized_score"] > max(primary_totals):
            justification = final.get("higher_than_both_justification")
            if not justification or len(justification.strip()) < 20:
                raise CalibrationError("adjudicator score above both primary totals requires a specific justification")
        return {**final, "reconciliation": "adjudicator_authoritative", "adjudication_reasons": reasons}

    averaged: dict[str, Any] = {}
    for category_id in CATEGORIES:
        left = first["category_results"][category_id]
        right = second["category_results"][category_id]
        numeric = [decimal(value) for value in (left["score"], right["score"]) if value is not None]
        mean_score = sum(numeric, Decimal("0")) / len(numeric) if numeric else None
        averaged[category_id] = {
            "applicability": left["applicability"],
            "assessment_status": left["assessment_status"],
            "score": display_number(mean_score),
            "reason": f"Primary average. Judge A: {left['reason']} Judge B: {right['reason']}",
            "evidence_spans": list(dict.fromkeys(left["evidence_spans"] + right["evidence_spans"])),
        }
    shell = {
        "schema_version": "3.0.0",
        "case_id": first["case_id"],
        "judge_id": "reconciled",
        "rubric_version": rubric["version"],
        "passage_function_interpretation": first["passage_function_interpretation"],
        "category_results": averaged,
        "hard_failures": first["hard_failures"],
        "normalized_score": 0,
        "capped_score": 0,
        "overall_status": "fail",
        "overall_reason": "Average of two materially agreeing primary judgments.",
        "higher_than_both_justification": None,
    }
    # Calculate expected values without trusting the placeholder totals.
    earned = Decimal("0")
    available = Decimal("0")
    policies = category_policy(rubric)
    missing = False
    minima_failed = False
    for category_id, result in averaged.items():
        if result["score"] is not None:
            earned += decimal(result["score"])
            available += decimal(policies[category_id]["weight"])
            minima_failed = minima_failed or (
                result["applicability"] == "required"
                and decimal(result["score"]) < decimal(policies[category_id]["minimum"])
            )
        elif result["applicability"] == "required":
            missing = True
    normalized = Decimal("100") * earned / available if available else None
    shell["normalized_score"] = display_number(normalized)
    shell["capped_score"] = display_number(normalized)
    if missing or normalized is None:
        shell["overall_status"] = "incomplete"
    elif minima_failed or normalized < decimal(rubric["passing_score"]):
        shell["overall_status"] = "fail"
    else:
        shell["overall_status"] = "pass"
    return {**calculate_score(shell, rubric), "reconciliation": "primary_average", "adjudication_reasons": []}


def source_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def unicode_errors(text: str) -> list[str]:
    errors: list[str] = []
    if "\ufffd" in text:
        errors.append("Unicode replacement character U+FFFD")
    if any(chr(codepoint) in text for codepoint in (0x9225, 0x951F, 0x95C1)):
        errors.append("common mojibake marker")
    return errors


def case_files(root: Path) -> Iterable[tuple[Path, Path]]:
    for generator in sorted(root.rglob("*.generator.json")):
        judge = generator.with_name(generator.name.replace(".generator.json", ".judge.json"))
        if not judge.is_file():
            raise CalibrationError(f"missing judge record for {generator}")
        yield generator, judge


def validate_suite(root: Path) -> dict[str, Any]:
    count = 0
    overlaps: list[dict[str, str]] = []
    seen: set[str] = set()
    for generator_path, judge_path in case_files(root):
        generator = read_json(generator_path)
        judge = read_json(judge_path)
        if generator["case_id"] in seen:
            raise CalibrationError(f"duplicate case ID: {generator['case_id']}")
        seen.add(generator["case_id"])
        for finding in validate_case_pair(generator, judge):
            overlaps.append({"case_id": generator["case_id"], "kind": finding.kind, "field": finding.judge_field, "detail": finding.detail})
        for path in (generator_path, judge_path):
            problems = unicode_errors(path.read_text(encoding="utf-8"))
            if problems:
                raise CalibrationError(f"{path}: {'; '.join(problems)}")
        count += 1
    if not count:
        raise CalibrationError(f"no split calibration cases found under {root}")
    if overlaps:
        first = overlaps[0]
        raise CalibrationError(
            f"answer-like phrase overlap in {first['case_id']} field {first['field']}: {first['kind']} {first['detail']}"
        )
    return {"cases": count, "phrase_overlap_findings": 0, "schema_version": "3.0.0"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate-suite")
    validate.add_argument("path", type=Path)
    leak = sub.add_parser("check-pair")
    leak.add_argument("generator", type=Path)
    leak.add_argument("judge", type=Path)
    score = sub.add_parser("validate-score")
    score.add_argument("path", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "validate-suite":
            result = validate_suite(args.path.resolve())
        elif args.command == "check-pair":
            findings = validate_case_pair(read_json(args.generator), read_json(args.judge))
            if findings:
                raise CalibrationError("answer-like phrase overlap: " + "; ".join(f"{item.judge_field}:{item.kind}" for item in findings))
            result = {"case_id": read_json(args.generator)["case_id"], "leakage": False}
        else:
            result = calculate_score(read_json(args.path))
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except CalibrationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
