#!/usr/bin/env python3
"""Deterministic safeguards for the additive lean D2R evaluator repair."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
REPAIR = ROOT / "evals" / "automated-triangulation" / "lean-v2"
SEALED_COMMIT = "0ad46b2cee197175cd549a51b003f695627724b1"
SCHEMA_VERSION = "3.1.0-lean.2"
D2R_CASES = ("OM-P02", "MGMT-P02", "IS-P02", "OR-P01", "IS-P01")
DIMENSIONS = (
    "structure_fidelity",
    "managerial_framing",
    "scholarly_positioning",
    "evidence_discipline",
    "prose_usability",
)
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
DISAGREEMENT_CLASSES = {
    "material_semantic_disagreement",
    "applicability_boundary_disagreement",
    "evidence_localization_mismatch",
    "schema_or_format_mismatch",
    "terminology_only_difference",
    "insufficient_context",
    "invalid_challenge",
}
PRESTIGE_KEYS = {
    "journal",
    "journal_name",
    "outlet",
    "publication_status",
    "author",
    "authors",
    "institution",
    "doi",
    "citation_count",
    "article_title",
    "title",
    "source_quality_label",
    "quality_label",
    "top_journal_designation",
    "top_journal",
    "location",
}
REQUIRED_CONTEXT = (
    "actor",
    "decisions",
    "timing",
    "decision_time_information",
    "objective",
    "constraints",
    "mechanism",
)


class RepairError(ValueError):
    pass


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def sha256_value(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def validate_schema(record: Any, schema_name: str) -> None:
    import jsonschema

    schema = json.loads((REPAIR / "schemas" / schema_name).read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(record)


def verify_lean_v1_preservation(commit: str = SEALED_COMMIT) -> None:
    """Require every tracked lean-v1 byte to match the sealed PR #5 head."""
    prefix = "evals/automated-triangulation/lean-v1/"
    tracked = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", commit, prefix],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    if not tracked:
        raise RepairError("sealed lean-v1 tree is unavailable")
    current = {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / prefix).rglob("*")
        if path.is_file()
    }
    expected = set(tracked)
    if current != expected:
        raise RepairError(f"lean-v1 path drift: added={sorted(current-expected)}, missing={sorted(expected-current)}")
    diff = subprocess.run(
        ["git", "diff", "--no-ext-diff", "--quiet", commit, "--", prefix], cwd=ROOT
    )
    if diff.returncode != 0:
        raise RepairError("sealed lean-v1 content changed")


def classify_disagreement(
    *,
    substantive_changed: bool = False,
    applicability_changed: bool = False,
    denominator_or_required_output_changed: bool = False,
    fidelity_changed: bool = False,
    hard_failure_changed: bool = False,
    contrast_order_changed: bool = False,
    support_status_changed: bool = False,
    evidence_only: bool = False,
    schema_only: bool = False,
    terminology_only: bool = False,
    insufficient_context: bool = False,
    challenge_has_valid_evidence: bool = True,
) -> str:
    """Apply the preregistered primary-class precedence without relabeling semantics."""
    if not challenge_has_valid_evidence:
        return "invalid_challenge"
    if insufficient_context:
        return "insufficient_context"
    if applicability_changed and denominator_or_required_output_changed:
        return "applicability_boundary_disagreement"
    if any((substantive_changed, fidelity_changed, hard_failure_changed, contrast_order_changed, support_status_changed)):
        return "material_semantic_disagreement"
    if evidence_only:
        return "evidence_localization_mismatch"
    if schema_only:
        return "schema_or_format_mismatch"
    if terminology_only:
        return "terminology_only_difference"
    return "invalid_challenge"


def needs_semantic_adjudication(classification: str) -> bool:
    if classification not in DISAGREEMENT_CLASSES:
        raise RepairError(f"unknown disagreement class: {classification}")
    return classification in {"material_semantic_disagreement", "applicability_boundary_disagreement"}


def derive_applicability(case: dict[str, Any]) -> dict[str, str]:
    """Predetermine applicability from task construction before any role executes."""
    function = str(case.get("passage_function", "")).lower().replace("-", "_")
    task = str(case.get("requested_task", "")).lower()
    attempted = {str(value) for value in case.get("attempted_layers", [])}
    explicit = {str(value) for value in case.get("required_layers", [])}
    context = case.get("context", {})

    result = {dimension: "not_applicable" for dimension in DIMENSIONS}
    result["structure_fidelity"] = "required"
    managerial_required = {"managerial_implications", "business_problem", "managerial_recommendation"}
    scholarly_required = {"contribution", "introduction", "research_question", "research_opportunity"}
    writing_functions = managerial_required | scholarly_required | {"rewrite", "narrative"}

    if function in managerial_required:
        result["managerial_framing"] = "required"
    elif function in {"model_setting", "computational_contribution", "contribution"}:
        result["managerial_framing"] = "optional"

    if function in scholarly_required:
        result["scholarly_positioning"] = "required"
    elif function == "business_problem":
        result["scholarly_positioning"] = "optional"

    has_claims = bool(case.get("has_external_claims")) or bool(context.get("empirical_claims"))
    result["evidence_discipline"] = "required" if has_claims else "optional"
    result["prose_usability"] = "required" if function in writing_functions or any(
        token in task for token in ("write", "rewrite", "draft", "frame", "paragraph", "explain")
    ) else "optional"

    for dimension in attempted | explicit:
        if dimension in result:
            result[dimension] = "required"
    for dimension in case.get("optional_layers", []):
        if dimension in result and dimension not in explicit and dimension not in attempted:
            result[dimension] = "optional"
    return result


