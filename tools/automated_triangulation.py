#!/usr/bin/env python3
"""Deterministic support for automated source-grounded triangulation.

This module deliberately does not call a language model.  It validates isolated
role records, reconciles evidence-backed applicability and fidelity findings,
computes preregistered metrics, emits public-safe aggregates, and verifies a
freeze manifest without opening either holdout.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "evals" / "automated-triangulation"
PREREGISTRATION = SUITE / "preregistration.json"
ATTESTATION = SUITE / "results" / "tier-a-attestation.json"

CATEGORIES = (
    "fidelity",
    "managerial_framing",
    "scholarly_positioning",
    "evidence_discipline",
    "prose_clarity",
)
APPLICABILITY = {"required", "optional", "not_applicable"}
APPLICABILITY_DECISIONS = {"accept", "challenge_with_evidence"}
ATOMIC_OUTCOMES = {"yes", "no", "uncertain"}
SILVER_STATUSES = {"silver_high_confidence", "silver_provisional", "unresolved"}
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
PRIVATE_KEYS = {
    "passage",
    "passage_text",
    "source_text",
    "full_text",
    "evidence_spans",
    "raw_annotations",
    "private_rationales",
    "reviewer_identity",
    "source_path",
    "pdf_path",
}


class TriangulationError(ValueError):
    """Raised when a deterministic evaluator invariant fails."""


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise TriangulationError(f"{path}: cannot read UTF-8 JSON: {exc}") from exc


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _evidence_span(span: Any) -> bool:
    """Accept a quoted span or a private location pointer plus a content hash."""
    if not isinstance(span, dict):
        return False
    location = span.get("location")
    quote = span.get("text")
    digest = span.get("sha256")
    return _nonempty(location) and (_nonempty(quote) or isinstance(digest, str) and len(digest) == 64)


def validate_schema(instance: Any, name: str) -> None:
    path = SUITE / "schemas" / name
    try:
        import jsonschema
    except ImportError as exc:  # pragma: no cover - development dependency guard
        raise TriangulationError("jsonschema is required for schema validation") from exc
    try:
        jsonschema.Draft202012Validator(read_json(path)).validate(instance)
    except jsonschema.ValidationError as exc:
        location = "/".join(str(item) for item in exc.absolute_path)
        raise TriangulationError(f"{name}: schema failure at {location or '<root>'}: {exc.message}") from exc


def validate_role_output(record: dict[str, Any], context: dict[str, Any] | None = None) -> None:
    validate_schema(record, "role-output.schema.json")
    if record["role"] == "meta_adjudication" and len(record.get("primary_role_output_ids", [])) < 2:
        raise TriangulationError("meta-adjudication requires at least two primary role outputs")
    if record["role"] != "meta_adjudication" and "primary_role_output_ids" in record:
        raise TriangulationError("a primary role cannot claim primary-role dependencies")
    for finding in record["findings"]:
        if finding["decision"] in {"supported", "not_supported"} and not finding["evidence_span_ids"]:
            raise TriangulationError(f"{finding['finding_id']}: substantive finding requires evidence")
    if context is None:
        return
    validate_schema(context, "context-packet.schema.json")
    if record["packet_id"] != context["packet_id"] or record["case_id"] != context["case_id"]:
        raise TriangulationError("role output does not match context packet")
    known_spans = {span["span_id"] for span in context["evidence_spans"]}
    referenced = {
        span_id for finding in record["findings"] for span_id in finding["evidence_span_ids"]
    }
    unknown = sorted(referenced - known_spans)
    if unknown:
        raise TriangulationError(f"role output references unknown evidence spans: {', '.join(unknown)}")


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def validate_split_manifest(record: dict[str, Any], require_target: bool = False) -> dict[str, Any]:
    validate_schema(record, "split-manifest.schema.json")
    unsigned = {key: value for key, value in record.items() if key != "manifest_sha256"}
    expected_hash = canonical_hash(unsigned)
    if record["manifest_sha256"] != expected_hash:
        raise TriangulationError(f"split manifest hash does not reconcile; expected {expected_hash}")
    clusters: dict[str, set[str]] = defaultdict(set)
    counts: Counter[tuple[str, str]] = Counter()
    seen_cases: set[str] = set()
    for case in record["cases"]:
        if case["case_id"] in seen_cases:
            raise TriangulationError(f"duplicate case ID: {case['case_id']}")
        seen_cases.add(case["case_id"])
        clusters[case["source_cluster_id"]].add(case["split"])
        counts[(case["split"], case["domain"])] += 1
        if case["split"] in {"validation", "holdout"} and case["silver_status"] != "silver_high_confidence":
            raise TriangulationError("validation and holdout accept only silver_high_confidence cases")
    leaked = sorted(cluster for cluster, splits in clusters.items() if len(splits) != 1)
    if leaked:
        raise TriangulationError(f"source clusters cross splits: {', '.join(leaked)}")
    if require_target:
        deficits = [
            f"{split}/{domain}={counts[(split, domain)]}"
            for split in ("development", "validation", "holdout")
            for domain in ("OM", "IS", "OR", "MGMT")
            if counts[(split, domain)] < 2
        ]
        if deficits:
            raise TriangulationError("split target requires at least two cases per domain/split: " + ", ".join(deficits))
    return {
        "valid": True,
        "case_count": len(record["cases"]),
        "source_cluster_count": len(clusters),
        "counts": {f"{split}:{domain}": count for (split, domain), count in sorted(counts.items())},
    }


def validate_applicability_challenge(record: dict[str, Any]) -> None:
    validate_schema(record, "applicability-challenge.schema.json")
    if record["category"] not in CATEGORIES:
        raise TriangulationError(f"unknown category: {record['category']}")
    if record["proposed_applicability"] not in APPLICABILITY:
        raise TriangulationError("invalid proposed_applicability")
    if record["decision"] not in APPLICABILITY_DECISIONS:
        raise TriangulationError("invalid applicability decision")
    if not _nonempty(record["rationale"]):
        raise TriangulationError("applicability rationale is required")
    if record["decision"] == "accept":
        if record.get("challenged_applicability") is not None:
            raise TriangulationError("accepted applicability cannot specify an alternative")
        return
    alternative = record.get("challenged_applicability")
    if alternative not in APPLICABILITY or alternative == record["proposed_applicability"]:
        raise TriangulationError("challenge must provide a different challenged_applicability")
    if not record.get("evidence_span_ids"):
        raise TriangulationError("challenge_with_evidence requires evidence span IDs")


def validate_atomic_checks(record: dict[str, Any]) -> list[str]:
    """Validate all 15 checks and return evidence-backed material failures."""
    validate_schema(record, "atomic-fidelity-result.schema.json")
    checks = record.get("checks")
    if not isinstance(checks, dict) or set(checks) != set(ATOMIC_CHECKS):
        missing = sorted(set(ATOMIC_CHECKS) - set(checks or {}))
        extra = sorted(set(checks or {}) - set(ATOMIC_CHECKS))
        raise TriangulationError(f"atomic checks must be exact; missing={missing}, extra={extra}")
    material_failures: list[str] = []
    for name in ATOMIC_CHECKS:
        result = checks[name]
        if not isinstance(result, dict) or result.get("verdict") not in ATOMIC_OUTCOMES:
            raise TriangulationError(f"{name}: invalid outcome")
        if not isinstance(result.get("material"), bool) or not _nonempty(result.get("rationale")):
            raise TriangulationError(f"{name}: material boolean and rationale are required")
        spans = result.get("evidence_span_ids", [])
        if not isinstance(spans, list):
            raise TriangulationError(f"{name}: malformed evidence span IDs")
        hard_failure = result.get("hard_failure") is True
        expected_hard_failure = result["verdict"] == "yes" and result["material"] and bool(spans)
        if hard_failure != expected_hard_failure:
            raise TriangulationError(f"{name}: hard_failure does not reconcile with verdict, materiality, and evidence")
        if expected_hard_failure:
            if not spans:
                raise TriangulationError(f"{name}: material yes requires supporting evidence")
            material_failures.append(name)
        if result["verdict"] != "yes" and result["material"]:
            raise TriangulationError(f"{name}: only a yes outcome may be material")
    reported = record.get("hard_failures", [])
    if set(reported) != set(material_failures):
        raise TriangulationError(
            f"hard_failures do not reconcile; expected {material_failures}, got {reported}"
        )
    expected_uncertain = sum(result["verdict"] == "uncertain" for result in checks.values()) / len(ATOMIC_CHECKS)
    if not math.isclose(float(record["uncertain_rate"]), expected_uncertain, abs_tol=1e-12):
        raise TriangulationError(f"uncertain_rate does not reconcile; expected {expected_uncertain}")
    return material_failures


def decide_silver_label(record: dict[str, Any]) -> str:
    """Derive a confidence-graded silver label; majority vote alone is insufficient."""
    # A final schema-valid decision can be validated directly. Rich private
    # adjudication inputs additionally support deterministic status derivation.
    if "role_output_ids" in record:
        validate_schema(record, "silver-decision.schema.json")
        if record["human_expert_review"] is not False:
            raise TriangulationError("automated silver decisions cannot claim human expert review")
        return record["silver_status"]
    applicability = record.get("applicability_role_decisions", [])
    findings = record.get("major_finding_role_decisions", [])
    role_ids = record.get("independent_role_ids", [])
    if len(set(role_ids)) < 3:
        expected = "unresolved"
    elif record.get("evidence_traceable") is not True or record.get("context_sufficient") is not True:
        expected = "unresolved"
    elif record.get("unresolved_model_context_ambiguity") is True:
        expected = "unresolved"
    else:
        app_count = Counter(applicability).most_common(1)[0][1] if applicability else 0
        finding_count = Counter(findings).most_common(1)[0][1] if findings else 0
        invariance = all(
            record.get(key) is True
            for key in ("contrast_ordering_stable", "paraphrase_stable", "prestige_blind")
        )
        if app_count >= 3 and finding_count >= 3 and invariance:
            expected = "silver_high_confidence"
        elif app_count >= 2 and finding_count >= 2:
            expected = "silver_provisional"
        else:
            expected = "unresolved"
    if record.get("silver_status") != expected:
        raise TriangulationError(
            f"silver status does not reconcile; expected {expected}, got {record.get('silver_status')}"
        )
    if expected == "silver_high_confidence" and record.get("split") in {"validation", "holdout"}:
        if record.get("source_cluster_id") in (None, ""):
            raise TriangulationError("validation/holdout silver cases require a source cluster")
    return expected


def _rate(numerator: float, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def _mean(values: Iterable[float]) -> float | None:
    values = list(values)
    return statistics.fmean(values) if values else None


def _rank(values: list[float]) -> list[float]:
    ordered = sorted(range(len(values)), key=values.__getitem__)
    result = [0.0] * len(values)
    index = 0
    while index < len(ordered):
        end = index + 1
        while end < len(ordered) and values[ordered[end]] == values[ordered[index]]:
            end += 1
        rank = (index + end - 1) / 2 + 1
        for position in ordered[index:end]:
            result[position] = rank
        index = end
    return result


def spearman(left: list[float], right: list[float]) -> float | None:
    if len(left) != len(right) or len(left) < 2:
        return None
    x, y = _rank(left), _rank(right)
    x_mean, y_mean = statistics.fmean(x), statistics.fmean(y)
    numerator = sum((a - x_mean) * (b - y_mean) for a, b in zip(x, y))
    denominator = math.sqrt(sum((a - x_mean) ** 2 for a in x) * sum((b - y_mean) ** 2 for b in y))
    return numerator / denominator if denominator else None


def compute_metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute only preregistered, public-safe metrics from case-level results."""
    if not records:
        raise TriangulationError("at least one metric record is required")
    applicability = [r for r in records if r.get("applicability_expected") is not None]
    private_app = [r for r in records if r.get("source_kind") == "private_anchor"]
    atomic = [r for r in records if r.get("expected_atomic_outcome") in {"yes", "no"}]
    positive = [r for r in atomic if r["expected_atomic_outcome"] == "yes"]
    negative = [r for r in atomic if r["expected_atomic_outcome"] == "no"]
    contrasts = [r for r in records if r.get("comparison_type") == "contrast"]
    fidelity_contrasts = [r for r in contrasts if r.get("affected_category") == "fidelity"]
    other_contrasts = [r for r in contrasts if r.get("affected_category") != "fidelity"]
    paraphrases = [r for r in records if r.get("comparison_type") == "paraphrase"]
    prestige = [r for r in records if r.get("comparison_type") == "prestige"]
    formatting = [r for r in records if r.get("comparison_type") == "formatting"]
    repeats = [r for r in records if r.get("comparison_type") == "repeat"]
    planted = [r for r in records if r.get("planted_claim") in {"empirical", "causal"}]
    scored = [float(r["normalized_score"]) for r in records if r.get("normalized_score") is not None]
    groups: dict[str, list[float]] = defaultdict(list)
    categories: dict[str, list[float]] = defaultdict(list)
    for record in records:
        if record.get("normalized_score") is not None and record.get("control_group"):
            groups[record["control_group"]].append(float(record["normalized_score"]))
        for category, value in record.get("category_scores", {}).items():
            if value is not None:
                categories[category].append(float(value))
    unaffected_movements = [
        abs(float(value))
        for record in contrasts
        for value in record.get("unaffected_category_movements", {}).values()
    ]
    span_checks = [r for r in records if r.get("judgment_kind") in {"fidelity", "evidence"}]
    metrics = {
        "synthetic_applicability_agreement": _rate(sum(r.get("applicability_actual") == r.get("applicability_expected") for r in applicability if r.get("source_kind") == "synthetic"), sum(r.get("source_kind") == "synthetic" for r in applicability)),
        "private_applicability_accept_rate": _rate(sum(r.get("applicability_decision") == "accept" for r in private_app), len(private_app)),
        "validation_unresolved_applicability_rate": _rate(sum(r.get("applicability_unresolved") is True for r in records if r.get("split") == "validation"), sum(r.get("split") == "validation" for r in records)),
        "actor_timing_information_objective_detection_rate": _rate(sum(r.get("detected") is True for r in positive if r.get("perturbation") in {"actor", "timing", "information", "objective"}), sum(r.get("perturbation") in {"actor", "timing", "information", "objective"} for r in positive)),
        "constraint_mechanism_detection_rate": _rate(sum(r.get("detected") is True for r in positive if r.get("perturbation") in {"constraint", "mechanism"}), sum(r.get("perturbation") in {"constraint", "mechanism"} for r in positive)),
        "false_positive_hard_failure_rate": _rate(sum(r.get("detected") is True for r in negative), len(negative)),
        "negative_hard_failure_agreement": _rate(sum(r.get("primary_agreement") is True for r in negative), len(negative)),
        "positive_hard_failure_agreement": _rate(sum(r.get("primary_agreement") is True for r in positive), len(positive)),
        "uncertain_atomic_rate": _rate(sum(r.get("atomic_outcome") == "uncertain" for r in records if "atomic_outcome" in r), sum("atomic_outcome" in r for r in records)),
        "material_fidelity_contrast_ordering": _rate(sum(r.get("ordered_correctly") is True for r in fidelity_contrasts), len(fidelity_contrasts)),
        "other_contrast_ordering": _rate(sum(r.get("ordered_correctly") is True for r in other_contrasts), len(other_contrasts)),
        "category_localization_accuracy": _rate(sum(r.get("localized") is True for r in contrasts), len(contrasts)),
        "unaffected_category_mean_movement": _mean(unaffected_movements),
        "paraphrase_mean_absolute_difference": _mean(abs(float(r["score_difference"])) for r in paraphrases),
        "prestige_mean_absolute_effect": _mean(abs(float(r["score_difference"])) for r in prestige),
        "formatting_substantive_mean_absolute_effect": _mean(abs(float(r["substantive_score_difference"])) for r in formatting),
        "repeated_run_rank_correlation": spearman([float(r["first_score"]) for r in repeats], [float(r["second_score"]) for r in repeats]),
        "inter_run_mean_absolute_difference": _mean(abs(float(r["first_score"]) - float(r["second_score"])) for r in repeats),
        "major_disagreement_adjudication_rate": _rate(sum(r.get("adjudicated") is True for r in records), len(records)),
        "above_95_rate": _rate(sum(value > 95 for value in scored), len(scored)),
        "ordered_control_distributions": all(groups.get(name) for name in ("positive", "intermediate", "negative")) and statistics.median(groups["positive"]) > statistics.median(groups["intermediate"]) > statistics.median(groups["negative"]),
        "nonconstant_categories": all(len(set(values)) > 1 for values in categories.values()) and set(CATEGORIES).issubset(categories),
        "valid_evidence_span_rate": _rate(sum(r.get("evidence_span_valid") is True for r in span_checks), len(span_checks)),
        "unsupported_claim_detection_rate": _rate(sum(r.get("detected") is True for r in planted), len(planted)),
        "record_count": len(records),
    }
    return metrics


