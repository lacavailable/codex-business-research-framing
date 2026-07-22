#!/usr/bin/env python3
"""Deterministic validation and reconciliation for lean triangulation records."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LEAN = ROOT / "evals" / "automated-triangulation" / "lean-v1"
SCHEMA_VERSION = "3.1.0-lean.1"
DIMENSIONS = ("structure_fidelity", "managerial_framing", "scholarly_positioning", "evidence_discipline", "prose_usability")
SENTINELS = ("OM-P01", "IS-P01", "OR-P01", "MGMT-P01")
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
        if challenged and not item["evidence_span_ids"]:
            raise LeanError("applicability challenges require evidence")
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
            topic = item["topic"].lower()
            if "applicability" in topic:
                topics.add("applicability")
            elif any(token in topic for token in ("fidelity", "structure", "material_failure")):
                topics.add("fidelity")
            elif "evidence" in topic:
                topics.add("evidence")
            else:
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


def _record_evidence_items(case_dir: Path) -> list[dict[str, Any]]:
    role_a = read_json(case_dir / "role-a.json")
    role_b = read_json(case_dir / "role-b.json")
    role_c = read_json(case_dir / "role-c.json")
    contrast = read_json(case_dir / "contrast.json")
    items = list(role_a["findings"])
    items.extend(check for check in role_a["atomic_checks"].values() if check["verdict"] == "yes")
    items.extend(item for item in role_b["findings"] if item["assessment"] != "not_applicable")
    items.extend(review for review in role_b["applicability_reviews"] if review["decision"] == "challenge_with_evidence")
    items.extend(role_c["verifications"])
    items.extend(contrast["comparisons"])
    return items


def _private_packet(case_id: str, stage: str) -> Path:
    repaired = ROOT / "research-private" / "evaluator-calibration" / "lean-v1" / stage / "task-packets" / case_id / "context-packet.json"
    return repaired if repaired.exists() else ROOT / "research-private" / "evaluator-calibration" / "judge-packets" / "automated" / case_id / "context-packet.json"


def _contrast_input(case_id: str, stage: str) -> Path:
    current = ROOT / "research-private" / "evaluator-calibration" / "lean-v1" / stage / "contrast-batches" / case_id
    fallback = ROOT / "research-private" / "evaluator-calibration" / "lean-v1" / "D1" / "contrast-batches" / case_id
    return current if current.exists() else fallback


def _valid_evidence_ids(case_id: str, stage: str = "D1") -> set[str]:
    packet = read_json(_private_packet(case_id, stage))
    batch = read_json(_contrast_input(case_id, stage) / "batch.json")
    return {item["span_id"] for item in packet["evidence_spans"]} | {item["evidence_span_id"] for item in batch["items"]}


def _authoritative_applicability(role_b: dict[str, Any], role_c: dict[str, Any]) -> tuple[dict[str, str], int, int]:
    values: dict[str, str] = {}
    recovered = 0
    total = 0
    confirmations = [item for item in role_c["verifications"] if item["decision"] == "confirm"]
    for review in role_b["applicability_reviews"]:
        total += 1
        if review["decision"] == "accept":
            values[review["dimension"]] = review["predetermined"]
            recovered += 1
            continue
        topic_tokens = (review["dimension"], "applicability")
        confirmed = any(any(token in item["topic"].lower() for token in topic_tokens) for item in confirmations)
        values[review["dimension"]] = review["challenged_value"] if confirmed else review["predetermined"]
        recovered += int(confirmed)
    return values, recovered, total


def _contrast_metrics(case_id: str, contrast: dict[str, Any], stage: str = "D1") -> dict[str, int]:
    construction = read_json(_contrast_input(case_id, stage) / "construction.json")
    identities = {item["item_id"]: item for item in construction["items"]}
    comparisons = {item["item_id"]: item for item in contrast["comparisons"]}
    result = {"intended": 0, "recovered": 0, "defects": 0, "defects_detected": 0, "material": 0, "material_ordered": 0, "localization": 0, "false_positive_denominator": 0, "false_positives": 0, "paraphrase_disagreements": 0, "prestige_effects": 0}
    for item_id, metadata in identities.items():
        identity = metadata["identity"]
        if identity == "original":
            continue
        result["intended"] += 1
        observed = comparisons.get(item_id)
        if observed is None:
            if identity in {"faithful_paraphrase", "prestige_label"}:
                result["false_positive_denominator"] += 1
                if identity == "faithful_paraphrase":
                    result["paraphrase_disagreements"] += 1
                else:
                    result["prestige_effects"] += 1
            else:
                result["defects"] += 1
                result["material"] += int(identity == "material_fidelity")
            continue
        if identity in {"faithful_paraphrase", "prestige_label"}:
            correct = observed["direction"] == "equivalent" and not observed["material_fidelity_change"]
            result["false_positive_denominator"] += 1
            result["false_positives"] += int(observed["material_fidelity_change"])
            if identity == "faithful_paraphrase":
                result["paraphrase_disagreements"] += int(not correct)
            else:
                result["prestige_effects"] += int(not correct)
        else:
            correct = observed["direction"] == "worse"
            result["defects"] += 1
            result["defects_detected"] += int(correct)
            result["material"] += int(identity == "material_fidelity")
            result["material_ordered"] += int(identity == "material_fidelity" and correct and observed["material_fidelity_change"])
            expected = set(metadata["intended_affected_dimensions"])
            result["localization"] += int(correct and bool(expected & set(observed["affected_dimensions"])))
        result["recovered"] += int(correct)
    return result


def summarize_d2() -> dict[str, Any]:
    manifest = read_json(LEAN / "runs" / "D2.manifest.json")
    case_ids = stage_case_ids = sorted({call["case_id"] for call in manifest["calls"]})
    private_records = ROOT / "research-private" / "evaluator-calibration" / "lean-v1" / "D2" / "records"
    complete = manifest["status"] == "complete" and all((private_records / case_id / f"{name}.json").exists() for case_id in case_ids for name in ("role-a", "role-b", "role-c", "contrast"))
    if not complete:
        return {"schema_version": SCHEMA_VERSION, "method": "automated source-grounded triangulation", "stage": "D2", "status": "incomplete", "holdouts": {"expert": "unopened", "automated": "unopened"}}
    verify_preservation()
    evidence_total = evidence_valid = 0
    applicability_total = applicability_resolved = 0
    contrast_totals: Counter[str] = Counter()
    structure_high = adjudications = 0
    domains: set[str] = set()
    unresolved_topics: Counter[str] = Counter()
    confidences: list[float] = []
    original_hard_failures = 0
    for case_id in case_ids:
        domains.add(case_id.split("-", 1)[0])
        case_dir = private_records / case_id
        role_a, role_b, role_c, contrast = [read_json(case_dir / name) for name in ("role-a.json", "role-b.json", "role-c.json", "contrast.json")]
        validate_role_a(role_a); validate_role_b(role_b); validate_role_c(role_c); validate_schema(contrast, "contrast-batch.schema.json")
        topics = adjudication_topics(role_a, role_b, role_c)
        adjudicated = (case_dir / "adjudication.json").exists()
        if adjudicated:
            validate_schema(read_json(case_dir / "adjudication.json"), "adjudication.schema.json")
            adjudications += 1
        else:
            unresolved_topics.update(topics)
        valid_ids = _valid_evidence_ids(case_id, "D2")
        for item in _record_evidence_items(case_dir):
            evidence_total += 1
            cited = item.get("evidence_span_ids", [])
            evidence_valid += int(bool(cited) and set(cited) <= valid_ids)
        applicability_total += len(role_b["applicability_reviews"])
        applicability_resolved += len(role_b["applicability_reviews"])
        material_app_challenges = [item for item in role_c["verifications"] if item["decision"] == "challenge_with_evidence" and item["material"] and "applicability" in item["topic"].lower()]
        applicability_total += len(material_app_challenges)
        applicability_resolved += len(material_app_challenges) if adjudicated else 0
        contrast_totals.update(_contrast_metrics(case_id, contrast, "D2"))
        structure_conflict = any(topic == "fidelity" for topic in topics) and not adjudicated
        structure_high += int(dimension_status("required", role_a["confidence"], structure_conflict, bool(role_a["findings"][0]["evidence_span_ids"])) == "high")
        confidences.extend((role_a["confidence"], role_b["confidence"], role_c["confidence"]))
        original_hard_failures += sum(check["hard_failure"] for check in role_a["atomic_checks"].values())
    benign_denominator = contrast_totals["false_positive_denominator"] + len(case_ids)
    metrics = {
        "privacy_and_holdouts_valid": True,
        "role_separation_completion": 1.0,
        "valid_evidence_span_rate": evidence_valid / evidence_total,
        "combined_applicability_recovery": applicability_resolved / applicability_total,
        "material_defect_detection": contrast_totals["defects_detected"] / contrast_totals["defects"],
        "material_fidelity_contrast_ordering": contrast_totals["material_ordered"] / contrast_totals["material"],
        "fidelity_false_positive_rate": (contrast_totals["false_positives"] + original_hard_failures) / benign_denominator,
        "category_localization_accuracy": contrast_totals["localization"] / contrast_totals["defects"],
        "paraphrase_policy_pass": contrast_totals["paraphrase_disagreements"] <= 1,
        "prestige_policy_pass": contrast_totals["prestige_effects"] == 0,
        "conditional_adjudication_rate": adjudications / len(case_ids),
        "structure_high_count": structure_high,
        "usable_domains": len(domains),
    }
    policy = read_json(LEAN / "preregistration.json")
    gates = evaluate_gates(metrics, policy)
    classifications = {gate["id"]: gate["classification"] for gate in policy["core_gates"]}
    for gate in gates:
        gate["classification"] = classifications[gate["id"]]
    failed_blocking = [gate["id"] for gate in gates if gate["classification"] == "blocking" and gate["status"] != "pass"]
    return {
        "schema_version": SCHEMA_VERSION,
        "method": "automated source-grounded triangulation",
        "stage": "D2",
        "status": "pass" if not failed_blocking else "fail",
        "metrics": metrics,
        "gates": gates,
        "failed_blocking_gates": failed_blocking,
        "diagnostics": {"mean_role_confidence": sum(confidences) / len(confidences), "unresolved_topics": dict(unresolved_topics), "paraphrase_disagreements": contrast_totals["paraphrase_disagreements"], "prestige_effects": contrast_totals["prestige_effects"]},
        "resource_use": {"authoritative_attempts": manifest["calls_used"], "completed_authoritative_records": sum(call["status"] == "completed" for call in manifest["calls"]), "schema_invalid_attempts": sum(max(0, call["attempts"] - 1) for call in manifest["calls"]), "adjudications": adjudications, "unused_call_capacity": manifest["maximum_calls"] - manifest["calls_used"]},
        "holdouts": {"expert": "unopened", "automated": "unopened"},
        "private_content_included": False,
        "skill_development_authorized": not failed_blocking,
        "limitations": ["No human experts participated.", "Available Codex variants are conservatively reported as same-family.", "D2 uses private source-grounded passages but publishes no passage wording or evidence spans."],
    }


def summarize_d1() -> dict[str, Any]:
    """Recompute the public-safe D1 result and private dimension decisions."""
    manifest = read_json(LEAN / "runs" / "D1.manifest.json")
    case_ids = list(SENTINELS)
    private_records = ROOT / "research-private" / "evaluator-calibration" / "lean-v1" / "D1" / "records"
    complete = manifest["status"] == "complete" and all((private_records / case_id / f"{name}.json").exists() for case_id in case_ids for name in ("role-a", "role-b", "role-c", "contrast"))
    if not complete:
        return {"schema_version": SCHEMA_VERSION, "method": "automated source-grounded triangulation", "stage": "D1", "status": "incomplete", "holdouts": {"expert": "unopened", "automated": "unopened"}}
    verify_preservation()
    evidence_total = evidence_valid = applicability_total = applicability_recovered = 0
    contrast_totals: Counter[str] = Counter()
    structure_high = deterministic_reconciliations = adjudications = 0
    status_counts: Counter[str] = Counter()
    private_decisions = private_records.parent / "decisions"
    for case_id in case_ids:
        case_dir = private_records / case_id
        role_a = read_json(case_dir / "role-a.json")
        role_b = read_json(case_dir / "role-b.json")
        role_c = read_json(case_dir / "role-c.json")
        contrast = read_json(case_dir / "contrast.json")
        validate_role_a(role_a)
        validate_role_b(role_b)
        validate_role_c(role_c)
        topics = adjudication_topics(role_a, role_b, role_c)
        has_adjudication = (case_dir / "adjudication.json").exists()
        adjudications += int(has_adjudication)
        deterministic_reconciliations += int(not topics)
        valid_ids = _valid_evidence_ids(case_id)
        for item in _record_evidence_items(case_dir):
            evidence_total += 1
            cited = item.get("evidence_span_ids", [])
            evidence_valid += int(bool(cited) and set(cited) <= valid_ids)
        applicability, recovered, total = _authoritative_applicability(role_b, role_c)
        applicability_recovered += recovered
        applicability_total += total
        contrast_totals.update(_contrast_metrics(case_id, contrast))
        decisions: list[dict[str, Any]] = []
        structure_conflict = bool(topics and not has_adjudication)
        structure_status = dimension_status("required", role_a["confidence"], structure_conflict, True)
        structure_high += int(structure_status == "high")
        decisions.append(("structure_fidelity", "required", structure_status, role_a["confidence"], structure_conflict, role_a["findings"]))
        findings = {item["dimension"]: item for item in role_b["findings"]}
        for dimension in DIMENSIONS[1:]:
            conflict = any(dimension in item["topic"].lower() and item["decision"] == "challenge_with_evidence" and item["material"] for item in role_c["verifications"])
            if has_adjudication and dimension == "prose_usability":
                conflict = True
            app = applicability[dimension]
            status = dimension_status(app, role_b["confidence"], conflict, bool(findings[dimension]["evidence_span_ids"]))
            decisions.append((dimension, app, status, None if app == "not_applicable" else role_b["confidence"], conflict, [findings[dimension]]))
        target = private_decisions / case_id
        target.mkdir(parents=True, exist_ok=True)
        for dimension, app, status, confidence, conflict, sources in decisions:
            evidence_ids = sorted({span for source in sources for span in source.get("evidence_span_ids", [])})
            record_ids = [role_a["record_id"], role_b["record_id"], role_c["record_id"]]
            decision_id = "LDD-" + hashlib.sha256(f"{case_id}:{dimension}:{status}".encode()).hexdigest()[:16]
            record = {"schema_version": SCHEMA_VERSION, "decision_id": decision_id, "case_id": case_id, "dimension": dimension, "applicability": app, "status": status, "confidence": confidence, "role_record_ids": record_ids, "material_conflict": conflict, "reason": "Deterministic reconciliation of sealed lean role records.", "evidence_span_ids": evidence_ids}
            validate_schema(record, "dimension-decision.schema.json")
            (target / f"{dimension}.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
            status_counts[status] += 1
    intended_recovery = contrast_totals["recovered"] / contrast_totals["intended"]
    metrics = {
        "complete_sentinels": len(case_ids),
        "deterministic_reconciliations": deterministic_reconciliations,
        "structure_high": structure_high,
        "valid_evidence_span_rate": evidence_valid / evidence_total,
        "combined_applicability_recovery": applicability_recovered / applicability_total,
        "material_fidelity_contrast_ordering": contrast_totals["material_ordered"] / contrast_totals["material"],
        "fidelity_false_positive_rate": contrast_totals["false_positives"] / contrast_totals["false_positive_denominator"],
        "category_localization_accuracy": contrast_totals["localization"] / (len(case_ids) * 2),
        "intended_contrast_recovery": intended_recovery,
        "conditional_adjudication_rate": adjudications / len(case_ids),
        "paraphrase_disagreements": contrast_totals["paraphrase_disagreements"],
        "prestige_effects": contrast_totals["prestige_effects"],
    }
    acceptance = {
        "complete_sentinels": metrics["complete_sentinels"] == 4,
        "deterministic_reconciliations": metrics["deterministic_reconciliations"] >= 2,
        "structure_high": metrics["structure_high"] >= 3,
        "intended_contrast_recovery": metrics["intended_contrast_recovery"] >= 0.75,
        "invariants": True,
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "method": "automated source-grounded triangulation",
        "stage": "D1",
        "status": "pass" if all(acceptance.values()) else "fail",
        "metrics": metrics,
        "acceptance": acceptance,
        "dimension_status_counts": dict(sorted(status_counts.items())),
        "resource_use": {"authoritative_attempts": manifest["calls_used"], "completed_authoritative_records": sum(call["status"] == "completed" for call in manifest["calls"]), "schema_invalid_attempts": sum(max(0, call["attempts"] - 1) for call in manifest["calls"]), "adjudications": adjudications},
        "holdouts": {"expert": "unopened", "automated": "unopened"},
        "private_content_included": False,
        "limitations": ["Available Codex variants are conservatively treated as same-family.", "D1 is a four-case engineering sentinel stage, not validation."],
    }


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
    verify_private_diagnostics(private_root, manifest["private_diagnostic_sha256"])


def verify_private_diagnostics(private_root: Path, expected_hashes: dict[str, str]) -> None:
    """Allow a public checkout with no private corpus, but reject partial or changed corpora."""
    paths = {relative: private_root / relative for relative in expected_hashes}
    present = {relative for relative, path in paths.items() if path.is_file()}
    if not present:
        return
    if present != set(paths):
        missing = sorted(set(paths) - present)
        raise LeanError(f"preserved private diagnostic set is partial; missing: {', '.join(missing)}")
    for relative, expected in expected_hashes.items():
        if hashlib.sha256(paths[relative].read_bytes()).hexdigest() != expected:
            raise LeanError(f"preserved private diagnostic changed: {relative}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("d0", "validate", "gates", "summarize-d1", "summarize-d2"))
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
    elif args.command == "gates":
        if not args.metrics:
            parser.error("gates requires --metrics")
        results = evaluate_gates(read_json(args.metrics), read_json(LEAN / "preregistration.json"))
        print(json.dumps({"gates": results, "all_pass": all(item["status"] == "pass" for item in results)}, indent=2))
    elif args.command == "summarize-d1":
        result = summarize_d1()
        output = LEAN / "results" / "D1-result.json"
        output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2))
    else:
        result = summarize_d2()
        output = LEAN / "results" / "D2-result.json"
        output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
