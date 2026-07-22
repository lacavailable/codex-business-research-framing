from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from conftest import ROOT, import_file


LEAN_V1 = ROOT / "evals" / "automated-triangulation" / "lean-v1"
LEAN_V2 = ROOT / "evals" / "automated-triangulation" / "lean-v2"
ATOMIC_CHECKS = (
    "actor_wrong",
    "decision_timing_changed",
    "future_information_used",
    "hidden_information_assumed_observed",
    "state_treated_as_decision",
    "behavioral_mechanism_changed",
    "material_constraint_removed",
    "objective_substituted",
    "profit_or_revenue_called_welfare",
    "equivalent_formulation_claimed_to_change_true_optimum",
    "runtime_directly_converted_to_profit",
    "post_deadline_certificate_claimed_to_change_executed_decision",
    "invented_empirical_fact",
    "unsupported_causal_claim",
    "hidden_major_assumption",
)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def repair_module(name: str = "lean_adjudication_repair"):
    return import_file(name, ROOT / "tools" / "lean_adjudication_repair.py")


def synthetic_packet() -> dict:
    return {
        "packet_id": "OPAQUE-0001",
        "case_id": "OM-P02",
        "source_id": "OM-001",
        "source_cluster_id": "SC-000000000001",
        "journal_name": "Prestigious Journal",
        "metadata": {
            "author": "Named Author",
            "institution": "Famous University",
            "doi": "10.0000/example",
            "citation_count": 999,
            "publication_status": "published",
            "source_quality_label": "top-journal",
            "article_title": "Recognizable Article Title",
        },
        "passage_function": "model_setting",
        "requested_task": "Frame the decision problem.",
        "attempted_layers": ["managerial_framing"],
        "output_profile": "standard",
        "context": {
            "actor": "retailer",
            "decisions": ["choose assortment"],
            "timing": "before demand",
            "decision_time_information": ["historical demand"],
            "objective": "expected profit",
            "constraints": ["capacity"],
            "mechanism": "stockout substitution",
        },
        "passage_sha256": "a" * 64,
        "evidence_spans": [
            {"span_id": "ES-001", "supports": ["actor", "objective"], "text": "Retailer chooses before demand."},
            {"span_id": "ES-002", "supports": ["objective"], "text": "The objective is expected profit."},
            {"span_id": "ES-003", "supports": ["mechanism"], "text": "Substitution follows stockouts."},
        ],
    }


def test_lean_v1_is_sealed_by_complete_byte_preservation_manifest() -> None:
    manifest = load(LEAN_V2 / "preservation-manifest.json")
    repair = repair_module("repair_preservation")
    repair.verify_lean_v1_preservation()
    source_manifest = ROOT / manifest["source_preservation_manifest"]
    assert manifest["source_preservation_manifest_sha256"] == repair.file_sha256(source_manifest)
    assert manifest["historical_artifacts_byte_preserved"] is True

    historical = load(LEAN_V1 / "results" / "D2-result.json")
    assert historical["status"] == "fail"
    assert historical["metrics"]["conditional_adjudication_rate"] == 3 / 8
    assert historical["failed_blocking_gates"] == ["conditional-adjudication"]
    assert historical["skill_development_authorized"] is False


@pytest.mark.parametrize(
    ("facts", "expected"),
    [
        ({"supported_status_changed": True}, "material_semantic_disagreement"),
        ({"applicability_changed": True, "denominator_changed": True}, "applicability_boundary_disagreement"),
        ({"compatible_span_mismatch": True}, "evidence_localization_mismatch"),
        ({"schema_invalid": True}, "schema_or_format_mismatch"),
        ({"wording_only": True}, "terminology_only_difference"),
        ({"context_sufficient": False}, "insufficient_context"),
        ({"challenge_has_valid_evidence": False}, "invalid_challenge"),
    ],
)
def test_disagreement_taxonomy_has_one_primary_class(facts: dict, expected: str) -> None:
    repair = repair_module(f"repair_classification_{expected}")
    translated = {
        "supported_status_changed": "support_status_changed",
        "denominator_changed": "denominator_or_required_output_changed",
        "compatible_span_mismatch": "evidence_only",
        "schema_invalid": "schema_only",
        "wording_only": "terminology_only",
        "context_sufficient": "insufficient_context",
    }
    kwargs = {}
    for key, value in facts.items():
        if key == "challenge_has_valid_evidence":
            kwargs[key] = value
        elif key == "context_sufficient":
            kwargs[translated[key]] = not value
        else:
            kwargs[translated.get(key, key)] = value
    assert repair.classify_disagreement(**kwargs) == expected


