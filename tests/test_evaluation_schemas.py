from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from conftest import ROOT


CASE_FIELDS = {
    "id", "domain", "prompt", "model_specification", "decision_time_facts",
    "fidelity_requirements", "prohibited_inferences", "evidence_needs",
    "hard_failure_traps", "adversarial", "tags",
}
EXPECTED_WEIGHTS = {
    "model_fidelity": 25,
    "decision_specificity": 15,
    "nontrivial_tradeoff": 15,
    "mechanism": 10,
    "evidence_discipline": 10,
    "boundaries": 10,
    "model_mapping": 10,
    "managerial_clarity": 5,
}


def load_cases() -> list[dict]:
    cases: list[dict] = []
    for path in sorted((ROOT / "evals" / "cases").glob("*.json")):
        value = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(value, list):
            cases.extend(value)
        elif isinstance(value, dict) and isinstance(value.get("cases"), list):
            cases.extend(value["cases"])
        else:
            cases.append(value)
    return cases


def test_thirty_case_schema_and_domain_balance() -> None:
    cases = load_cases()
    assert len(cases) == 30
    assert len({case.get("id") for case in cases}) == 30
    assert Counter(case.get("domain") for case in cases) == {"OM": 10, "IS": 10, "OR": 10}
    for case in cases:
        assert CASE_FIELDS <= set(case), f"{case.get('id')} is missing required fields"
        assert isinstance(case["adversarial"], bool)
        for field in (
            "decision_time_facts", "fidelity_requirements", "prohibited_inferences",
            "evidence_needs", "hard_failure_traps", "tags",
        ):
            assert isinstance(case[field], list) and case[field], f"{case['id']}.{field} must be nonempty"
        assert isinstance(case["prompt"], str) and case["prompt"].strip()
        assert isinstance(case["model_specification"], (str, dict)) and case["model_specification"]
    assert any(case["adversarial"] for case in cases)


def normalize_categories(value) -> dict[str, int]:
    if isinstance(value, dict):
        return {
            name: int(details["weight"] if isinstance(details, dict) else details)
            for name, details in value.items()
        }
    return {item["id"]: int(item["weight"]) for item in value}


def test_rubric_schema_weights_and_hard_failures() -> None:
    files = sorted((ROOT / "evals" / "rubrics").glob("*.json"))
    assert files, "a machine-readable JSON rubric is required"
    rubrics = [json.loads(path.read_text(encoding="utf-8")) for path in files]
    matching = [rubric for rubric in rubrics if "categories" in rubric]
    assert len(matching) == 1, "exactly one scoring rubric with categories is required"
    rubric = matching[0]
    assert normalize_categories(rubric["categories"]) == EXPECTED_WEIGHTS
    assert sum(EXPECTED_WEIGHTS.values()) == 100
    assert isinstance(rubric.get("hard_failures"), list) and len(rubric["hard_failures"]) >= 9
    threshold = rubric.get("passing_threshold", rubric.get("passing_score"))
    cap = rubric.get("hard_failure_cap")
    assert isinstance(threshold, int) and isinstance(cap, int) and cap < threshold
