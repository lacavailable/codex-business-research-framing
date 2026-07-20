#!/usr/bin/env python3
"""Initialize and validate the ignored private evaluator-calibration workspace."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / "research-private" / "evaluator-calibration"
SUBDIRS = (
    "source-passages",
    "model-context",
    "expert-annotations",
    "contrast-variants",
    "judge-packets",
    "results",
)


class PrivateCalibrationError(ValueError):
    pass


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def initialize() -> dict[str, Any]:
    for name in SUBDIRS:
        (PRIVATE / name).mkdir(parents=True, exist_ok=True)
    marker = PRIVATE / "PRIVATE-NOT-FOR-COMMIT.txt"
    if not marker.exists():
        marker.write_text(
            "This directory may contain copyrighted passages and reviewer information.\n"
            "It is ignored by Git. Never copy raw passage text or identifying reviewer data into tracked files.\n",
            encoding="utf-8",
            newline="\n",
        )
    return {"private_root": str(PRIVATE), "subdirectories": list(SUBDIRS)}


def ingest(source_id: str, input_path: Path, metadata_path: Path) -> dict[str, Any]:
    if not input_path.is_file() or not metadata_path.is_file():
        raise PrivateCalibrationError("input passage and metadata files are required")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    required = {
        "full_citation", "journal", "year", "domain", "control_group", "article_type", "passage_function",
        "access_status", "copyright_status", "recognizability_risk", "contamination_risk",
    }
    missing = sorted(required - set(metadata))
    if missing:
        raise PrivateCalibrationError("metadata missing: " + ", ".join(missing))
    target = PRIVATE / "source-passages" / f"{source_id}.txt"
    if target.exists():
        raise PrivateCalibrationError(f"source already exists: {source_id}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(input_path, target)
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    record = {
        "schema_version": "3.0.0",
        "source_id": source_id,
        **metadata,
        "source_sha256": digest,
        "expert_review_status": "pending",
        "minimally_anonymized_path": None,
        "paraphrased_path": None,
        "semantic_equivalence_verified": False,
    }
    write_json(PRIVATE / "model-context" / f"{source_id}.json", record)
    return {"source_id": source_id, "source_sha256": digest, "status": "ingested_private"}


def verify() -> dict[str, Any]:
    initialize()
    contexts = sorted((PRIVATE / "model-context").glob("*.json"))
    if len(contexts) > 36:
        raise PrivateCalibrationError("candidate limit exceeded: at most 36 sources may be screened")
    reviewers_by_domain: dict[str, set[str]] = {key: set() for key in ("OM", "IS", "OR", "MGMT")}
    accepted_by_domain_group = {
        domain: {"positive": 0, "intermediate": 0}
        for domain in reviewers_by_domain
    }
    accepted = 0
    errors: list[str] = []
    for context_path in contexts:
        record = json.loads(context_path.read_text(encoding="utf-8"))
        source_id = record.get("source_id")
        passage = PRIVATE / "source-passages" / f"{source_id}.txt"
        if not passage.is_file():
            errors.append(f"{source_id}: source passage missing")
            continue
        digest = hashlib.sha256(passage.read_bytes()).hexdigest()
        if digest != record.get("source_sha256"):
            errors.append(f"{source_id}: source hash mismatch")
        annotations = sorted((PRIVATE / "expert-annotations").glob(f"{source_id}.*.json"))
        confirmed_reviewers: set[str] = set()
        for path in annotations:
            annotation = json.loads(path.read_text(encoding="utf-8"))
            reviewer = annotation.get("reviewer_id")
            domain = annotation.get("domain")
            if reviewer and domain in reviewers_by_domain:
                confirmed_reviewers.add(reviewer)
                reviewers_by_domain[domain].add(reviewer)
        domain = record.get("domain")
        group = record.get("control_group")
        if domain not in reviewers_by_domain or group not in {"positive", "intermediate"}:
            errors.append(f"{source_id}: invalid domain or control group")
        elif len(confirmed_reviewers) >= 2 and record.get("semantic_equivalence_verified") is True:
            accepted += 1
            accepted_by_domain_group[domain][group] += 1
    if errors:
        raise PrivateCalibrationError("; ".join(errors))
    return {
        "sources": len(contexts),
        "accepted_passages": accepted,
        "accepted_by_domain_group": accepted_by_domain_group,
        "reviewers_by_domain": {key: len(value) for key, value in reviewers_by_domain.items()},
        "release_ready": (
            accepted == 24
            and all(counts == {"positive": 3, "intermediate": 3} for counts in accepted_by_domain_group.values())
            and all(len(value) >= 2 for value in reviewers_by_domain.values())
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init")
    add = sub.add_parser("ingest")
    add.add_argument("--source-id", required=True)
    add.add_argument("--input", type=Path, required=True)
    add.add_argument("--metadata", type=Path, required=True)
    sub.add_parser("verify")
    args = parser.parse_args()
    try:
        if args.command == "init":
            result = initialize()
        elif args.command == "ingest":
            initialize()
            result = ingest(args.source_id, args.input.resolve(), args.metadata.resolve())
        else:
            result = verify()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, UnicodeError, json.JSONDecodeError, PrivateCalibrationError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
