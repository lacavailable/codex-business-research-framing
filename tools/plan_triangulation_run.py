#!/usr/bin/env python3
"""Create and update deterministic, resumable lean triangulation run manifests."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LEAN = ROOT / "evals" / "automated-triangulation" / "lean-v1"
ANCHORS = ROOT / "evals" / "automated-triangulation" / "top-journal-private-manifests" / "private-anchor-manifest.json"
PROMPTS = LEAN / "prompts" / "roles.json"
PROMPTS_D2 = LEAN / "prompts" / "roles-d2.json"
SCHEMA_VERSION = "3.1.0-lean.1"
STAGE_BUDGETS = {
    "D0": (0, 0),
    "D1": (16, 4),
    "D2": (32, 8),
    "validation": (32, 8),
}
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


ROLE_MODELS = {
    "role_a": ("gpt-5.6-sol", "high"),
    "role_b": ("gpt-5.6-terra", "high"),
    "role_c": ("gpt-5.6-sol", "high"),
    "contrast_judge": ("gpt-5.6-terra", "high"),
    "adjudicator": ("gpt-5.6-sol", "xhigh"),
}


def _call(case_id: str, role: str, prompt_hash: str, ordinal: int, call_kind: str = "required") -> dict[str, Any]:
    token = canonical_hash([case_id, role, ordinal, prompt_hash])[:16]
    model_id, effort = ROLE_MODELS[role]
    return {
        "call_id": f"LCALL-{token}",
        "call_kind": call_kind,
        "case_id": case_id,
        "role": role,
        "prompt_hash": prompt_hash,
        "provider": "OpenAI",
        "model_id": model_id,
        "family_claim": "same_family",
        "settings": {"reasoning_effort": effort, "sampling_controls": "not_exposed"},
        "status": "not_required" if call_kind == "conditional" else "planned",
        "attempts": 0,
        "output_path": None,
        "output_sha256": None,
        "schema_valid": None,
        "started_at": None,
        "completed_at": None,
    }


def build_manifest(stage: str, timestamp: str | None = None) -> dict[str, Any]:
    if stage not in STAGE_BUDGETS:
        raise RunPlanError(f"unknown stage: {stage}")
    timestamp = timestamp or utc_now()
    prompt_data = read_json(PROMPTS_D2 if stage in {"D2", "validation"} else PROMPTS)
    prompt_hashes = {name: canonical_hash(text) for name, text in prompt_data.items() if name in {"role_a", "role_b", "role_c", "contrast_judge", "adjudicator"}}
    calls: list[dict[str, Any]] = []
    cases = stage_cases(stage)
    for case_id in cases:
        for role in ("role_a", "role_b", "role_c", "contrast_judge"):
            calls.append(_call(case_id, role, prompt_hashes[role], len(calls)))
    if stage in {"D1", "D2", "validation"}:
        for case_id in cases:
            calls.append(_call(case_id, "adjudicator", prompt_hashes["adjudicator"], len(calls), "conditional"))
    required_cap, conditional_cap = STAGE_BUDGETS[stage]
    maximum = required_cap + conditional_cap
    if len(calls) > maximum:
        raise RunPlanError(f"{stage} plan exceeds {maximum} calls")
    run_token = canonical_hash([stage, cases, prompt_hashes])[:16]
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": f"LRUN-{run_token}",
        "stage": stage,
        "split": "validation" if stage == "validation" else "development",
        "required_call_cap": required_cap,
        "conditional_adjudication_cap": conditional_cap,
        "maximum_calls": maximum,
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
    if manifest["calls_used"] != sum(call["attempts"] for call in manifest["calls"]):
        raise RunPlanError("calls_used does not reconcile with recorded attempts")
    if manifest["calls_used"] > manifest["maximum_calls"]:
        raise RunPlanError("call budget exceeded")
    ids = [call["call_id"] for call in manifest["calls"]]
    if len(ids) != len(set(ids)):
        raise RunPlanError("duplicate call IDs")
    if manifest["maximum_calls"] != manifest["required_call_cap"] + manifest["conditional_adjudication_cap"]:
        raise RunPlanError("maximum_calls does not reconcile with required and conditional caps")
    required = [call for call in manifest["calls"] if call["call_kind"] == "required"]
    conditional = [call for call in manifest["calls"] if call["call_kind"] == "conditional"]
    if len(required) != manifest["required_call_cap"] or len(conditional) != manifest["conditional_adjudication_cap"]:
        raise RunPlanError("manifest call kinds do not reconcile with caps")
    prompt_data = read_json(PROMPTS_D2 if manifest["stage"] in {"D2", "validation"} else PROMPTS)
    expected_hashes = {name: canonical_hash(prompt_data[name]) for name in ROLE_MODELS}
    for call in manifest["calls"]:
        if call["prompt_hash"] != expected_hashes[call["role"]]:
            raise RunPlanError(f"{call['call_id']}: prompt hash drift")
        expected_model, expected_effort = ROLE_MODELS[call["role"]]
        if call["model_id"] != expected_model or call["settings"]["reasoning_effort"] != expected_effort:
            raise RunPlanError(f"{call['call_id']}: model/settings drift")
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


def find_call(manifest: dict[str, Any], call_id: str) -> dict[str, Any]:
    for call in manifest["calls"]:
        if call["call_id"] == call_id:
            return call
    raise RunPlanError(f"unknown call ID: {call_id}")


def start_call(manifest: dict[str, Any], call_id: str) -> dict[str, Any]:
    call = find_call(manifest, call_id)
    if call["call_kind"] == "conditional" and call["status"] != "needs_adjudication":
        raise RunPlanError(f"{call_id}: conditional adjudication is not activated")
    allowed = {"planned", "paused_resource_limit", "schema_invalid", "needs_adjudication"}
    if call["status"] not in allowed:
        raise RunPlanError(f"{call_id}: cannot start from {call['status']}")
    if manifest["calls_used"] >= manifest["maximum_calls"]:
        raise RunPlanError("call budget exhausted")
    call["attempts"] += 1
    call["status"] = "running"
    call["started_at"] = utc_now()
    call["completed_at"] = None
    call["schema_valid"] = None
    manifest["calls_used"] = sum(item["attempts"] for item in manifest["calls"])
    manifest["status"] = "running"
    manifest["updated_at"] = utc_now()
    return call


def activate_adjudication(manifest: dict[str, Any], case_id: str) -> dict[str, Any]:
    matches = [call for call in manifest["calls"] if call["case_id"] == case_id and call["role"] == "adjudicator"]
    if len(matches) != 1:
        raise RunPlanError(f"{case_id}: expected one adjudication slot")
    call = matches[0]
    if call["status"] != "not_required":
        raise RunPlanError(f"{case_id}: adjudication slot already {call['status']}")
    call["status"] = "needs_adjudication"
    manifest["updated_at"] = utc_now()
    return call


def rebase_prompt_hashes(manifest: dict[str, Any]) -> None:
    """Adopt the stage prompt version without erasing attempts or changing call IDs."""
    prompt_data = read_json(PROMPTS_D2 if manifest["stage"] in {"D2", "validation"} else PROMPTS)
    expected = {role: canonical_hash(prompt_data[role]) for role in ROLE_MODELS}
    for call in manifest["calls"]:
        if call["prompt_hash"] == expected[call["role"]]:
            continue
        if call["status"] == "completed":
            raise RunPlanError(f"{call['call_id']}: cannot rebase a completed call")
        call["prompt_hash"] = expected[call["role"]]
    manifest["updated_at"] = utc_now()


def complete_call(manifest: dict[str, Any], call_id: str, output: Path) -> dict[str, Any]:
    call = find_call(manifest, call_id)
    if call["status"] not in {"running", "schema_invalid", "completed"}:
        raise RunPlanError(f"{call_id}: must be running, schema_invalid, or completed before completion")
    was_completed = call["status"] == "completed"
    private_root = (ROOT / "research-private" / "evaluator-calibration").resolve()
    resolved = output.resolve()
    if private_root not in resolved.parents:
        raise RunPlanError("authoritative output must remain under ignored private calibration storage")
    record = read_json(resolved)
    try:
        spec = importlib.util.spec_from_file_location("lean_triangulation_checkpoint", ROOT / "tools" / "lean_triangulation.py")
        if spec is None or spec.loader is None:
            raise RunPlanError("could not load lean record validators")
        lean = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(lean)
        if call["role"] == "role_a":
            lean.validate_role_a(record)
        elif call["role"] == "role_b":
            lean.validate_role_b(record)
        elif call["role"] == "role_c":
            lean.validate_role_c(record)
        elif call["role"] == "contrast_judge":
            lean.validate_schema(record, "contrast-batch.schema.json")
        else:
            lean.validate_schema(record, "adjudication.schema.json")
        if record.get("case_id") != call["case_id"]:
            raise RunPlanError(f"{call_id}: output case ID mismatch")
    except Exception:
        call["status"] = "schema_invalid"
        call["schema_valid"] = False
        call["completed_at"] = utc_now()
        manifest["updated_at"] = utc_now()
        raise
    call["status"] = "completed"
    call["schema_valid"] = True
    call["output_path"] = f"private-record:{call_id}"
    call["output_sha256"] = hashlib.sha256(resolved.read_bytes()).hexdigest()
    if not was_completed:
        call["completed_at"] = utc_now()
    required = [item for item in manifest["calls"] if item["call_kind"] == "required"]
    activated = [item for item in manifest["calls"] if item["call_kind"] == "conditional" and item["status"] != "not_required"]
    manifest["status"] = "complete" if all(item["status"] == "completed" for item in required + activated) else "running"
    manifest["updated_at"] = utc_now()
    return call


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("create", "verify", "pause", "progress", "remaining", "start", "complete", "activate-adjudication", "rebase-prompts"))
    parser.add_argument("--stage", choices=tuple(STAGE_BUDGETS))
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--call-id")
    parser.add_argument("--case-id")
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
        elif args.command == "start":
            if not args.call_id:
                parser.error("start requires --call-id")
            start_call(manifest, args.call_id)
            atomic_write(path, manifest)
        elif args.command == "complete":
            if not args.call_id or not args.output:
                parser.error("complete requires --call-id and --output")
            try:
                complete_call(manifest, args.call_id, args.output if args.output.is_absolute() else ROOT / args.output)
            finally:
                atomic_write(path, manifest)
        elif args.command == "activate-adjudication":
            if not args.case_id:
                parser.error("activate-adjudication requires --case-id")
            activate_adjudication(manifest, args.case_id)
            atomic_write(path, manifest)
        elif args.command == "rebase-prompts":
            rebase_prompt_hashes(manifest)
            atomic_write(path, manifest)
        validate_manifest(manifest)
    if args.command == "progress":
        progress = public_progress(manifest)
        output = args.output or LEAN / "results" / f"{manifest['stage']}-progress.json"
        output = output if output.is_absolute() else ROOT / output
        atomic_write(output, progress)
        print(json.dumps(progress, indent=2))
    elif args.command == "remaining":
        required = [call for call in manifest["calls"] if call["call_kind"] == "required" and call["status"] != "completed"]
        conditional = [call for call in manifest["calls"] if call["call_kind"] == "conditional" and call["status"] not in {"completed", "not_required"}]
        print(json.dumps({
            "run_id": manifest["run_id"],
            "calls_used": manifest["calls_used"],
            "remaining_budget": manifest["maximum_calls"] - manifest["calls_used"],
            "required_remaining": [{"call_id": call["call_id"], "case_id": call["case_id"], "role": call["role"]} for call in required],
            "conditional_activated": [{"call_id": call["call_id"], "case_id": call["case_id"]} for call in conditional],
        }, indent=2))
    else:
        print(json.dumps({"manifest": str(path.relative_to(ROOT)), "run_id": manifest["run_id"], "status": manifest["status"], "calls": len(manifest["calls"]), "maximum_calls": manifest["maximum_calls"]}, indent=2))


if __name__ == "__main__":
    main()