def test_material_semantic_and_denominator_disputes_require_llm_adjudication() -> None:
    repair = repair_module("repair_semantic_trigger")
    semantic = repair.classify_disagreement(support_status_changed=True)
    applicability = repair.classify_disagreement(
        applicability_changed=True, denominator_or_required_output_changed=True
    )
    localization = repair.classify_disagreement(evidence_only=True)
    assert repair.needs_semantic_adjudication(semantic) is True
    assert repair.needs_semantic_adjudication(applicability) is True
    assert repair.needs_semantic_adjudication(localization) is False


def test_evidence_localization_repair_is_deterministic_and_nonsemantic() -> None:
    repair = repair_module("repair_evidence")
    packet = synthetic_packet()
    role_findings = [
        {"role": "role_a", "assessment": "supported", "material": False, "hard_failure": False, "evidence_span_ids": ["ES-001"]},
        {"role": "role_b", "assessment": "supported", "material": False, "hard_failure": False, "evidence_span_ids": ["ES-002"]},
        {"role": "role_c", "assessment": "supported", "material": False, "hard_failure": False, "evidence_span_ids": ["ES-002"]},
    ]
    result = repair.resolve_evidence_localization(case_id="OM-P02", finding_key="objective", role_findings=role_findings, packet=packet)
    assert result["accepted_evidence_reference"] == "ES-001"
    assert result["original_evidence_references"] == [["ES-001"], ["ES-002"], ["ES-002"]]
    assert result["reason_no_semantic_adjudication"]
    assert result["finding_key"] == "objective"
    assert result["substantive_finding_unchanged"] is True
    assert len(result["record_hash"]) == 64
    assert result["deterministic_rule"]


def test_evidence_repair_rejects_semantic_conflict_foreign_or_invented_spans() -> None:
    repair = repair_module("repair_evidence_rejections")
    packet = synthetic_packet()
    with pytest.raises(repair.RepairError):
        repair.resolve_evidence_localization(case_id="OM-P02", finding_key="objective", packet=packet, role_findings=[
                {"role": "role_a", "assessment": "supported", "material": False, "hard_failure": False, "evidence_span_ids": ["ES-001"]},
                {"role": "role_b", "assessment": "unsupported", "material": False, "hard_failure": False, "evidence_span_ids": ["ES-002"]},
            ]
        )
    with pytest.raises(repair.RepairError):
        repair.resolve_evidence_localization(case_id="OM-P02", finding_key="objective", packet=packet, role_findings=[
                {"role": "role_a", "assessment": "supported", "material": False, "hard_failure": False, "evidence_span_ids": ["ES-999"]},
                {"role": "role_b", "assessment": "supported", "material": False, "hard_failure": False, "evidence_span_ids": ["ES-002"]},
            ]
        )


def test_applicability_is_predetermined_with_documented_precedence() -> None:
    repair = repair_module("repair_applicability")
    # Explicit task requirements outrank every lower-precedence signal.
    result = repair.derive_applicability({"passage_function": "model_setting", "requested_task": "map model", "required_layers": ["scholarly_positioning"], "attempted_layers": [], "context": {}, "response_profile": "compact"})
    assert result["scholarly_positioning"] == "required"
    # Attempting a layer makes it assessable even when the passage function would not.
    result = repair.derive_applicability({"passage_function": "contribution", "requested_task": "position contribution", "attempted_layers": ["managerial_framing"], "context": {}, "response_profile": "compact"})
    assert result["managerial_framing"] == "required"
    result = repair.derive_applicability({"passage_function": "model_setting", "requested_task": "map model", "attempted_layers": [], "context": {}, "response_profile": "standard"})
    assert result["scholarly_positioning"] == "not_applicable"
    result = repair.derive_applicability({"passage_function": "managerial_implications", "requested_task": "draft implications", "attempted_layers": [], "context": {"actor": "manager"}, "response_profile": "standard"})
    assert result["managerial_framing"] == "required"