def resolve_evidence_localization(
    *,
    case_id: str,
    finding_key: str,
    role_findings: list[dict[str, Any]],
    packet: dict[str, Any],
) -> dict[str, Any]:
    """Resolve compatible span localization only; never decide a substantive conflict."""
    if len(role_findings) < 2:
        raise RepairError("evidence repair requires at least two role findings")
    signatures = {
        (item.get("assessment"), item.get("material"), item.get("hard_failure"))
        for item in role_findings
    }
    if len(signatures) != 1:
        raise RepairError("substantive finding, materiality, or hard-failure disagreement requires adjudication")
    spans = {item["span_id"]: item for item in packet.get("evidence_spans", [])}
    if not spans:
        raise RepairError("packet contains no evidence spans")
    original = [list(item.get("evidence_span_ids", [])) for item in role_findings]
    referenced = {span_id for group in original for span_id in group}
    if not referenced or not referenced <= set(spans):
        raise RepairError("referenced evidence must belong to the same packet")
    direct = sorted(
        span_id for span_id in referenced if finding_key in set(spans[span_id].get("supports", []))
    )
    if not direct:
        raise RepairError("no referenced span directly supports the finding")
    accepted = direct[0]
    rejected = sorted(referenced - {accepted})
    record = {
        "schema_version": SCHEMA_VERSION,
        "repair_id": "LER-" + hashlib.sha256(f"{case_id}:{finding_key}:{accepted}".encode()).hexdigest()[:16],
        "case_id": case_id,
        "finding_key": finding_key,
        "classification": "evidence_localization_mismatch",
        "original_evidence_references": original,
        "accepted_evidence_reference": accepted,
        "superseded_evidence_references": rejected,
        "deterministic_rule": "same_finding_same_packet_direct_support_v1",
        "substantive_finding_unchanged": True,
        "fidelity_unchanged": True,
        "hard_failure_unchanged": True,
        "contrast_ordering_unchanged": True,
        "confidence_change": 0.0,
        "reason_no_semantic_adjudication": "Roles agree on status and materiality; the packet support index resolves compatible span granularity.",
    }
    record["record_hash"] = sha256_value(record)
    return record


def _scrub(value: Any, forbidden_values: Iterable[str]) -> Any:
    forbidden = [item for item in forbidden_values if item]
    if isinstance(value, dict):
        return {
            key: _scrub(child, forbidden)
            for key, child in value.items()
            if key.lower() not in PRESTIGE_KEYS and key.lower() not in {"source_id", "source_cluster_id", "source_sha256"}
        }
    if isinstance(value, list):
        return [_scrub(child, forbidden) for child in value]
    if isinstance(value, str):
        cleaned = value
        for phrase in sorted(forbidden, key=len, reverse=True):
            cleaned = re.sub(re.escape(phrase), "[REDACTED]", cleaned, flags=re.IGNORECASE)
        return cleaned
    return value


def blind_production_packet(packet: dict[str, Any], forbidden_values: Iterable[str] = ()) -> dict[str, Any]:
    """Create an ordinary judge packet with physical cue removal, not prompt-only masking."""
    blinded = _scrub(deepcopy(packet), forbidden_values)
    raw_case = str(packet.get("case_id", "unknown"))
    blinded["case_id"] = "CASE-" + hashlib.sha256(raw_case.encode()).hexdigest()[:16]
    blinded["source_ref"] = "SRC-" + hashlib.sha256(str(packet.get("source_id", "source")).encode()).hexdigest()[:16]
    blinded["prestige_cues_removed"] = True
    return blinded


def assert_no_prestige_cues(packet: dict[str, Any], forbidden_values: Iterable[str] = ()) -> None:
    serialized = json.dumps(packet, ensure_ascii=False).lower()
    present_keys = [key for key in PRESTIGE_KEYS if f'"{key.lower()}"' in serialized]
    present_values = [value for value in forbidden_values if value and value.lower() in serialized]
    if present_keys or present_values:
        raise RepairError(f"prestige cue reached production packet: keys={present_keys}, values={present_values}")


