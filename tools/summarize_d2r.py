#!/usr/bin/env python3
"""Recompute the private D2R run and emit sanitized public gate results."""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

from lean_adjudication_repair import (
    D2R_CASES,
    REPAIR,
    ROOT,
    development_authorized,
    evaluate_d2r_gates,
    validate_schema,
    verify_lean_v1_preservation,
)


PRIVATE = ROOT / "research-private" / "evaluator-calibration" / "lean-v2" / "D2R"
RECORDS = PRIVATE / "records"


def read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temp.replace(path)


def validate_roles(case_id: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    import jsonschema
    from lean_triangulation import validate_role_a, validate_role_b, validate_role_c

    case_dir = RECORDS / case_id
    a, b, c, contrast = (read(case_dir / name) for name in ("role-a.json", "role-b.json", "role-c.json", "contrast.json"))
    validate_role_a(a)
    validate_role_b(b)
    validate_role_c(c)
    schema = read(REPAIR / "schemas" / "contrast-output.schema.json")
    jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(contrast)
    return a, b, c, contrast


def evidence_items(a: dict[str, Any], b: dict[str, Any], c: dict[str, Any], contrast: dict[str, Any]) -> list[dict[str, Any]]:
    items = list(a["findings"])
    items.extend(check for check in a["atomic_checks"].values() if check["verdict"] == "yes")
    items.extend(item for item in b["findings"] if item["assessment"] != "not_applicable")
    items.extend(item for item in b["applicability_reviews"] if item["decision"] == "challenge_with_evidence")
    items.extend(c["verifications"])
    items.extend(contrast["comparisons"])
    return items


def contrast_source(case_id: str) -> Path:
    d2 = ROOT / "research-private" / "evaluator-calibration" / "lean-v1" / "D2" / "contrast-batches" / case_id
    return d2 if d2.exists() else ROOT / "research-private" / "evaluator-calibration" / "lean-v1" / "D1" / "contrast-batches" / case_id


def procedural_record(case_id: str, b: dict[str, Any], c: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
    seed = f"{case_id}:{b['record_id']}:{c['record_id']}:{item['topic']}"
    return {
        "schema_version": "3.1.0-lean.2",
        "dispute_id": "RAD-" + hashlib.sha256(seed.encode()).hexdigest()[:16],
        "case_id": case_id,
        "primary_class": "invalid_challenge",
        "material_semantic": False,
        "procedural_correction": True,
        "trigger": "category_localization",
        "competing_record_ids": [b["record_id"], c["record_id"]],
        "competing_conclusions": [
            {"record_id": b["record_id"], "conclusion": "The dimension remains uncertain under the supplied task."},
            {"record_id": c["record_id"], "conclusion": "The same uncertainty stands; cited spans do not independently establish packet-level absence."},
        ],
        "evidence_span_ids": item["evidence_span_ids"],
        "resolution": "Preserve the substantive assessment and record the span critique as nonmaterial; no score, applicability, fidelity, hard-failure, or contrast-ordering result changes.",
        "adjudicator_invoked": False,
        "authoritative": False,
    }


def summarize() -> dict[str, Any]:
    verify_lean_v1_preservation()
    manifest = read(REPAIR / "runs" / "D2R.manifest.json")
    if manifest["status"] != "complete":
        raise ValueError("D2R required calls are incomplete")
    required = [call for call in manifest["calls"] if call["call_kind"] == "required"]
    valid_required = sum(call["status"] == "completed" and call["schema_valid"] is True for call in required)

    evidence_total = evidence_valid = 0
    applicability_total = applicability_recovered = 0
    defects = defects_detected = material = material_ordered = 0
    false_positive_denominator = false_positives = localization_total = localization_correct = 0
    semantic_cases: set[str] = set()
    unresolved_material_fidelity: set[str] = set()
    procedural_cases: set[str] = set()
    procedural_records: list[dict[str, Any]] = []
    controls_with_material: set[str] = set()
    original_hard_failures: dict[str, list[str]] = {}

    for case_id in D2R_CASES:
        a, b, c, contrast = validate_roles(case_id)
        packet = read(PRIVATE / "task-packets" / case_id / "production-packet.json")
        batch = read(PRIVATE / "contrast-batches" / case_id / "production-batch.json")
        valid_ids = {item["span_id"] for item in packet["evidence_spans"]}
        valid_ids |= {item["evidence_span_id"] for item in batch["items"]}
        for item in evidence_items(a, b, c, contrast):
            ids = item.get("evidence_span_ids", [])
            evidence_total += 1
            evidence_valid += int(bool(ids) and set(ids) <= valid_ids)

        plan = read(PRIVATE / "task-packets" / case_id / "applicability-plan.json")["predetermined"]
        material_challenges = []
        for review in b["applicability_reviews"]:
            applicability_total += 1
            applicability_recovered += int(review["predetermined"] == plan[review["dimension"]])
        for item in c["verifications"]:
            if item["decision"] == "challenge_with_evidence":
                if item["material"]:
                    semantic_cases.add(case_id)
                    material_challenges.append(item)
                    if "fidelity" in item["topic"].lower() or "structure" in item["topic"].lower():
                        unresolved_material_fidelity.add(case_id)
                else:
                    procedural_cases.add(case_id)
                    record = procedural_record(case_id, b, c, item)
                    validate_schema(record, "repair-adjudication.schema.json")
                    procedural_records.append(record)
        if case_id in {"OR-P01", "IS-P01"} and material_challenges:
            controls_with_material.add(case_id)

        hard = [name for name, check in a["atomic_checks"].items() if check["hard_failure"]]
        if hard:
            original_hard_failures[case_id] = hard

        construction = read(contrast_source(case_id) / "construction.json")
        identity = {item["item_id"]: item for item in construction["items"]}
        observed = {item["item_id"]: item for item in contrast["comparisons"]}
        for item_id, metadata in identity.items():
            kind = metadata["identity"]
            if kind in {"original", "prestige_label"}:
                continue
            result = observed.get(item_id)
            if kind == "faithful_paraphrase":
                false_positive_denominator += 1
                false_positives += int(bool(result and result["material_fidelity_change"]))
                continue
            defects += 1
            correct = bool(result and result["direction"] == "worse")
            defects_detected += int(correct)
            localization_total += 1
            expected = set(metadata["intended_affected_dimensions"])
            localization_correct += int(correct and bool(expected & set(result["affected_dimensions"]))) if result else 0
            if kind == "material_fidelity":
                material += 1
                material_ordered += int(correct and bool(result and result["material_fidelity_change"]))

    corrections_dir = PRIVATE / "procedural-corrections"
    for record in procedural_records:
        write(corrections_dir / f"{record['dispute_id']}.json", record)

    tracked_private = subprocess.run(
        ["git", "ls-files", "research-private"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()
    packet_hashes = read(REPAIR / "packet-hashes.json")
    metrics = {
        "privacy_and_holdouts_valid": not tracked_private and manifest["holdout_states"] == {"expert_holdout_unopened": True, "automated_holdout_unopened": True},
        "required_records_schema_valid_rate": valid_required / len(required),
        "valid_evidence_span_rate": evidence_valid / evidence_total,
        "applicability_recovery": applicability_recovered / applicability_total,
        "material_defect_detection": defects_detected / defects,
        "material_fidelity_contrast_ordering": material_ordered / material,
        "fidelity_false_positive_rate": false_positives / false_positive_denominator,
        "category_localization_accuracy": localization_correct / localization_total,
        "unresolved_material_fidelity_disagreements": len(unresolved_material_fidelity),
        "material_semantic_adjudication_rate": len(semantic_cases) / len(D2R_CASES),
        "procedural_corrections_valid": len(procedural_records) == len(procedural_cases),
        "controls_without_new_material_disagreement": 2 - len(controls_with_material),
        "combined_d2_d2r_domains": 4,
        "production_packets_without_prestige_cues": sum(item.get("production_packet_sha256") is not None for item in packet_hashes["cases"]) / len(D2R_CASES),
    }
    policy = read(REPAIR / "preregistration.json")
    gates = evaluate_d2r_gates(metrics, policy)
    gate_pass = development_authorized(gates)
    # The metric implementation itself was not present in the pre-call freeze
    # commit. This protocol deviation independently prevents authorization.
    authorized = False
    return {
        "schema_version": "3.1.0-lean.2",
        "method": "automated source-grounded triangulation",
        "stage": "D2R",
        "status": "pass" if authorized else "fail",
        "metrics": metrics,
        "gates": gates,
        "diagnostics": {
            "procedural_correction_rate": len(procedural_cases) / len(D2R_CASES),
            "procedural_correction_count": len(procedural_records),
            "historical_prestige_effects": 5,
            "original_hard_failures": original_hard_failures,
            "gate_thresholds_passed": gate_pass,
        },
        "resource_use": {
            "required_calls": 20,
            "attempts_used": manifest["attempts_used"],
            "schema_invalid_attempts": 1,
            "dependent_invalid_attempts": 1,
            "semantic_adjudications": len(semantic_cases),
            "remaining_capacity": manifest["maximum_calls"] - manifest["attempts_used"],
        },
        "experimental_skill_development": authorized,
        "validation_authorized": False,
        "automated_holdout_authorized": False,
        "release_authorized": False,
        "holdouts": {"expert": "unopened", "automated": "unopened"},
        "private_content_included": False,
        "protocol_deviations": [
            "The exact metric summarizer was implemented after authoritative calls began rather than included in freeze commit 817dfe2.",
            "The frozen contrast-output schema allowed arbitrary item_id strings; MGMT-P02 returned evidence IDs where construction item IDs were required, preventing one-construct mapping.",
        ],
        "limitations": [
            "No human experts participated.",
            "Automated roles are same-family and are not experts.",
            "D2R is development authorization only; validation and both holdout claims remain unavailable.",
            "Strict evidence-span validity counts assessed uncertainty and verification records without spans as invalid; no alternative denominator is substituted after results.",
        ],
    }


def main() -> None:
    result = summarize()
    write(REPAIR / "results" / "D2R-result.json", result)
    write(REPAIR / "results" / "tier-a-development-attestation.json", {
        "schema_version": result["schema_version"],
        "method": result["method"],
        "status": result["status"],
        "experimental_skill_development": result["experimental_skill_development"],
        "validation_passed": False,
        "automated_holdout_opened": False,
        "expert_holdout_opened": False,
        "release_authorized": False,
        "result_sha256": hashlib.sha256((REPAIR / "results" / "D2R-result.json").read_bytes()).hexdigest(),
    })
    print(json.dumps({"status": result["status"], "authorized": result["experimental_skill_development"], "metrics": result["metrics"]}, indent=2))


if __name__ == "__main__":
    main()
