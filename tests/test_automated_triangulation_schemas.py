from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

from conftest import ROOT, import_file


AUTO = ROOT / "evals" / "automated-triangulation"
SCHEMAS = AUTO / "schemas"
MANIFESTS = AUTO / "top-journal-private-manifests"

ATOMIC_CHECKS = {
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
}

EXPECTED_SCHEMAS = {
    "aggregate-export.schema.json",
    "applicability-challenge.schema.json",
    "atomic-fidelity-result.schema.json",
    "context-packet.schema.json",
    "contrast-metadata.schema.json",
    "role-output.schema.json",
    "silver-decision.schema.json",
    "split-manifest.schema.json",
    "tier-a-attestation.schema.json",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validator(name: str) -> Draft202012Validator:
    schema = load_json(SCHEMAS / name)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evidence_check(
    verdict: str = "no", *, material: bool = False, hard_failure: bool = False, evidence: list[str] | None = None
) -> dict:
    return {
        "verdict": verdict,
        "material": material,
        "hard_failure": hard_failure,
        "evidence_span_ids": evidence or [],
        "rationale": "The source-grounded context supports this decision.",
    }


def valid_atomic_record() -> dict:
    return {
        "schema_version": "3.0.0-automated.1",
        "case_id": "AC0123456789abcdef",
        "applicability": "required",
        "checks": {name: evidence_check() for name in sorted(ATOMIC_CHECKS)},
        "hard_failures": [],
        "uncertain_rate": 0,
    }


def walk_keys(value: object) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        keys.update(value)
        for item in value.values():
            keys.update(walk_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.update(walk_keys(item))
    return keys


def test_all_automated_schemas_are_draft_2020_12_and_closed() -> None:
    assert {path.name for path in SCHEMAS.glob("*.json")} == EXPECTED_SCHEMAS
    for name in EXPECTED_SCHEMAS:
        schema = load_json(SCHEMAS / name)
        Draft202012Validator.check_schema(schema)
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["additionalProperties"] is False


def test_passage_function_applicability_is_predetermined() -> None:
    module = import_file("automated_triangulation_applicability", ROOT / "tools" / "automated_triangulation.py")
    assert module.derive_applicability("model_setting") == {
        "fidelity": "required",
        "managerial_framing": "optional",
        "scholarly_positioning": "not_applicable",
        "evidence_discipline": "required",
        "prose_clarity": "required",
    }
    with pytest.raises(module.TriangulationError, match="unknown passage function"):
        module.derive_applicability("prestige_label")


def test_atomic_schema_requires_exactly_the_fifteen_preregistered_checks() -> None:
    schema = load_json(SCHEMAS / "atomic-fidelity-result.schema.json")
    checks = schema["properties"]["checks"]
    assert set(checks["required"]) == ATOMIC_CHECKS
    assert set(checks["properties"]) == ATOMIC_CHECKS
    assert set(schema["properties"]["hard_failures"]["items"]["enum"]) == ATOMIC_CHECKS
    validator("atomic-fidelity-result.schema.json").validate(valid_atomic_record())


def test_atomic_schema_rejects_missing_unknown_and_unsupported_hard_failures() -> None:
    check = validator("atomic-fidelity-result.schema.json")
    missing = valid_atomic_record()
    del missing["checks"]["actor_wrong"]
    with pytest.raises(ValidationError):
        check.validate(missing)

    unknown = valid_atomic_record()
    unknown["checks"]["outlet_not_prestigious"] = evidence_check()
    with pytest.raises(ValidationError):
        check.validate(unknown)

    unsupported = valid_atomic_record()
    unsupported["checks"]["actor_wrong"] = evidence_check(
        "yes", material=False, hard_failure=True, evidence=[]
    )
    unsupported["hard_failures"] = ["actor_wrong"]
    with pytest.raises(ValidationError):
        check.validate(unsupported)

    supported = valid_atomic_record()
    supported["checks"]["actor_wrong"] = evidence_check(
        "yes", material=True, hard_failure=True, evidence=["ES-001"]
    )
    supported["hard_failures"] = ["actor_wrong"]
    check.validate(supported)


def test_applicability_challenges_require_evidence_and_closed_enums() -> None:
    check = validator("applicability-challenge.schema.json")
    record = {
        "schema_version": "3.0.0-automated.1",
        "case_id": "AC0123456789abcdef",
        "category": "managerial_framing",
        "proposed_applicability": "required",
        "decision": "challenge_with_evidence",
        "challenged_applicability": "not_applicable",
        "rationale": "The requested task does not attempt managerial implications.",
        "evidence_span_ids": [],
    }
    with pytest.raises(ValidationError):
        check.validate(record)
    record["evidence_span_ids"] = ["ES-001"]
    check.validate(record)
    record["decision"] = "override"
    with pytest.raises(ValidationError):
        check.validate(record)


def test_validation_and_holdout_accept_only_high_confidence_silver_decisions() -> None:
    check = validator("silver-decision.schema.json")
    record = {
        "schema_version": "3.0.0-automated.1",
        "decision_id": "ASD-0123456789abcdef",
        "case_id": "AC0123456789abcdef",
        "source_cluster_id": "SC-0123456789ab",
        "split": "validation",
        "silver_status": "silver_provisional",
        "role_output_ids": ["ARO-0123456789abcdef", "ARO-fedcba9876543210"],
        "conflicts": [],
        "rationale": "Independent roles agree and the context is sufficient.",
        "evidence_span_ids": ["ES-001"],
        "human_expert_review": False,
    }
    with pytest.raises(ValidationError):
        check.validate(record)
    record["silver_status"] = "silver_high_confidence"
    check.validate(record)
    assert not any("gold" in value or "expert" in value for value in schema_string_enums(SCHEMAS / "silver-decision.schema.json"))


def schema_string_enums(path: Path) -> list[str]:
    values: list[str] = []

    def visit(value: object) -> None:
        if isinstance(value, dict):
            enum = value.get("enum")
            if isinstance(enum, list):
                values.extend(item.lower() for item in enum if isinstance(item, str))
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(load_json(path))
    return values


def test_tier_a_attestation_cannot_claim_experts_or_formal_release() -> None:
    check = validator("tier-a-attestation.schema.json")
    record = {
        "schema_version": "3.0.0-automated.1",
        "authorization_tier": "tier_a",
        "overall_status": "incomplete",
        "status": "incomplete",
        "development_passed": False,
        "validation_passed": False,
        "evaluator_frozen": False,
        "automated_holdout_opened": False,
        "production_benchmark_complete": False,
        "experimental_release_eligible": False,
        "expert_holdout_unopened": True,
        "no_human_experts": True,
        "freeze_commit": None,
        "limitations": ["No human experts participated."],
    }
    record.pop("overall_status")
    check.validate(record)
    record["no_human_experts"] = False
    with pytest.raises(ValidationError):
        check.validate(record)
    record["no_human_experts"] = True
    record["experimental_release_eligible"] = True
    with pytest.raises(ValidationError):
        check.validate(record)


def test_private_anchor_manifest_is_balanced_and_public_safe() -> None:
    manifest = load_json(MANIFESTS / "private-anchor-manifest.json")
    records = manifest["records"]
    assert len(records) == 24
    counts = Counter((record["domain"], record["provisional_split"]) for record in records)
    assert counts == Counter({(domain, split): 2 for domain in ("OM", "IS", "OR", "MGMT") for split in ("development", "validation", "holdout")})
    assert len({record["passage_id"] for record in records}) == 24
    forbidden = {"source_text", "passage_text", "evidence_spans", "source_window", "raw_annotation", "expert_identity"}
    assert not (walk_keys(manifest) & forbidden)
    assert all(record["public_text_included"] is False for record in records)


def test_recorded_expert_holdout_hashes_are_immutable() -> None:
    baseline = load_json(MANIFESTS / "expert-holdout-baseline.json")
    assert baseline["baseline_commit"] == "540e72071ea35be228ef4c72c1b3276223631a44"
    assert baseline["expert_holdout_unopened"] is True
    assert len(baseline["files"]) == 114
    for relative, expected in baseline["files"].items():
        path = ROOT / relative
        assert path.is_file(), relative
        assert digest(path) == expected, relative


def test_private_preparation_verify_reports_all_holdout_states() -> None:
    completed = subprocess.run(
        [sys.executable, "tools/prepare_private_triangulation.py", "verify"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    result = json.loads(completed.stdout)
    assert result == {
        "expert_holdout_unopened": True,
        "automated_holdout_unopened": True,
        "automated_holdout_opened": False,
        "private_paths_tracked": False,
        "valid": True,
        "errors": [],
    }
