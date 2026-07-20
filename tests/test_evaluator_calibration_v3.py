from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

from conftest import ROOT, import_file


CAL = import_file("evaluator_calibration_v3", ROOT / "tools/evaluator_calibration.py")
sys.modules.setdefault("evaluator_calibration", CAL)
GEN = import_file("generate_public_calibration_v3", ROOT / "tools/generate_public_calibration.py")
HARNESS = import_file("calibration_harness_v3", ROOT / "tools/calibration_harness.py")
RUBRIC = CAL.load_rubric()
WEIGHTS = {item["id"]: item["weight"] for item in RUBRIC["categories"]}


def result(applicability: str, score: float | None, reason: str = "Artifact-specific reason.") -> dict:
    status = "not_applicable" if applicability == "not_applicable" else ("not_assessed" if score is None else "assessed")
    return {
        "applicability": applicability,
        "assessment_status": status,
        "score": score,
        "reason": reason,
        "evidence_spans": [] if score is None else ["Relevant synthetic span."],
    }


def score_record(
    judge_id: str,
    values: dict[str, tuple[str, float | None]],
    failures: list[str] | None = None,
    function: str = "business_problem",
    justification: str | None = None,
) -> dict:
    failures = failures or []
    categories = {key: result(*values[key]) for key in CAL.CATEGORIES}
    earned = sum(value[1] for value in values.values() if value[1] is not None)
    available = sum(WEIGHTS[key] for key, value in values.items() if value[1] is not None)
    normalized = 100 * earned / available if available else None
    capped = min(normalized, RUBRIC["hard_failure_cap"]) if normalized is not None and failures else normalized
    minima = {item["id"]: item["minimum"] for item in RUBRIC["categories"]}
    required_missing = any(app == "required" and value is None for app, value in values.values())
    minimum_failed = any(app == "required" and value is not None and value < minima[key] for key, (app, value) in values.items())
    if required_missing or normalized is None:
        status = "incomplete"
    elif failures or minimum_failed or capped < RUBRIC["passing_score"]:
        status = "fail"
    else:
        status = "pass"
    return {
        "schema_version": "3.0.0",
        "case_id": "C0123456789abcdef",
        "judge_id": judge_id,
        "rubric_version": RUBRIC["version"],
        "passage_function_interpretation": function,
        "category_results": categories,
        "hard_failures": failures,
        "normalized_score": normalized,
        "capped_score": capped,
        "overall_status": status,
        "overall_reason": "Complete synthetic judgment.",
        "higher_than_both_justification": justification,
    }


def standard_values() -> dict[str, tuple[str, float | None]]:
    return {
        "fidelity": ("required", 24),
        "managerial_framing": ("required", 20),
        "scholarly_positioning": ("not_applicable", None),
        "evidence_discipline": ("required", 12),
        "prose_clarity": ("required", 8),
    }


def test_nonapplicable_category_is_removed_from_denominator() -> None:
    normalized = CAL.calculate_score(score_record("judge_a", standard_values()))
    assert normalized["normalized_score"] == 80.0
    assert normalized["overall_status"] == "pass"


def test_required_not_assessed_is_incomplete() -> None:
    values = standard_values()
    values["fidelity"] = ("required", None)
    normalized = CAL.calculate_score(score_record("judge_a", values))
    assert normalized["overall_status"] == "incomplete"


def test_optional_assessed_enters_denominator_without_minimum() -> None:
    values = standard_values()
    values["scholarly_positioning"] = ("optional", 2)
    normalized = CAL.calculate_score(score_record("judge_a", values))
    assert normalized["normalized_score"] == 66.0
    assert normalized["overall_status"] == "fail"


def test_primary_scores_average_without_rounding() -> None:
    first_values = standard_values()
    second_values = standard_values()
    first_values["fidelity"] = ("required", 24.25)
    second_values["fidelity"] = ("required", 24.75)
    reconciled = CAL.reconcile_scores(score_record("judge_a", first_values), score_record("judge_b", second_values))
    assert reconciled["reconciliation"] == "primary_average"
    assert reconciled["category_results"]["fidelity"]["score"] == 24.5


def test_applicability_disagreement_requires_authoritative_adjudication() -> None:
    first = score_record("judge_a", standard_values())
    values = standard_values()
    values["scholarly_positioning"] = ("optional", 10)
    second = score_record("judge_b", values)
    with pytest.raises(CAL.CalibrationError, match="adjudication required"):
        CAL.reconcile_scores(first, second)
    final = score_record("adjudicator", standard_values())
    reconciled = CAL.reconcile_scores(first, second, final)
    assert reconciled["judge_id"] == "adjudicator"
    assert reconciled["reconciliation"] == "adjudicator_authoritative"


