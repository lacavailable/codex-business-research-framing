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


ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / "research-private" / "evaluator-calibration"
PUBLIC = ROOT / "evals" / "automated-triangulation"
LEGACY = ROOT / "evals" / "calibration"

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
        path.relative_to(ROOT).as_posix(): sha256_bytes(path.read_bytes())
        for path in legacy_holdout_files()
    }
    record = {
        "schema_version": "1.0.0",
        "baseline_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
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
        path = ROOT / relative
        if not path.is_file() or sha256_bytes(path.read_bytes()) != expected:
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "verify"))
    args = parser.parse_args()
    if args.command == "prepare":
        records = prepare_private_packets()
        baseline = record_expert_holdout()
        print(json.dumps({"private_packets": len(records), "expert_holdout_files": len(baseline["files"])}, indent=2))
    else:
        verify()


if __name__ == "__main__":
    main()