def evaluate_gates(metrics: dict[str, Any], policy: dict[str, Any] | None = None) -> dict[str, Any]:
    policy = policy or read_json(PREREGISTRATION)
    outcomes: dict[str, dict[str, Any]] = {}
    for gate in policy["gates"]:
        metric = metrics.get(gate["metric"])
        if metric is None:
            passed = False
            reason = "metric unavailable"
        elif gate["operator"] == ">=":
            passed = metric >= gate["threshold"]
            reason = None
        elif gate["operator"] == "<=":
            passed = metric <= gate["threshold"]
            reason = None
        elif gate["operator"] == "<":
            passed = metric < gate["threshold"]
            reason = None
        elif gate["operator"] == "is":
            passed = metric is gate["threshold"]
            reason = None
        else:
            raise TriangulationError(f"unsupported gate operator: {gate['operator']}")
        outcomes[gate["id"]] = {
            "metric": gate["metric"], "observed": metric, "operator": gate["operator"],
            "threshold": gate["threshold"], "passed": passed, "reason": reason,
        }
    return {"passed": all(item["passed"] for item in outcomes.values()), "gates": outcomes}


def _walk_keys(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def public_safe_export(metrics: dict[str, Any], gate_result: dict[str, Any], provenance: dict[str, Any]) -> dict[str, Any]:
    """Build an aggregate-only record and reject accidental private payloads."""
    digest_source = json.dumps({"metrics": metrics, "provenance": provenance}, sort_keys=True).encode()
    metric_rows = []
    for key, value in sorted(metrics.items()):
        if key == "record_count":
            unit = "count"
        elif "correlation" in key:
            unit = "correlation"
        elif "movement" in key or "difference" in key or "effect" in key:
            unit = "points"
        else:
            unit = "proportion"
        numeric = float(value) if isinstance(value, (int, float, bool)) else None
        metric_rows.append({"metric_id": key, "value": numeric, "unit": unit, "sample_size": int(metrics["record_count"])})
    export = {
        "schema_version": "3.0.0-automated.1",
        "export_id": "AAE-" + hashlib.sha256(digest_source).hexdigest()[:16],
        "claim_label": "automated source-grounded triangulation",
        "split": provenance.get("split", "combined"),
        "case_counts": provenance.get("case_counts", {"OM": 0, "IS": 0, "OR": 0, "MGMT": 0, "total": int(metrics["record_count"])}),
        "metrics": metric_rows,
        "private_content_excluded": {
            "passage_text": True, "evidence_spans": True, "pdfs": True,
            "raw_annotations": True, "expert_identities": True,
        },
        "human_experts_participated": False,
        "expert_holdout_state": "expert_holdout_unopened",
        "source_manifest_sha256": provenance.get("source_manifest_sha256", provenance.get("input_sha256", "0" * 64)),
    }
    leaked = sorted(set(_walk_keys(export)) & PRIVATE_KEYS)
    if leaked:
        raise TriangulationError(f"public export contains private fields: {', '.join(leaked)}")
    serialized = json.dumps(export, ensure_ascii=False)
    if "expert validated" in serialized.casefold() or "gold label" in serialized.casefold():
        raise TriangulationError("public export contains prohibited validation terminology")
    validate_schema(export, "aggregate-export.schema.json")
    return export


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_freeze(record: dict[str, Any], root: Path = ROOT) -> dict[str, Any]:
    if record.get("expert_holdout_state") != "expert_holdout_unopened":
        raise TriangulationError("expert holdout must remain unopened")
    if record.get("automated_holdout_state") not in {"automated_holdout_unopened", "automated_holdout_opened"}:
        raise TriangulationError("invalid automated holdout state")
    files = record.get("files")
    if not isinstance(files, dict) or not files:
        raise TriangulationError("freeze manifest must list files")
    errors = []
    for relative, expected in sorted(files.items()):
        path = (root / relative).resolve()
        try:
            path.relative_to(root.resolve())
        except ValueError as exc:
            raise TriangulationError(f"freeze path escapes repository: {relative}") from exc
        actual = sha256_file(path) if path.is_file() else "missing"
        if actual != expected:
            errors.append(f"{relative}: expected {expected}, got {actual}")
    if errors:
        raise TriangulationError("freeze verification failed:\n" + "\n".join(errors))
    return {
        "freeze_commit": record.get("freeze_commit"),
        "files_verified": len(files),
        "expert_holdout_state": record["expert_holdout_state"],
        "automated_holdout_state": record["automated_holdout_state"],
    }


def validate_attestation(record: dict[str, Any]) -> dict[str, Any]:
    validate_schema(record, "tier-a-attestation.schema.json")
    required = {
        "schema_version", "authorization_tier", "status", "development_passed",
        "validation_passed", "evaluator_frozen", "automated_holdout_opened",
        "production_benchmark_complete", "experimental_release_eligible",
        "expert_holdout_unopened", "no_human_experts", "limitations", "freeze_commit",
    }
    if set(record) != required:
        raise TriangulationError(f"Tier A attestation fields must be exact; missing={sorted(required-set(record))}, extra={sorted(set(record)-required)}")
    if record["authorization_tier"] != "tier_a":
        raise TriangulationError("invalid Tier A authorization tier")
    if record["no_human_experts"] is not True or record["expert_holdout_unopened"] is not True:
        raise TriangulationError("Tier A requires no-human disclosure and unopened expert holdout")
    eligible = all(record[key] is True for key in (
        "development_passed", "validation_passed", "evaluator_frozen",
        "automated_holdout_opened", "production_benchmark_complete",
    ))
    if record["experimental_release_eligible"] is not eligible:
        raise TriangulationError(f"experimental_release_eligible must be {eligible}")
    if eligible and record["status"] != "pass":
        raise TriangulationError("eligible Tier A attestation must have pass status")
    if not eligible and record["status"] == "pass":
        raise TriangulationError("ineligible Tier A attestation cannot have pass status")
    if not isinstance(record["limitations"], list) or not record["limitations"]:
        raise TriangulationError("Tier A attestation requires limitations")
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    app = sub.add_parser("validate-applicability")
    app.add_argument("path", type=Path)
    atomic = sub.add_parser("validate-atomic")
    atomic.add_argument("path", type=Path)
    role = sub.add_parser("validate-role")
    role.add_argument("path", type=Path)
    role.add_argument("--context", type=Path)
    silver = sub.add_parser("validate-silver")
    silver.add_argument("path", type=Path)
    split = sub.add_parser("validate-split")
    split.add_argument("path", type=Path)
    split.add_argument("--require-target", action="store_true")
    metrics = sub.add_parser("metrics")
    metrics.add_argument("records", type=Path)
    metrics.add_argument("--output", type=Path)
    freeze = sub.add_parser("verify-freeze")
    freeze.add_argument("manifest", type=Path)
    attest = sub.add_parser("validate-attestation")
    attest.add_argument("path", type=Path, nargs="?", default=ATTESTATION)
    args = parser.parse_args(argv)
    try:
        if args.command == "validate-applicability":
            record = read_json(args.path)
            validate_applicability_challenge(record)
            result = {"valid": True, "case_id": record["case_id"]}
        elif args.command == "validate-atomic":
            record = read_json(args.path)
            result = {"valid": True, "hard_failures": validate_atomic_checks(record)}
        elif args.command == "validate-role":
            record = read_json(args.path)
            context = read_json(args.context) if args.context else None
            validate_role_output(record, context)
            result = {"valid": True, "output_id": record["output_id"], "role": record["role"]}
        elif args.command == "validate-silver":
            record = read_json(args.path)
            result = {"valid": True, "silver_status": decide_silver_label(record)}
        elif args.command == "validate-split":
            result = validate_split_manifest(read_json(args.path), args.require_target)
        elif args.command == "metrics":
            records = read_json(args.records)
            if not isinstance(records, list):
                raise TriangulationError("metric input must be a JSON array")
            computed = compute_metrics(records)
            gates = evaluate_gates(computed)
            result = public_safe_export(computed, gates, {"input_sha256": sha256_file(args.records)})
            if args.output:
                write_json(args.output, result)
        elif args.command == "verify-freeze":
            result = verify_freeze(read_json(args.manifest))
        else:
            result = validate_attestation(read_json(args.path))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except TriangulationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