def validate_and_repair_packet(packet: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Normalize representation-only defects and emit a semantic-preservation audit."""
    original = deepcopy(packet)
    repaired = deepcopy(packet)
    transformations: list[dict[str, str]] = []

    def record_change(kind: str, pointer: str, before: Any, after: Any, reason: str) -> None:
        transformations.append({
            "kind": kind,
            "json_pointer": pointer,
            "before_sha256": sha256_value(before),
            "after_sha256": sha256_value(after),
            "reason": reason,
        })

    # Normalize only representation. No semantic field is synthesized.
    for old, new in (("passageFunction", "passage_function"), ("requestedTask", "requested_task")):
        if old in repaired and new not in repaired:
            before = repaired[old]
            repaired[new] = repaired.pop(old)
            record_change("field_name_normalization", f"/{old}", {old: before}, {new: before}, f"normalized field name to {new}")
    for span in repaired.get("evidence_spans", []):
        supports = span.get("supports", [])
        normalized = [item if str(item).startswith("context.") else f"context.{item}" for item in supports]
        if normalized != supports:
            span["supports"] = normalized
            index = repaired["evidence_spans"].index(span)
            record_change("supports_path_normalization", f"/evidence_spans/{index}/supports", supports, normalized, "prefixed derived context paths")
        if isinstance(span.get("text"), str):
            normalized_text = span["text"].replace("\r\n", "\n").replace("\r", "\n")
            if normalized_text != span["text"]:
                before_text = span["text"]
                span["text"] = normalized_text
                index = repaired["evidence_spans"].index(span)
                record_change("unicode_normalization", f"/evidence_spans/{index}/text", before_text, normalized_text, "normalized line endings")

    required_top = ("case_id", "passage_function", "requested_task", "passage_sha256", "context", "evidence_spans")
    missing = [key for key in required_top if key not in repaired]
    if missing:
        raise RepairError(f"missing required packet fields: {missing}")
    context = repaired["context"]
    absent_context = [key for key in REQUIRED_CONTEXT if key not in context]
    if absent_context:
        raise RepairError(f"missing semantic context fields; deterministic repair forbidden: {absent_context}")
    unresolved_context = [key for key in REQUIRED_CONTEXT if context[key] in (None, "", [])]
    if not re.fullmatch(r"[0-9a-f]{64}", repaired["passage_sha256"]):
        raise RepairError("invalid passage/source-window hash")
    span_ids = [item.get("span_id") for item in repaired["evidence_spans"]]
    if len(span_ids) != len(set(span_ids)) or any(not re.fullmatch(r"ES-[0-9]{3}", str(item)) for item in span_ids):
        raise RepairError("evidence-span identifiers are invalid or duplicated")
    if "\ufffd" in json.dumps(repaired, ensure_ascii=False):
        raise RepairError("Unicode replacement character found")

    audit = {
        "schema_version": SCHEMA_VERSION,
        "audit_id": "PRA-" + hashlib.sha256(canonical_json(original)).hexdigest()[:16],
        "case_id": str(repaired["case_id"]),
        "original_packet_ref": "private:original-preserved.json",
        "repaired_packet_ref": "private:production-packet.json",
        "original_sha256": sha256_value(original),
        "repaired_sha256": sha256_value(repaired),
        "validation_before": [
            *(f"unresolved context field preserved as unknown: {key}" for key in unresolved_context),
            *(f"representation normalization required at {item['json_pointer']}" for item in transformations),
        ],
        "transformations": transformations,
        "validation_after": ["required fields present", "evidence identifiers unique", "source-window hash valid", "semantic unknowns not imputed"],
        "substantive_content_changed": False,
        "prestige_cues_removed": True,
    }
    return repaired, audit


def validate_role_a_prompt(prompt_contract: dict[str, Any]) -> None:
    checks = prompt_contract.get("atomic_checks", [])
    if checks != list(ATOMIC_CHECKS) or len(checks) != len(set(checks)):
        raise RepairError("Role A prompt must enumerate all 15 atomic checks exactly once in canonical order")
    required = set(prompt_contract.get("required_output_keys", []))
    expected = {
        "schema_version", "record_id", "case_id", "role", "prompt_hash", "model", "fresh_context",
        "sealed_at", "confidence", "structure", "atomic_checks", "findings",
    }
    if required != expected:
        raise RepairError("Role A required output keys do not match its schema contract")


def evaluate_d2r_gates(metrics: dict[str, Any], policy: dict[str, Any]) -> list[dict[str, Any]]:
    results = []
    for gate in policy["core_gates"]:
        observed = metrics.get(gate["metric"])
        operator = gate["operator"]
        threshold = gate["threshold"]
        if observed is None:
            status = "not_assessed"
        elif operator == "is":
            status = "pass" if observed is threshold else "fail"
        elif operator == ">=":
            status = "pass" if observed >= threshold else "fail"
        elif operator == "<=":
            status = "pass" if observed <= threshold else "fail"
        elif operator == "=":
            status = "pass" if observed == threshold else "fail"
        else:
            raise RepairError(f"unsupported operator: {operator}")
        results.append({**gate, "observed": observed, "status": status})
    return results


def development_authorized(gates: list[dict[str, Any]]) -> bool:
    return bool(gates) and all(gate["status"] == "pass" for gate in gates)