def test_production_blinding_removes_nested_prestige_cues_and_values() -> None:
    repair = repair_module("repair_blinding")
    forbidden_values = ("Prestigious Journal", "Famous University", "Recognizable Article Title", "top-journal")
    blinded = repair.blind_production_packet(synthetic_packet(), forbidden_values)
    serialized = json.dumps(blinded, ensure_ascii=False).lower()
    for forbidden in (
        "journal_name", "publication_status", "author", "institution", "doi",
        "citation_count", "article_title", "source_quality_label", "top-journal",
        "prestigious journal", "famous university", "recognizable article title",
    ):
        assert forbidden not in serialized
    assert blinded["case_id"].startswith("CASE-")
    assert blinded["context"]["actor"] == "retailer"
    assert blinded["evidence_spans"] == synthetic_packet()["evidence_spans"]


def test_packet_repair_is_audited_and_cannot_invent_semantic_context() -> None:
    repair = repair_module("repair_packet")
    packet = synthetic_packet()
    packet["passageFunction"] = packet.pop("passage_function")
    packet["evidence_spans"][0]["supports"] = ["actor", "objective"]
    repaired, audit = repair.validate_and_repair_packet(packet)
    assert repaired["passage_function"] == "model_setting"
    assert repaired["evidence_spans"][0]["supports"] == ["context.actor", "context.objective"]
    assert audit["original_sha256"] != audit["repaired_sha256"]
    assert audit["substantive_content_changed"] is False
    assert audit["transformations"]
    assert {item["kind"] for item in audit["transformations"]} == {"field_name_normalization", "supports_path_normalization"}
    assert audit["validation_after"]

    missing_actor = synthetic_packet()
    missing_actor["context"]["actor"] = None
    unresolved, unresolved_audit = repair.validate_and_repair_packet(missing_actor)
    assert unresolved["context"]["actor"] is None
    assert any("actor" in item for item in unresolved_audit["validation_before"])


def test_role_a_contract_contains_every_atomic_key_exactly_once() -> None:
    repair = repair_module("repair_role_a_prompt")
    prompt = load(LEAN_V2 / "prompts" / "roles-d2r.json")["role_a"]
    repair.validate_role_a_prompt(prompt)
    for key in ATOMIC_CHECKS:
        assert prompt["atomic_checks"].count(key) == 1


def test_d2r_manifest_freezes_cases_models_budgets_and_holdouts() -> None:
    planner = import_file("d2r_planner", ROOT / "tools" / "plan_d2r_run.py")
    manifest = planner.build_manifest("2026-07-22T00:00:00Z")
    planner.validate_manifest(manifest)
    assert manifest["stage"] == "D2R"
    assert manifest["split"] == "development"
    assert manifest["case_set"] == ["OM-P02", "MGMT-P02", "IS-P02", "OR-P01", "IS-P01"]
    assert manifest["control_cases"] == ["OR-P01", "IS-P01"]
    assert manifest["required_call_cap"] == 20
    assert manifest["conditional_adjudication_cap"] == 5
    assert manifest["maximum_calls"] == 25
    assert manifest["calls_used"] == 0
    assert manifest["holdout_states"] == {
        "expert_holdout_unopened": True,
        "automated_holdout_unopened": True,
    }
    required = [item for item in manifest["calls"] if item["call_kind"] == "required"]
    conditional = [item for item in manifest["calls"] if item["call_kind"] == "conditional"]
    assert len(required) == 20
    assert len(conditional) == 5
    assert {item["role"] for item in required} == {"role_a", "role_b", "role_c", "contrast_judge"}
    models = {item["role"]: (item["model_id"], item["settings"]["reasoning_effort"]) for item in manifest["calls"]}
    assert models == {
        "role_a": ("gpt-5.6-sol", "high"),
        "role_b": ("gpt-5.6-terra", "high"),
        "role_c": ("gpt-5.6-sol", "high"),
        "contrast_judge": ("gpt-5.6-terra", "high"),
        "adjudicator": ("gpt-5.6-sol", "xhigh"),
    }
    assert all(item["family_claim"] == "same_family" for item in manifest["calls"])
    assert all(item["settings"]["sampling_controls"] == "unavailable" for item in manifest["calls"])


