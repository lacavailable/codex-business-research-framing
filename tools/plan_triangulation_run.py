#!/usr/bin/env python3
"""Create and update deterministic, resumable lean triangulation run manifests."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LEAN = ROOT / "evals" / "automated-triangulation" / "lean-v1"
ANCHORS = ROOT / "evals" / "automated-triangulation" / "top-journal-private-manifests" / "private-anchor-manifest.json"
PROMPTS = LEAN / "prompts" / "roles.json"
SCHEMA_VERSION = "3.1.0-lean.1"
STAGE_LIMITS = {"D0": 0, "D1": 16, "D2": 40, "validation": 40}
SENTINELS = ("OM-P01", "IS-P01", "OR-P01", "MGMT-P01")


class RunPlanError(ValueError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_hash(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def stage_cases(stage: str) -> list[str]:
    records = read_json(ANCHORS)["records"]
    if stage == "D0":
        return []
    if stage == "D1":
        return list(SENTINELS)
    split = "development" if stage == "D2" else "validation"
    return sorted(item["passage_id"] for item in records if item["provisional_split"] == split)


def _call(case_id: str, role: str, prompt_hash: str, ordinal: int) -> dict[str, Any]:
    token = canonical_hash([case_id, role, ordinal, prompt_hash])[:16]
    return {
        "call_id": f"LCALL-{token}",
        "case_id": case_id,
        "role": role,
        "prompt_hash": prompt_hash,
        "model_id": "unassigned",
        "settings": {},
        "status": "planned",
        "attempts": 0,
        "output_path": None,
        "output_sha256": None,
        "schema_valid": None,
        "started_at": None,
        "completed_at": None,
    }


def build_manifest(stage: str, timestamp: str | None = None) -> dict[str, Any]:
    if stage not in STAGE_LIMITS:
        raise RunPlanError(f"unknown stage: {stage}")
    timestamp = timestamp or utc_now()
    prompt_data = read_json(PROMPTS)
    prompt_hashes = {name: canonical_hash(text) for name, text in prompt_data.items() if name in {"role_a", "role_b", "role_c", "contrast_judge", "adjudicator"}}
    calls: list[dict[str, Any]] = []
    cases = stage_cases(stage)
    for case_id in cases:
        for role in ("role_a", "role_b", "role_c", "contrast_judge"):
            calls.append(_call(case_id, role, prompt_hashes[role], len(calls)))
    if stage in {"D2", "validation"}:
        for case_id in cases:
            calls.append(_call(case_id, "adjudicator", prompt_hashes["adjudicator"], len(calls)))
    if len(calls) > STAGE_LIMITS[stage]:
        raise RunPlanError(f"{stage} plan exceeds {STAGE_LIMITS[stage]} calls")
    run_token = canonical_hash([stage, cases, prompt_hashes])[:16]
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": f"LRUN-{run_token}",
        "stage": stage,
        "split": "validation" if stage == "validation" else "development",
        "maximum_calls": STAGE_LIMITS[stage],
        "calls_used": 0,
        "status": "complete" if stage == "D0" else "planned",
        "holdouts_opened": False,
        "created_at": timestamp,
        "updated_at": timestamp,
        "calls": calls,
    }


def validate_manifest(manifest: dict[str, Any]) -> None:
    import jsonschema

    schema = read_json(LEAN / "schemas" / "run-manifest.schema.json")
    jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(manifest)
    if manifest["calls_used"] != sum(call["status"] in {"completed", "schema_invalid", "needs_adjudication"} for call in manifest["calls"]):
        raise RunPlanError("calls_used does not reconcile with recorded attempted calls")
    if manifest["calls_used"] > manifest["maximum_calls"]:
        raise RunPlanError("call budget exceeded")
    ids = [call["call_id"] for call in manifest["calls"]]
    if len(ids) != len(set(ids)):
        raise RunPlanError("duplicate call IDs")
    by_case: dict[str, dict[str, int]] = {}
    for index, call in enumerate(manifest["calls"]):
        by_case.setdefault(call["case_id"], {})[call["role"]] = index
    for case_id, roles in by_case.items():
        if "role_c" in roles and not (roles.get("role_a", 10**9) < roles["role_c"] and roles.get("role_b", 10**9) < roles["role_c"]):
            raise RunPlanError(f"{case_id}: Role C must follow Roles A and B")


def public_progress(manifest: dict[str, Any]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for call in manifest["calls"]:
        if call["status"] == "completed":
            counts[call["role"]] = counts.get(call["role"], 0) + 1
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": manifest["run_id"],
        "stage": manifest["stage"],
        "status": manifest["status"],
        "case_count": len({call["case_id"] for call in manifest["calls"]}),
        "calls_completed": sum(counts.values()),
        "calls_maximum": manifest["maximum_calls"],
        "role_counts": counts,
        "private_content_excluded": True,
        "expert_holdout_unopened": True,
        "automated_holdout_unopened": True,
        "updated_at": manifest["updated_at"],
    }


def pause(manifest: dict[str, Any]) -> dict[str, Any]:
    manifest["status"] = "paused_resource_limit"
    manifest["updated_at"] = utc_now()
    for call in manifest["calls"]:
        if call["status"] == "running":
            call["status"] = "paused_resource_limit"
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("create", "verify", "pause", "progress"))
    parser.add_argument("--stage", choices=tuple(STAGE_LIMITS))
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    default = LEAN / "runs" / f"{args.stage}.manifest.json" if args.stage else None
    path = args.manifest or default
    if path is None:
        parser.error("--stage or --manifest is required")
    path = path if path.is_absolute() else ROOT / path
    if args.command == "create":
        if not args.stage:
            parser.error("create requires --stage")
        manifest = build_manifest(args.stage)
        validate_manifest(manifest)
        atomic_write(path, manifest)
    else:
        manifest = read_json(path)
        if args.command == "pause":
            pause(manifest)
            atomic_write(path, manifest)
        validate_manifest(manifest)
    if args.command == "progress":
        progress = public_progress(manifest)
        output = args.output or LEAN / "results" / f"{manifest['stage']}-progress.json"
        output = output if output.is_absolute() else ROOT / output
        atomic_write(output, progress)
        print(json.dumps(progress, indent=2))
    else:
        print(json.dumps({"manifest": str(path.relative_to(ROOT)), "run_id": manifest["run_id"], "status": manifest["status"], "calls": len(manifest["calls"]), "maximum_calls": manifest["maximum_calls"]}, indent=2))


if __name__ == "__main__":
    main()
