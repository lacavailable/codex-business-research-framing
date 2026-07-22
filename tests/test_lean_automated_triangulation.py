from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from conftest import ROOT, import_file


LEAN = ROOT / "evals" / "automated-triangulation" / "lean-v1"
SCHEMAS = LEAN / "schemas"
EXPECTED = {
    "adjudication.schema.json", "contrast-batch.schema.json", "dimension-decision.schema.json",
    "progress.schema.json", "role-a.schema.json", "role-b.schema.json", "role-c.schema.json",
    "run-manifest.schema.json", "tier-a-lean-attestation.schema.json",
}
ATOMIC = {
    "actor_wrong", "decision_timing_changed", "future_information_used", "hidden_information_assumed_observed",
    "state_treated_as_decision", "behavioral_mechanism_changed", "material_constraint_removed", "objective_substituted",
    "profit_or_revenue_called_welfare", "equivalent_formulation_claimed_to_change_true_optimum",
    "runtime_directly_converted_to_profit", "post_deadline_certificate_claimed_to_change_executed_decision",
    "invented_empirical_fact", "unsupported_causal_claim", "hidden_major_assumption",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_lean_schemas_are_additive_closed_and_valid() -> None:
    assert {path.name for path in SCHEMAS.glob("*.json")} == EXPECTED
    for path in SCHEMAS.glob("*.json"):
        schema = load(path)
        Draft202012Validator.check_schema(schema)
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["additionalProperties"] is False
    assert (ROOT / "evals/automated-triangulation/schemas/role-output.schema.json").exists()


def test_pr3_partial_records_are_explicitly_non_authoritative() -> None:
    policy = load(LEAN / "preregistration.json")
    assert policy["authoritative_prior_records"] is False
    audit = (ROOT / "docs/pr3-partial-run-audit.md").read_text(encoding="utf-8")
    assert "incomplete_due_to_execution_capacity" in audit
    assert "not authoritative" in audit
    lean = import_file("lean_preservation", ROOT / "tools/lean_triangulation.py")
    lean.verify_preservation()


def test_call_plans_match_hard_budgets_and_ordering() -> None:
    planner = import_file("lean_planner", ROOT / "tools/plan_triangulation_run.py")
    expected = {"D0": (0, 0), "D1": (16, 4), "D2": (32, 8), "validation": (32, 8)}
    for stage, (required_cap, conditional_cap) in expected.items():
        manifest = planner.build_manifest(stage, "2026-07-22T00:00:00Z")
        planner.validate_manifest(manifest)
        assert manifest["required_call_cap"] == required_cap
        assert manifest["conditional_adjudication_cap"] == conditional_cap
        assert manifest["maximum_calls"] == required_cap + conditional_cap
        assert len(manifest["calls"]) == required_cap + conditional_cap
        roles = [call["role"] for call in manifest["calls"]]
        if stage == "D1":
            assert roles.count("adjudicator") == 4
        if stage in {"D2", "validation"}:
            assert roles.count("adjudicator") == 8


def test_pause_is_not_failure_and_preserves_exact_resume_point() -> None:
    planner = import_file("lean_planner_pause", ROOT / "tools/plan_triangulation_run.py")
    manifest = planner.build_manifest("D1", "2026-07-22T00:00:00Z")
    manifest["calls"][0]["status"] = "completed"
    manifest["calls"][0]["schema_valid"] = True
    manifest["calls"][0]["output_path"] = "private/output.json"
    manifest["calls"][0]["output_sha256"] = "a" * 64
    manifest["calls"][0]["started_at"] = "2026-07-22T00:00:01Z"
    manifest["calls"][0]["completed_at"] = "2026-07-22T00:00:02Z"
    manifest["calls"][0]["attempts"] = 1
    manifest["calls_used"] = 1
    manifest["calls"][1]["status"] = "running"
    paused = planner.pause(manifest)
    assert paused["status"] == "paused_resource_limit"
    assert paused["calls"][0]["status"] == "completed"
    assert paused["calls"][1]["status"] == "paused_resource_limit"
    planner.validate_manifest(paused)


def test_start_counts_attempts_and_conditional_slots_require_activation() -> None:
    planner = import_file("lean_planner_start", ROOT / "tools/plan_triangulation_run.py")
    manifest = planner.build_manifest("D1", "2026-07-22T00:00:00Z")
    required = next(call for call in manifest["calls"] if call["call_kind"] == "required")
    planner.start_call(manifest, required["call_id"])
    assert manifest["calls_used"] == 1
    assert required["attempts"] == 1
    conditional = next(call for call in manifest["calls"] if call["call_kind"] == "conditional")
    with pytest.raises(planner.RunPlanError, match="not activated"):
        planner.start_call(manifest, conditional["call_id"])
    planner.activate_adjudication(manifest, conditional["case_id"])
    planner.start_call(manifest, conditional["call_id"])
    assert manifest["calls_used"] == 2


def test_completed_call_can_be_revalidated_without_spending_an_attempt(tmp_path: Path) -> None:
    planner = import_file("lean_planner_revalidate", ROOT / "tools/plan_triangulation_run.py")
    manifest = planner.build_manifest("D1", "2026-07-22T00:00:00Z")
    call = next(item for item in manifest["calls"] if item["role"] == "role_a")
    planner.start_call(manifest, call["call_id"])
    output = ROOT / "research-private/evaluator-calibration/lean-v1/test-revalidation-role-a.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    record = role_a()
    record["case_id"] = call["case_id"]
    record["prompt_hash"] = call["prompt_hash"]
    record["model"] = {
        "provider": call["provider"],
        "model_id": call["model_id"],
        "family_claim": call["family_claim"],
        "settings": call["settings"],
    }
    output.write_text(json.dumps(record), encoding="utf-8")
    try:
        planner.complete_call(manifest, call["call_id"], output)
        first_completed_at = call["completed_at"]
        first_attempts = call["attempts"]
        record["confidence"] = 0.91
        output.write_text(json.dumps(record), encoding="utf-8")
        planner.complete_call(manifest, call["call_id"], output)
        assert call["attempts"] == first_attempts
        assert manifest["calls_used"] == 1
        assert call["completed_at"] == first_completed_at
    finally:
        output.unlink(missing_ok=True)


def role_a() -> dict:
    check = {"verdict": "no", "material": False, "hard_failure": False, "reason": "No conflict found.", "evidence_span_ids": []}
    return {
        "schema_version": "3.1.0-lean.1", "record_id": "LRA-0123456789abcdef", "case_id": "OM-P01",
        "role": "role_a", "prompt_hash": "a" * 64,
        "model": {"provider": "OpenAI", "model_id": "test", "family_claim": "same_family", "settings": {}},
        "fresh_context": True, "sealed_at": "2026-07-22T00:00:02Z", "confidence": 0.9,
        "structure": {}, "atomic_checks": {name: dict(check) for name in ATOMIC},
        "findings": [{"dimension": "structure_fidelity", "assessment": "supported", "reason": "Aligned.", "evidence_span_ids": ["ES-001"]}],
    }


def role_b() -> dict:
    return {
        "schema_version": "3.1.0-lean.1", "record_id": "LRB-0123456789abcdef", "case_id": "OM-P01",
        "role": "role_b", "prompt_hash": "b" * 64,
        "model": {"provider": "OpenAI", "model_id": "test", "family_claim": "same_family", "settings": {}},
        "fresh_context": True, "sealed_at": "2026-07-22T00:00:03Z", "confidence": 0.85,
        "applicability_reviews": [
            {"dimension": dimension, "predetermined": "required", "decision": "accept", "challenged_value": None, "reason": "Matches task.", "evidence_span_ids": []}
            for dimension in ("managerial_framing", "scholarly_positioning", "evidence_discipline", "prose_usability")
        ],
        "findings": [{"dimension": "managerial_framing", "assessment": "supported", "reason": "Concrete choice.", "evidence_span_ids": ["ES-001"]}],
    }


def role_c() -> dict:
    return {
        "schema_version": "3.1.0-lean.1", "record_id": "LRC-0123456789abcdef", "case_id": "OM-P01", "role": "role_c",
        "role_a_id": "LRA-0123456789abcdef", "role_b_id": "LRB-0123456789abcdef",
        "role_a_sealed_at": "2026-07-22T00:00:02Z", "role_b_sealed_at": "2026-07-22T00:00:03Z",
        "started_at": "2026-07-22T00:00:04Z", "sealed_at": "2026-07-22T00:00:05Z",
        "prompt_hash": "c" * 64, "model": {}, "fresh_context": True, "confidence": 0.8,
        "verifications": [{"topic": "fidelity.actor", "decision": "confirm", "material": False, "reason": "Evidence matches.", "evidence_span_ids": ["ES-001"]}],
    }


def test_role_order_atomic_materiality_and_conditional_adjudication() -> None:
    lean = import_file("lean_records", ROOT / "tools/lean_triangulation.py")
    a, b, c = role_a(), role_b(), role_c()
    lean.validate_role_a(a)
    lean.validate_role_b(b)
    b["applicability_reviews"][0]["evidence_span_ids"] = ["ES-001"]
    lean.validate_role_b(b)
    lean.validate_role_c(c)
    assert lean.adjudication_topics(a, b, c) == []
    c["verifications"][0].update({"decision": "challenge_with_evidence", "material": True})
    assert lean.adjudication_topics(a, b, c) == ["fidelity"]
    c["verifications"][0]["topic"] = "role_b.prose_usability_finding"
    assert lean.adjudication_topics(a, b, c) == ["category_localization"]
    c["started_at"] = "2026-07-22T00:00:01Z"
    with pytest.raises(lean.LeanError, match="before"):
        lean.validate_role_c(c)


def test_dimension_thresholds_are_noncompensatory() -> None:
    lean = import_file("lean_dimensions", ROOT / "tools/lean_triangulation.py")
    assert lean.dimension_status("required", 0.8, False, True) == "high"
    assert lean.dimension_status("required", 0.79, False, True) == "provisional"
    assert lean.dimension_status("required", 0.99, True, True) == "unresolved"
    assert lean.dimension_status("required", 0.99, False, False) == "unresolved"
    assert lean.dimension_status("not_applicable", 0.0, False, True) == "not_applicable"


def test_policy_has_exact_core_gates_and_separate_diagnostics() -> None:
    policy = load(LEAN / "preregistration.json")
    assert len(policy["core_gates"]) == 13
    classifications = {gate["id"]: gate["classification"] for gate in policy["core_gates"]}
    assert classifications["paraphrase-invariance"] == "diagnostic"
    assert classifications["prestige-invariance"] == "diagnostic"
    assert all(value == "blocking" for key, value in classifications.items() if key not in {"paraphrase-invariance", "prestige-invariance"})
    assert policy["D1_acceptance"] == {
        "complete_sentinels": 4,
        "minimum_deterministic_reconciliations": 2,
        "minimum_structure_high": 3,
        "minimum_intended_contrast_recovery": 0.75,
        "require_all_invariants": True,
    }
    assert "combined-applicability" in classifications
    assert "material-defect-detection" in classifications
    assert set(policy["diagnostics"]) == {"reliability", "score_distributions", "confidence", "inter_run_variation", "unresolved_dimensions", "non_core_perturbations"}
    assert policy["stages"]["D1"]["adjudication_allowed"] == "conditional_only"
    assert policy["stages"]["D1"]["maximum_model_calls"] == 20


def test_d0_preserves_private_boundary_and_uses_no_model_calls() -> None:
    lean = import_file("lean_d0", ROOT / "tools/lean_triangulation.py")
    result = lean.d0()
    assert result["status"] == "pass"
    assert result["model_calls"] == 0
    assert result["expert_holdout_unopened"] is True
    assert result["automated_holdout_unopened"] is True


def test_d2_failure_blocks_freeze_validation_and_skill_development() -> None:
    result = load(LEAN / "results/D2-result.json")
    assert result["status"] == "fail"
    assert result["failed_blocking_gates"] == ["conditional-adjudication"]
    assert result["metrics"]["conditional_adjudication_rate"] == 3 / 8
    assert result["metrics"]["prestige_policy_pass"] is False
    assert result["skill_development_authorized"] is False
    assert result["holdouts"] == {"expert": "unopened", "automated": "unopened"}
    manifest = load(LEAN / "runs/D2.manifest.json")
    assert manifest["status"] == "complete"
    assert manifest["calls_used"] == 36
    assert sum(call["status"] == "completed" for call in manifest["calls"] if call["call_kind"] == "required") == 32
    assert sum(call["status"] == "completed" for call in manifest["calls"] if call["role"] == "adjudicator") == 3


def test_failed_tier_a_attestation_is_schema_valid_and_conservative() -> None:
    attestation = load(LEAN / "results/tier-a-lean-attestation.json")
    Draft202012Validator(load(SCHEMAS / "tier-a-lean-attestation.schema.json")).validate(attestation)
    assert attestation["status"] == "fail"
    assert attestation["development_passed"] is False
    assert attestation["validation_passed"] is False
    assert attestation["evaluator_frozen"] is False
    assert attestation["experimental_release_eligible"] is False
    assert attestation["automated_holdout_opened"] is False


def test_d2_role_a_prompt_names_the_frozen_atomic_registry() -> None:
    prompt = load(LEAN / "prompts/roles-d2.json")["role_a"]
    assert all(name in prompt for name in ATOMIC)


def test_public_freeze_verification_is_line_ending_stable(tmp_path: Path) -> None:
    verifier = import_file("freeze_line_endings", ROOT / "tools/verify_calibration_freeze.py")
    fixture = tmp_path / "fixture.txt"
    fixture.write_bytes(b"alpha\r\nbeta\r\n")
    assert verifier.canonical_bytes(fixture) == b"alpha\nbeta\n"
    assert verifier.main() == 0
