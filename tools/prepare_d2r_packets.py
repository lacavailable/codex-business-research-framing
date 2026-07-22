#!/usr/bin/env python3
"""Prepare private, source-grounded D2R packets without opening either holdout."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from lean_adjudication_repair import (
    D2R_CASES,
    ROOT,
    assert_no_prestige_cues,
    blind_production_packet,
    derive_applicability,
    sha256_value,
    validate_schema,
    validate_and_repair_packet,
)


PRIVATE = ROOT / "research-private" / "evaluator-calibration"
OUTPUT = PRIVATE / "lean-v2" / "D2R"
PUBLIC = ROOT / "evals" / "automated-triangulation" / "lean-v2"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temp.replace(path)


def source_packet(case_id: str) -> Path:
    d2 = PRIVATE / "lean-v1" / "D2" / "task-packets" / case_id / "context-packet.json"
    if d2.exists():
        return d2
    d1 = PRIVATE / "lean-v1" / "D1" / "task-packets" / case_id / "context-packet.json"
    if d1.exists():
        return d1
    return PRIVATE / "judge-packets" / "automated" / case_id / "context-packet.json"


def contrast_root(case_id: str) -> Path:
    d2 = PRIVATE / "lean-v1" / "D2" / "contrast-batches" / case_id
    if d2.exists():
        return d2
    return PRIVATE / "lean-v1" / "D1" / "contrast-batches" / case_id


def forbidden_values(packet: dict[str, Any]) -> list[str]:
    values = []
    for key in ("source_id", "source_cluster_id", "article_title", "title", "journal", "outlet", "doi"):
        value = packet.get(key)
        if isinstance(value, str):
            values.append(value)
    return values


def prepare_case(case_id: str) -> dict[str, Any]:
    original = read_json(source_packet(case_id))
    repaired, repair_audit = validate_and_repair_packet(original)
    repair_audit["case_id"] = case_id
    repaired["attempted_layers"] = []
    repaired["required_layers"] = ["structure_fidelity"]
    repaired["response_profile"] = "full_audit"
    applicability = derive_applicability(repaired)
    applicability_ref = "LAP-" + hashlib.sha256(f"{case_id}:applicability".encode()).hexdigest()[:16]
    forbidden = forbidden_values(original)
    blinded = blind_production_packet(repaired, forbidden)
    evidence_spans = [
        {"span_id": span["span_id"], "text": span["text"]}
        for span in blinded["evidence_spans"]
    ]
    supports: dict[str, list[str]] = {}
    for span in repaired["evidence_spans"]:
        for path in span.get("supports", []):
            supports.setdefault(path, []).append(span["span_id"])
    production = {
        "schema_version": "3.1.0-lean.2",
        "opaque_case_id": "D2R-" + hashlib.sha256(case_id.encode()).hexdigest()[:16],
        "domain": repaired["domain"],
        "passage_function": repaired["passage_function"],
        "requested_task": repaired["requested_task"],
        "attempted_layers": repaired["attempted_layers"],
        "response_profile": repaired["response_profile"],
        "anonymized_context": blinded["context"],
        "passage": "\n\n".join(span["text"] for span in evidence_spans),
        "evidence_spans": evidence_spans,
        "supports": supports,
        "applicability_ref": applicability_ref,
        "source_content_sha256": repaired["passage_sha256"],
        "packet_sha256": "0" * 64,
        "prestige_cues_absent": True,
    }
    production["packet_sha256"] = sha256_value({key: value for key, value in production.items() if key != "packet_sha256"})
    assert_no_prestige_cues(production, forbidden)
    validate_schema(production, "production-packet.schema.json")

    source_dir = contrast_root(case_id)
    batch = read_json(source_dir / "batch.json")
    construction = read_json(source_dir / "construction.json")
    identity_by_item = {item["item_id"]: item["identity"] for item in construction["items"]}
    production_items = [
        item for item in batch["items"] if identity_by_item.get(item["item_id"]) != "prestige_label"
    ]
    prestige_items = [
        item for item in batch["items"] if identity_by_item.get(item["item_id"]) == "prestige_label"
    ]
    if len(production_items) != 4 or len(prestige_items) != 1:
        raise ValueError(f"{case_id}: expected four production items and one prestige diagnostic")
    production_batch = {
        "schema_version": "3.1.0-lean.2",
        "batch_id": "D2RB-" + hashlib.sha256(case_id.encode()).hexdigest()[:16],
        "case_id": production["opaque_case_id"],
        "items": production_items,
        "prestige_cues_removed": True,
    }
    # Contrast passages are synthetic, but remove any source metadata fields recursively.
    production_batch = blind_production_packet(production_batch, forbidden)
    assert_no_prestige_cues(production_batch, forbidden)
    diagnostic = {
        "schema_version": "3.1.0-lean.2",
        "case_id": case_id,
        "arm": "prestige_diagnostic_only",
        "items": prestige_items,
        "excluded_from_production": True,
        "source_construction_hash": sha256_value(construction),
    }

    case_dir = OUTPUT / "task-packets" / case_id
    write_json(case_dir / "original-preserved.json", original)
    write_json(case_dir / "repair-audit.json", repair_audit)
    write_json(case_dir / "applicability-plan.json", {
        "schema_version": "3.1.0-lean.2",
        "applicability_ref": applicability_ref,
        "case_id": case_id,
        "precedence": ["explicit_task_requirement", "explicitly_attempted_layer", "passage_function", "supplied_context", "response_profile"],
        "predetermined": applicability,
    })
    write_json(case_dir / "production-packet.json", production)
    write_json(OUTPUT / "contrast-batches" / case_id / "production-batch.json", production_batch)
    write_json(OUTPUT / "prestige-diagnostics" / case_id / "diagnostic-arm.json", diagnostic)
    return {
        "case_id": case_id,
        "original_hash": sha256_value(original),
        "repaired_hash": repair_audit["repaired_sha256"],
        "production_packet_hash": sha256_value(production),
        "production_batch_hash": sha256_value(production_batch),
        "prestige_diagnostic_hash": sha256_value(diagnostic),
        "prestige_cues_removed": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare", action="store_true", help="write ignored private D2R packets")
    parser.add_argument("--write-public-hashes", action="store_true", help="write sanitized tracked packet hashes")
    args = parser.parse_args()
    if not args.prepare:
        parser.error("--prepare is required")
    summaries = [prepare_case(case_id) for case_id in D2R_CASES]
    private_manifest = {
        "schema_version": "3.1.0-lean.2",
        "stage": "D2R",
        "cases": summaries,
        "expert_holdout_unopened": True,
        "automated_holdout_unopened": True,
    }
    write_json(OUTPUT / "packet-manifest.json", private_manifest)
    if args.write_public_hashes:
        write_json(PUBLIC / "packet-hashes.json", {
            "schema_version": "3.1.0-lean.2",
            "stage": "D2R",
            "private_content_included": False,
            "cases": [
                {
                    "case_id": item["case_id"],
                    "production_packet_sha256": item["production_packet_hash"],
                    "production_batch_sha256": item["production_batch_hash"],
                    "prestige_diagnostic_sha256": item["prestige_diagnostic_hash"],
                }
                for item in summaries
            ],
            "expert_holdout_unopened": True,
            "automated_holdout_unopened": True,
        })
    print(json.dumps({"prepared": len(summaries), "output": str(OUTPUT)}, indent=2))


if __name__ == "__main__":
    main()
