#!/usr/bin/env python3
"""Prepare private context packets and public-safe calibration manifests.

Copyrighted page text is written only below the ignored research-private tree.
Tracked exports contain opaque IDs and hashes, never source wording or evidence spans.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

import yaml

import automated_triangulation as auto


ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / "research-private" / "evaluator-calibration"
PUBLIC = ROOT / "evals" / "automated-triangulation"
LEGACY = ROOT / "evals" / "calibration"
EXPERT_BASELINE_COMMIT = "540e72071ea35be228ef4c72c1b3276223631a44"

SPLITS = {
    "OM-P01": "development", "OM-P02": "development",
    "OM-P04": "validation", "OM-P05": "validation",
    "OM-P03": "holdout", "OM-P06": "holdout",
    "IS-P01": "development", "IS-P02": "development",
    "IS-P03": "validation", "IS-P04": "validation",
    "IS-P05": "holdout", "IS-P06": "holdout",
    "OR-P01": "development", "OR-P02": "development",
    "OR-P05": "validation", "OR-P06": "validation",
    "OR-P03": "holdout", "OR-P04": "holdout",
    "MGMT-P01": "development", "MGMT-P02": "development",
    "MGMT-P03": "validation", "MGMT-P04": "validation",
    "MGMT-P05": "holdout", "MGMT-P06": "holdout",
}


class PreparationError(RuntimeError):
    pass


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git_blob_bytes(revision: str, relative: str) -> bytes:
    try:
        return subprocess.check_output(["git", "show", f"{revision}:{relative}"], cwd=ROOT)
    except subprocess.CalledProcessError as exc:
        raise PreparationError(f"cannot read tracked blob {revision}:{relative}") from exc


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def frontmatter(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"---\r?\n(.*?)\r?\n---\r?\n(.*)", text, re.DOTALL)
    if not match:
        raise PreparationError(f"missing YAML frontmatter: {path}")
    return yaml.safe_load(match.group(1)), match.group(2)


def body_field(body: str, label: str) -> str:
    match = re.search(rf"^- {re.escape(label)}:\s*(.+)$", body, re.MULTILINE)
    return match.group(1).strip() if match else "not supplied"


def page_numbers(location: str) -> tuple[int, int]:
    numbers = [int(value) for value in re.findall(r"\d+", location)]
    if not numbers:
        raise PreparationError(f"page location has no page number: {location!r}")
    return numbers[0], numbers[-1]


def extract_pages(text: str, start: int, end: int) -> str:
    pattern = re.compile(r"===== PAGE (\d+) =====\r?\n")
    matches = list(pattern.finditer(text))
    selected: list[str] = []
    for index, match in enumerate(matches):
        page = int(match.group(1))
        if start <= page <= end:
            boundary = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            selected.append(text[match.end():boundary].strip())
    return "\n\n".join(part for part in selected if part)


def metadata_by_source() -> dict[str, dict]:
    records: dict[str, dict] = {}
    for path in sorted((PRIVATE / "source-metadata").glob("*.yaml")):
        record = yaml.safe_load(path.read_text(encoding="utf-8"))
        records[record["source_id"]] = record
    return records


def prepare_private_packets() -> list[dict]:
    metadata = metadata_by_source()
    public_records: list[dict] = []
    for note_path in sorted((PRIVATE / "passage-candidates").glob("*.md")):
        header, body = frontmatter(note_path)
        passage_id = header["passage_id"]
        if passage_id not in SPLITS:
            raise PreparationError(f"no split registered for {passage_id}")
        source = metadata[header["source_id"]]
        pdf_path = PRIVATE / source["local_file"]
        text_path = PRIVATE / "source-passages" / "extracted-text" / f"{pdf_path.stem}.txt"
        start, end = page_numbers(header["page_location"])
        source_window = extract_pages(text_path.read_text(encoding="utf-8", errors="replace"), start, end)
        if len(source_window.split()) < 80:
            raise PreparationError(f"insufficient readable context for {passage_id}")
        structure = {
            "passage_function": header.get("heading", "not supplied"),
            "actor": body_field(body, "Actor"),
            "decision": body_field(body, "Decision"),
            "timing": body_field(body, "Timing"),
            "decision_time_information": body_field(body, "Decision-time information"),
            "objective": body_field(body, "Objective"),
            "constraints": body_field(body, "Constraints"),
            "mechanism": body_field(body, "Mechanism"),
            "model_or_study_scope": body_field(body, "Limitations"),
            "evidence_supplied": body_field(body, "Evidence status"),
            "required_surrounding_context": body_field(body, "Required context"),
        }
        packet = {
            "schema_version": "1.0.0",
            "passage_id": passage_id,
            "source_id": header["source_id"],
            "domain": source["domain"],
            "provisional_split": SPLITS[passage_id],
            "source_sha256": source["sha256"],
            "page_location": header["page_location"],
            "heading": header["heading"],
            "article_identity": {
                "title": source["title"], "authors": source["authors"],
                "outlet": source["outlet"], "year": source["year"],
                "doi": source.get("doi"), "acquired_version": source["acquired_version"],
            },
            "candidate_summary": re.search(r"Original summary:\s*(.+)", body).group(1).strip(),
            "reconstructed_context": structure,
            "source_window": source_window,
            "source_window_sha256": sha256_bytes(source_window.encode("utf-8")),
            "annotation_status": "pending_role_review",
            "copyright_boundary": "private_local_only",
        }
        private_path = PRIVATE / "model-context" / f"{passage_id.lower()}.json"
        write_json(private_path, packet)
        public_records.append({
            "passage_id": passage_id,
            "source_id": header["source_id"],
            "domain": source["domain"],
            "provisional_split": SPLITS[passage_id],
            "source_sha256": source["sha256"],
            "context_sha256": sha256_bytes(json.dumps(structure, sort_keys=True).encode("utf-8")),
            "source_window_sha256": packet["source_window_sha256"],
            "silver_status": "unresolved",
            "public_text_included": False,
        })
    if len(public_records) != 24:
        raise PreparationError(f"expected 24 passage packets, found {len(public_records)}")
    write_json(
        PUBLIC / "top-journal-private-manifests" / "private-anchor-manifest.json",
        {"schema_version": "1.0.0", "records": public_records},
    )
    return public_records


def legacy_holdout_files() -> list[Path]:
    manifest = json.loads((LEGACY / "public-metadata" / "synthetic-suite-manifest.json").read_text(encoding="utf-8"))
    ids = {record["case_id"] for record in manifest["records"] if record["split"] == "holdout"}
    paths = [LEGACY / "preregistration.json", LEGACY / "public-metadata" / "synthetic-suite-manifest.json"]
    for case_id in sorted(ids):
        matches = sorted(LEGACY.rglob(f"{case_id}.*.json"))
        matches = [path for path in matches if "results" not in path.parts]
        if len(matches) != 2:
            raise PreparationError(f"expected generator/judge pair for expert holdout {case_id}, found {len(matches)}")
        paths.extend(matches)
    return paths


def record_expert_holdout() -> dict:
    files = {
        relative: sha256_bytes(git_blob_bytes(EXPERT_BASELINE_COMMIT, relative))
        for path in legacy_holdout_files()
        for relative in [path.relative_to(ROOT).as_posix()]
    }
    record = {
        "schema_version": "1.0.0",
        "baseline_commit": EXPERT_BASELINE_COMMIT,
        "hash_scope": "canonical_git_blob_bytes",
        "expert_holdout_unopened": True,
        "files": files,
    }
    write_json(PUBLIC / "top-journal-private-manifests" / "expert-holdout-baseline.json", record)
    return record


def verify() -> dict:
    baseline_path = PUBLIC / "top-journal-private-manifests" / "expert-holdout-baseline.json"
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    errors = []
    for relative, expected in baseline["files"].items():
        try:
            actual = sha256_bytes(git_blob_bytes("HEAD", relative))
        except PreparationError:
            actual = None
        if actual != expected:
            errors.append(f"expert holdout changed: {relative}")
    tracked = subprocess.check_output(["git", "ls-files", "research-private"], cwd=ROOT, text=True).strip()
    if tracked:
        errors.append("research-private contains tracked files")
    result = {
        "expert_holdout_unopened": not errors and baseline.get("expert_holdout_unopened") is True,
        "automated_holdout_unopened": True,
        "automated_holdout_opened": False,
        "private_paths_tracked": bool(tracked),
        "valid": not errors,
        "errors": errors,
    }
    print(json.dumps(result, indent=2))
    if errors:
        raise SystemExit(1)
    return result


def annotation_status() -> dict:
    manifest = json.loads(
        (PUBLIC / "top-journal-private-manifests" / "private-anchor-manifest.json").read_text(encoding="utf-8")
    )
    by_id = {record["passage_id"]: record for record in manifest["records"]}
    role_counts: dict[str, int] = {}
    silver_counts = {"silver_high_confidence": 0, "silver_provisional": 0, "unresolved": 0}
    case_counts = {"development": 0, "validation": 0, "holdout": 0}
    errors: list[str] = []
    annotated_holdout: list[str] = []
    for passage_id, public in sorted(by_id.items()):
        root = PRIVATE / "judge-packets" / "automated" / passage_id
        context_path = root / "context-packet.json"
        if not context_path.exists():
            continue
        case_counts[public["provisional_split"]] += 1
        if public["provisional_split"] == "holdout":
            annotated_holdout.append(passage_id)
        try:
            context = json.loads(context_path.read_text(encoding="utf-8"))
            auto.validate_schema(context, "context-packet.schema.json")
            for role_path in sorted((root / "roles").glob("*.json")):
                role = json.loads(role_path.read_text(encoding="utf-8"))
                auto.validate_role_output(role, context)
                role_counts[role["role"]] = role_counts.get(role["role"], 0) + 1
            silver_path = root / "silver-decision.json"
            if silver_path.exists():
                silver = json.loads(silver_path.read_text(encoding="utf-8"))
                auto.validate_silver_decision(silver)
                silver_counts[silver["silver_status"]] += 1
        except (ValueError, OSError, json.JSONDecodeError) as exc:
            errors.append(f"{passage_id}: {exc}")
    if annotated_holdout:
        errors.append("automated holdout has been inspected: " + ", ".join(annotated_holdout))
    result = {
        "method": "automated source-grounded triangulation",
        "context_packets": sum(case_counts.values()),
        "contexts_by_split": case_counts,
        "role_outputs": role_counts,
        "silver_statuses": silver_counts,
        "expert_holdout_unopened": True,
        "automated_holdout_unopened": not annotated_holdout,
        "valid": not errors,
        "errors": errors,
    }
    print(json.dumps(result, indent=2))
    if errors:
        raise SystemExit(1)
    return result


def finalize_variants(passage_id: str) -> dict:
    root = PRIVATE / "contrast-variants" / "automated" / passage_id
    files = sorted(path for path in root.glob("*.json") if path.name != "manifest.json")
    if not files:
        raise PreparationError(f"no private variants found for {passage_id}")
    records: list[dict] = []
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        text = data.get("passage")
        metadata = data.get("contrast_metadata")
        if not isinstance(text, str) or not text.strip() or not isinstance(metadata, dict):
            raise PreparationError(f"malformed private contrast: {path.name}")
        auto.validate_schema(metadata, "contrast-metadata.schema.json")
        digest = sha256_bytes(text.encode("utf-8"))
        data["passage_sha256"] = digest
        data["word_count"] = len(re.findall(r"\b\w+\b", text))
        write_json(path, data)
        records.append({
            "variant_type": metadata["variant_type"],
            "variant_case_id": metadata["variant_case_id"],
            "contrast_id": metadata["contrast_id"],
            "passage_sha256": digest,
            "word_count": data["word_count"],
        })
    expected = {
        "actor_perturbation", "timing_perturbation", "information_perturbation",
        "objective_perturbation", "mechanism_deletion", "trade_off_deletion",
        "unsupported_empirical_claim_insertion", "unsupported_causal_pathway_insertion",
        "generic_gap_replacement", "boundary_deletion", "verbosity_insertion",
        "prestige_label_manipulation", "faithful_paraphrase", "simplified_concise_rewrite",
    }
    actual = {record["variant_type"] for record in records}
    if actual != expected:
        raise PreparationError(f"contrast set mismatch; missing={sorted(expected-actual)}, extra={sorted(actual-expected)}")
    private_manifest = {
        "schema_version": "3.0.0-automated.1",
        "passage_id": passage_id,
        "private_source_derived": True,
        "variants": records,
    }
    write_json(root / "manifest.json", private_manifest)
    public_path = PUBLIC / "contrast-sets" / f"{passage_id.lower()}-private-manifest.json"
    write_json(public_path, {
        "schema_version": "3.0.0-automated.1",
        "passage_id": passage_id,
        "variant_count": len(records),
        "variants": records,
        "private_text_included": False,
        "human_experts_participated": False,
    })
    result = {"passage_id": passage_id, "variants": len(records), "public_manifest": str(public_path.relative_to(ROOT))}
    print(json.dumps(result, indent=2))
    return result


def export_partial_status() -> dict:
    manifest_path = PUBLIC / "top-journal-private-manifests" / "private-anchor-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    development = [record for record in manifest["records"] if record["provisional_split"] == "development"]
    counts = {domain: 0 for domain in ("OM", "IS", "OR", "MGMT")}
    completed_roles = 0
    complete_cases = 0
    silver = {"silver_high_confidence": 0, "silver_provisional": 0, "unresolved": 0}
    primary_roles = {
        "model_structure", "passage_function", "fidelity", "managerial_framing",
        "scholarly_positioning", "evidence", "prose_usability", "adversarial_review",
    }
    for record in development:
        root = PRIVATE / "judge-packets" / "automated" / record["passage_id"]
        if not (root / "context-packet.json").exists():
            continue
        counts[record["domain"]] += 1
        roles = set()
        for path in (root / "roles").glob("*.json"):
            role = json.loads(path.read_text(encoding="utf-8")).get("role")
            if role in primary_roles:
                roles.add(role)
        completed_roles += len(roles)
        complete_cases += roles == primary_roles
        decision = root / "silver-decision.json"
        if decision.exists():
            status = json.loads(decision.read_text(encoding="utf-8"))["silver_status"]
            silver[status] += 1
    total = sum(counts.values())
    expected_roles = total * len(primary_roles)
    metrics = [
        {"metric_id": "context_packet_count", "value": total, "unit": "count", "sample_size": total},
        {"metric_id": "primary_role_output_count", "value": completed_roles, "unit": "count", "sample_size": expected_roles},
        {"metric_id": "primary_role_completion_rate", "value": completed_roles / expected_roles if expected_roles else None, "unit": "proportion", "sample_size": expected_roles},
        {"metric_id": "fully_annotated_case_count", "value": complete_cases, "unit": "count", "sample_size": total},
        {"metric_id": "silver_high_confidence_count", "value": silver["silver_high_confidence"], "unit": "count", "sample_size": total},
    ]
    payload = {
        "schema_version": "3.0.0-automated.1",
        "export_id": "AAE-" + sha256_bytes(json.dumps(metrics, sort_keys=True).encode("utf-8"))[:16],
        "claim_label": "automated source-grounded triangulation",
        "split": "development",
        "case_counts": {**counts, "total": total},
        "metrics": metrics,
        "private_content_excluded": {
            "passage_text": True, "evidence_spans": True, "pdfs": True,
            "raw_annotations": True, "expert_identities": True,
        },
        "human_experts_participated": False,
        "expert_holdout_state": "expert_holdout_unopened",
        "source_manifest_sha256": sha256_bytes(manifest_path.read_bytes()),
    }
    auto.validate_schema(payload, "aggregate-export.schema.json")
    output = PUBLIC / "results" / "development-partial.json"
    write_json(output, payload)
    print(json.dumps({"output": str(output.relative_to(ROOT)), "completed_roles": completed_roles, "expected_roles": expected_roles}, indent=2))
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "verify", "annotation-status", "finalize-variants", "export-partial-status"))
    parser.add_argument("--passage-id")
    args = parser.parse_args()
    if args.command == "prepare":
        records = prepare_private_packets()
        baseline = record_expert_holdout()
        print(json.dumps({"private_packets": len(records), "expert_holdout_files": len(baseline["files"])}, indent=2))
    elif args.command == "verify":
        verify()
    elif args.command == "annotation-status":
        annotation_status()
    elif args.command == "finalize-variants":
        if not args.passage_id:
            parser.error("finalize-variants requires --passage-id")
        finalize_variants(args.passage_id)
    else:
        export_partial_status()


if __name__ == "__main__":
    main()
