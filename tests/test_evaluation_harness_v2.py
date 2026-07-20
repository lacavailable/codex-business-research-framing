from __future__ import annotations

import pytest

from conftest import ROOT, import_file


MODULE = import_file("evaluate_benchmark_v2", ROOT / "tools/evaluate_benchmark.py")
RUBRIC = MODULE.load_rubric(ROOT)


def score(judge_id: str, values: dict[str, int], failures: list[str] | None = None) -> dict:
    failures = failures or []
    raw = sum(values.values())
    capped = min(raw, RUBRIC["hard_failure_cap"]) if failures else raw
    minima = {item["id"]: item["minimum"] for item in RUBRIC["categories"]}
    passed = capped >= RUBRIC["passing_score"] and not failures and all(
        values[key] >= minimum for key, minimum in minima.items()
    )
    return {
        "schema_version": "1.0.0",
        "blind_id": "B0123456789ab",
        "judge_id": judge_id,
        "rubric_version": RUBRIC["version"],
        "category_scores": values,
        "hard_failures": failures,
        "rationale": {key: "Artifact-specific reason." for key in values},
        "raw_total": raw,
        "capped_total": capped,
        "pass": passed,
    }


def test_layer_minimum_is_noncompensatory() -> None:
    values = {
        "fidelity": 30,
        "managerial_framing": 25,
        "scholarly_positioning": 20,
        "evidence_discipline": 15,
        "prose_clarity": 4,
    }
    normalized = MODULE.normalize_score(score("judge_a", values), RUBRIC, "test")
    assert normalized["raw_total"] == 94
    assert normalized["pass"] is False


def test_hard_failure_disagreement_requires_adjudicator() -> None:
    values = {
        "fidelity": 24,
        "managerial_framing": 20,
        "scholarly_positioning": 16,
        "evidence_discipline": 12,
        "prose_clarity": 8,
    }
    first = score("judge_a", values, ["information_gate_failure"])
    second = score("judge_b", values)
    with pytest.raises(MODULE.EvaluationError):
        MODULE.reconcile_scores([first, second], None, RUBRIC)


def test_adjudicator_resolves_material_disagreement() -> None:
    high = {
        "fidelity": 27,
        "managerial_framing": 22,
        "scholarly_positioning": 17,
        "evidence_discipline": 13,
        "prose_clarity": 8,
    }
    low = dict(high, fidelity=17)
    middle = dict(high, fidelity=23)
    reconciled, required = MODULE.reconcile_scores(
        [score("judge_a", high), score("judge_b", low)],
        score("adjudicator", middle),
        RUBRIC,
    )
    assert required is True
    assert reconciled["category_scores"]["fidelity"] == 23