def passing_d2r_metrics() -> dict:
    return {
        "privacy_and_holdouts_valid": True,
        "required_records_schema_valid_rate": 1.0,
        "production_packets_without_prestige_cues": 1.0,
        "valid_evidence_span_rate": 0.95,
        "applicability_recovery": 0.95,
        "material_defect_detection": 0.90,
        "material_fidelity_contrast_ordering": 0.90,
        "fidelity_false_positive_rate": 0.05,
        "category_localization_accuracy": 0.80,
        "unresolved_material_fidelity_disagreements": 0,
        "material_semantic_adjudications": 1,
        "case_count": 5,
        "procedural_corrections_valid": True,
        "controls_without_new_material_disagreement": 2,
        "combined_d2_d2r_domains": 4,
    }


def test_d2r_has_fourteen_noncompensatory_gates_and_narrow_authorization() -> None:
    repair = repair_module("repair_d2r_gates")
    metrics = passing_d2r_metrics()
    metrics["material_semantic_adjudication_rate"] = metrics["material_semantic_adjudications"] / metrics["case_count"]
    policy = load(LEAN_V2 / "preregistration.json")
    gates = repair.evaluate_d2r_gates(metrics, policy)
    assert len(gates) == 14
    assert all(gate["status"] == "pass" for gate in gates)
    assert repair.development_authorized(gates) is True

    failing = passing_d2r_metrics()
    failing["material_semantic_adjudications"] = 2
    failing["material_semantic_adjudication_rate"] = 2 / 5
    failed = repair.evaluate_d2r_gates(failing, policy)
    assert any(gate["id"] == "material-semantic-adjudication" and gate["status"] == "fail" for gate in failed)
    assert repair.development_authorized(failed) is False


def test_public_repair_area_contains_no_private_paths_or_passage_text() -> None:
    tracked = set(
        line for line in __import__("subprocess").check_output(
            ["git", "ls-files"], cwd=ROOT, text=True, encoding="utf-8"
        ).splitlines() if line
    )
    assert not any(path.startswith("research-private/") for path in tracked)
    for path in LEAN_V2.rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            assert "research-private/evaluator-calibration" not in text
            assert "private passage text" not in text.lower()


def test_d2r_failure_blocks_skill_and_preserves_holdouts() -> None:
    result = load(LEAN_V2 / "results" / "D2R-result.json")
    assert result["status"] == "fail"
    assert result["experimental_skill_development"] is False
    assert result["validation_authorized"] is False
    assert result["automated_holdout_authorized"] is False
    assert result["release_authorized"] is False
    assert result["holdouts"] == {"expert": "unopened", "automated": "unopened"}
    failed = {gate["id"] for gate in result["gates"] if gate["status"] == "fail"}
    assert failed == {"evidence-spans", "material-defect-detection", "material-fidelity-ordering"}
    assert result["resource_use"]["attempts_used"] == 22
    assert result["resource_use"]["semantic_adjudications"] == 0
    assert len(result["protocol_deviations"]) == 2


def test_repair_branch_has_no_skill_changes() -> None:
    repair = repair_module("repair_skill_tree")
    manifest = load(LEAN_V2 / "preservation-manifest.json")
    assert repair.skill_tree_sha256() == manifest["baseline_skill_tree_sha256"]