def test_adjudicator_above_both_requires_explanation() -> None:
    low = standard_values()
    high = standard_values()
    low["fidelity"] = ("required", 15)
    high["fidelity"] = ("required", 23)
    first = score_record("judge_a", low)
    second = score_record("judge_b", high)
    final_values = standard_values()
    final_values["fidelity"] = ("required", 28)
    with pytest.raises(CAL.CalibrationError, match="requires a specific justification"):
        CAL.reconcile_scores(first, second, score_record("adjudicator", final_values))
    final = score_record(
        "adjudicator",
        final_values,
        justification="Both primary judges overlooked the explicit timing and information sentence.",
    )
    assert CAL.reconcile_scores(first, second, final)["normalized_score"] > second["normalized_score"]


def test_hard_failure_is_noncompensatory() -> None:
    values = {key: ("required", WEIGHTS[key]) for key in CAL.CATEGORIES}
    normalized = CAL.calculate_score(score_record("judge_a", values, ["information_gate_failure"]))
    assert normalized["normalized_score"] == 100.0
    assert normalized["capped_score"] == 69.0
    assert normalized["overall_status"] == "fail"


def test_agreeing_primary_hard_failure_remains_capped() -> None:
    values = {key: ("required", WEIGHTS[key]) for key in CAL.CATEGORIES}
    first = score_record("judge_a", values, ["actor_gate_failure"])
    second = score_record("judge_b", values, ["actor_gate_failure"])
    reconciled = CAL.reconcile_scores(first, second)
    assert reconciled["normalized_score"] == 100.0
    assert reconciled["capped_score"] == 69.0
    assert reconciled["overall_status"] == "fail"


def test_forbidden_key_and_phrase_leakage_are_detected() -> None:
    generator_path = next((ROOT / "evals/calibration/synthetic-analogues").glob("*.generator.json"))
    judge_path = generator_path.with_name(generator_path.name.replace(".generator.json", ".judge.json"))
    generator = json.loads(generator_path.read_text(encoding="utf-8"))
    judge = json.loads(judge_path.read_text(encoding="utf-8"))
    leaked = copy.deepcopy(generator)
    leaked["context"]["prohibited_model_changes"] = ["future facts"]
    with pytest.raises(CAL.CalibrationError):
        CAL.validate_case_pair(leaked, judge)
    phrase = "this answer key phrase must never appear in generator material"
    generator["anonymized_passage"] += " " + phrase
    judge["expected_weaknesses"] = [phrase]
    assert CAL.phrase_overlap(generator, judge)


def test_generated_suite_counts_and_clustered_splits() -> None:
    files, manifest = GEN.build_records()
    assert len(manifest["records"]) == 168
    groups = {name: sum(record["group"] == name for record in manifest["records"]) for name in ("positive", "intermediate", "negative", "contrast")}
    assert groups == {"positive": 12, "intermediate": 12, "negative": 24, "contrast": 120}
    by_case = {record["case_id"]: record for record in manifest["records"]}
    for record in manifest["records"]:
        if record["group"] == "contrast":
            assert record["split"] == by_case[record["original_case_id"]]["split"]
    constructs = {name: sum(record.get("changed_construct") == name for record in manifest["records"]) for name in GEN.CONSTRUCTS}
    assert all(value == 12 for value in constructs.values())
    assert all(path.suffix == ".json" for path, _ in files)
    for _, record in files:
        contrast = record.get("contrast") if isinstance(record, dict) else None
        if contrast:
            applicable = record["applicable_categories"]
            assert all(applicable[category] != "not_applicable" for category in contrast["expected_declines"])


def test_generated_files_are_current_and_leak_free() -> None:
    assert GEN.main.__module__
    assert CAL.validate_suite(ROOT / "evals/calibration")["cases"] == 168


def test_default_packets_leave_holdout_locked(tmp_path: Path) -> None:
    result = HARNESS.prepare(tmp_path, 21, {"development", "validation"})
    manifest = json.loads((tmp_path / "packet-manifest.json").read_text(encoding="utf-8"))
    selected = {case for packet in manifest["judges"]["judge_a"] for case in packet["case_ids"]}
    gold = {
        record["case_id"]: record
        for record in json.loads((ROOT / "evals/calibration/public-metadata/synthetic-suite-manifest.json").read_text(encoding="utf-8"))["records"]
    }
    assert result["cases"] == 112
    assert {gold[case]["split"] for case in selected} == {"development", "validation"}
