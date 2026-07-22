#!/usr/bin/env python3
"""Deterministic validation and reconciliation for lean triangulation records."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LEAN = ROOT / "evals" / "automated-triangulation" / "lean-v1"
DIMENSIONS = ("structure_fidelity", "managerial_framing", "scholarly_positioning", "evidence_discipline", "prose_usability")
ATOMIC_CHECKS = {
    "actor_wrong", "decision_timing_changed", "future_information_used", "hidden_information_assumed_observed",
    "state_treated_as_decision", "behavioral_mechanism_changed", "material_constraint_removed", "objective_substituted",
    "profit_or_revenue_called_welfare", "equivalent_formulation_claimed_to_change_true_optimum",
    "runtime_directly_converted_to_profit", "post_deadline_certificate_claimed_to_change_executed_decision",
    "invented_empirical_fact", "unsupported_causal_claim", "hidden_major_assumption",
}


class LeanError(ValueError):
    pass


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_schema(record: Any, name: str) -> None:
    import jsonschema

    schema = read_json(LEAN / "schemas" / name)
    jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(record)


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def validate_role_a(record: dict[str, Any]) -> None:
    validate_schema(record, "role-a.schema.json")
    if set(record["atomic_checks"]) != ATOMIC_CHECKS:
        raise LeanError("Role A must report exactly the 15 registered atomic checks")
    for name, check in record["atomic_checks"].items():
        expected = check["verdict"] == "yes" and check["material"] and bool(check["evidence_span_ids"])
        if check["hard_failure"] != expected:
            raise LeanError(f"{name}: hard failure requires materiality and evidence")
        if check["verdict"] != "yes" and check["material"]:
            raise LeanError(f"{name}: only a yes verdict may be material")


def validate_role_b(record: dict[str, Any]) -> None:
    validate_schema(record, "role-b.schema.json")
    reviews = {item["dimension"]: item for item in record["applicability_reviews"]}
    if set(reviews) != set(DIMENSIONS[1:]):
        raise LeanError("Role B must review each framing/usability dimension exactly once")
    for item in reviews.values():
        challenged = item["decision"] == "challenge_with_evidence"
        if challenged != bool(item["evidence_span_ids"]):
            raise LeanError("applicability challenges require evidence; acceptance must not fabricate challenge evidence")
        if challenged == (item["challenged_value"] is None):
            raise LeanError("challenged_value must appear only for a challenge")
        if challenged and item["challenged_value"] == item["predetermined"]:
            raise LeanError("a challenge must propose a different applicability")


def validate_role_c(record: dict[str, Any]) -> None:
    validate_schema(record, "role-c.schema.json")
    started = parse_time(record["started_at"])
    if started < parse_time(record["role_a_sealed_at"]) or started < parse_time(record["role_b_sealed_at"]):
        raise LeanError("Role C started before Roles A and B were sealed")
    for item in record["verifications"]:
        if item["decision"] == "challenge_with_evidence" and not item["evidence_span_ids"]:
            raise LeanError("Role C challenges require evidence")


def adjudication_topics(role_a: dict[str, Any], role_b: dict[str, Any], role_c: dict[str, Any]) -> list[str]:
    validate_role_a(role_a)
    validate_role_b(role_b)
    validate_role_c(role_c)
    if len({role_a["case_id"], role_b["case_id"], role_c["case_id"]}) != 1:
        raise LeanError("role records do not belong to one case")
    topics: set[str] = set()
    for item in role_c["verifications"]:
        if item["decision"] == "challenge_with_evidence" and item["material"]:
            topic = item["topic"]
            if topic.startswith("applicability"):
                topics.add("applicability")
            elif topic.startswith("fidelity"):
                topics.add("fidelity")
            elif topic.startswith("evidence"):
                topics.add("evidence")
            elif topic.startswith("localization"):
                topics.add("category_localization")
    return sorted(topics)


def dimension_status(applicability: str, confidence: float, material_conflict: bool, evidence_valid: bool) -> str:
    if applicability == "not_applicable":
        return "not_applicable" if not material_conflict else "unresolved"
    if material_conflict or not evidence_valid or confidence < 0.60:
        return "unresolved"
    if confidence >= 0.80:
        return "high"
    return "provisional"


def evaluate_gates(metrics: dict[str, Any], policy: dict[str, Any]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for gate in policy["core_gates"]:
        observed = metrics.get(gate["metric"])
        if observed is None:
            status = "not_assessed"
        elif gate["operator"] == "is":
            status = "pass" if observed is gate["threshold"] else "fail"
        elif gate["operator"] == ">=":
            status = "pass" if observed >= gate["threshold"] else "fail"
        elif gate["operator"] == "<=":
            status = "pass" if observed <= gate["threshold"] else "fail"
        elif gate["operator"] == "=":
            status = "pass" if observed == gate["threshold"] else "fail"
        else:
            raise LeanError(f"unknown gate operator: {gate['operator']}")
        results.append({"id": gate["id"], "status": status, "observed": observed, "threshold": gate["threshold"]})
    return results


def d0() -> dict[str, Any]:
    import jsonschema
    import subprocess
    import sys

    schemas = sorted((LEAN / "schemas").glob("*.json"))
    for path in schemas:
        jsonschema.Draft202012Validator.check_schema(read_json(path))
    prereg = read_json(LEAN / "preregistration.json")
    if len(prereg["core_gates"]) != 13:
        raise LeanError("the lean policy must contain exactly 13 core gates")
    verify = subprocess.run([sys.executable, "tools/prepare_private_triangulation.py", "verify"], cwd=ROOT, text=True, capture_output=True, check=True)
    holdouts = json.loads(verify.stdout)
    if not holdouts["valid"]:
        raise LeanError("private/holdout verification failed")
    verify_preservation()
    return {"schema_version": "3.1.0-lean.1", "stage": "D0", "status": "pass", "model_calls": 0, "schema_count": len(schemas), "core_gate_count": 13, "expert_holdout_unopened": True, "automated_holdout_unopened": True, "private_paths_tracked": False}


def verify_preservation() -> None:
    manifest = read_json(LEAN / "preservation-manifest.json")
    private_root = ROOT / "research-private" / "evaluator-calibration"
    for relative, expected in manifest["tracked_pr3_sha256"].items():
        try:
            current = subprocess.check_output(["git", "show", f"HEAD:{relative}"], cwd=ROOT)
        except subprocess.CalledProcessError as exc:
            raise LeanError(f"cannot read preserved PR #3 artifact: {relative}") from exc
        if hashlib.sha256(current).hexdigest() != expected:
            raise LeanError(f"preserved PR #3 artifact changed: {relative}")
    if not private_root.exists():
        return
    for relative, expected in manifest["private_diagnostic_sha256"].items():
        path = private_root / relative
        if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise LeanError(f"preserved private diagnostic changed: {relative}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("d0", "validate", "gates"))
    parser.add_argument("--schema")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--metrics", type=Path)
    args = parser.parse_args()
    if args.command == "d0":
        print(json.dumps(d0(), indent=2))
    elif args.command == "validate":
        if not args.schema or not args.input:
            parser.error("validate requires --schema and --input")
        validate_schema(read_json(args.input), args.schema)
        print(json.dumps({"valid": True, "schema": args.schema}, indent=2))
    else:
        if not args.metrics:
            parser.error("gates requires --metrics")
        results = evaluate_gates(read_json(args.metrics), read_json(LEAN / "preregistration.json"))
        print(json.dumps({"gates": results, "all_pass": all(item["status"] == "pass" for item in results)}, indent=2))


if __name__ == "__main__":
    main()
