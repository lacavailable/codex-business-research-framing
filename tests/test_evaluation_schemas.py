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
    "fidelity": 30,
    "managerial_framing": 25,
    "scholarly_positioning": 20,
    "evidence_discipline": 15,
    "prose_clarity": 10,
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


def test_forty_two_case_schema_and_domain_balance() -> None:
    cases = load_cases()
    assert len(cases) == 42
    assert len({case.get("id") for case in cases}) == 42
    assert Counter(case.get("domain") for case in cases) == {"OM": 14, "IS": 14, "OR": 14}
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
    new_cases = [case for case in cases if int(case["id"].rsplit("-", 1)[1]) >= 11]
    assert len(new_cases) == 12
    assert Counter(case["domain"] for case in new_cases) == {"OM": 4, "IS": 4, "OR": 4}
    assert sum(case["adversarial"] for case in new_cases) == 8


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
    assert rubric["version"] == "2.0.0"
    assert isinstance(rubric.get("hard_failures"), list) and len(rubric["hard_failures"]) >= 6
    threshold = rubric.get("passing_threshold", rubric.get("passing_score"))
    cap = rubric.get("hard_failure_cap")
    assert threshold == 70 and cap == 69
    assert rubric["automatic_failure_on_fidelity_hard_failure"] is True
    assert all(0 <= layer["minimum"] <= layer["weight"] for layer in rubric["categories"])
