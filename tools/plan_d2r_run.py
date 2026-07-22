#!/usr/bin/env python3
"""Build and validate the immutable-budget D2R call manifest."""

from __future__ import annotations

import hashlib
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPAIR = ROOT / "evals" / "automated-triangulation" / "lean-v2"
CASES = ("OM-P02", "MGMT-P02", "IS-P02", "OR-P01", "IS-P01")
REQUIRED_ROLES = ("role_a", "role_b", "role_c", "contrast_judge")
MODEL_ASSIGNMENTS = {
    "role_a": ("gpt-5.6-sol", "high"),
    "role_b": ("gpt-5.6-terra", "high"),
    "role_c": ("gpt-5.6-sol", "high"),
    "contrast_judge": ("gpt-5.6-terra", "high"),
    "adjudicator": ("gpt-5.6-sol", "xhigh"),
}


class RunPlanError(ValueError):
    pass


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_manifest(created_at: str = "2026-07-22T00:00:00Z") -> dict[str, Any]:
    prompts = json.loads((REPAIR / "prompts" / "roles-d2r.json").read_text(encoding="utf-8"))
    packet_hashes_path = REPAIR / "packet-hashes.json"
    packet_hashes = {}
    if packet_hashes_path.exists():
        packet_hashes = {
            item["case_id"]: item["production_packet_sha256"]
            for item in json.loads(packet_hashes_path.read_text(encoding="utf-8"))["cases"]
        }
    calls = []
    for case_id in CASES:
        for role in REQUIRED_ROLES:
            model, effort = MODEL_ASSIGNMENTS[role]
            calls.append(_call(case_id, role, "required", prompts, model, effort, packet_hashes.get(case_id)))
        model, effort = MODEL_ASSIGNMENTS["adjudicator"]
        call = _call(case_id, "adjudicator", "conditional", prompts, model, effort, packet_hashes.get(case_id))
        call["status"] = "not_required"
        calls.append(call)
    return {
        "schema_version": "3.1.0-lean.2",
        "run_id": "LRUN2-" + canonical_hash([CASES, created_at])[:16],
        "stage": "D2R",
        "split": "development",
        "case_set": list(CASES),
        "control_cases": ["OR-P01", "IS-P01"],
        "required_call_cap": 20,
        "conditional_adjudication_cap": 5,
        "maximum_calls": 25,
        "calls_used": 0,
        "attempts_used": 0,
        "status": "planned",
        "holdout_states": {"expert_holdout_unopened": True, "automated_holdout_unopened": True},
        "created_at": created_at,
        "updated_at": created_at,
        "calls": calls,
    }


def _call(case_id: str, role: str, kind: str, prompts: dict[str, Any], model: str, effort: str, packet_sha256: str | None) -> dict[str, Any]:
    call_id = "LCALL2-" + canonical_hash([case_id, role])[:16]
    return {
        "call_id": call_id,
        "call_kind": kind,
        "case_id": case_id,
        "role": role,
        "prompt_hash": canonical_hash(prompts[role]),
        "provider": "OpenAI",
        "model_id": model,
        "family_claim": "same_family",
        "settings": {"reasoning_effort": effort, "sampling_controls": "unavailable"},
        "status": "planned",
        "attempts": 0,
        "packet_sha256": packet_sha256,
        "output_ref": None,
        "output_sha256": None,
        "schema_valid": None,
        "started_at": None,
        "completed_at": None,
    }


def validate_manifest(manifest: dict[str, Any]) -> None:
    import jsonschema

    schema = json.loads((REPAIR / "schemas" / "run-manifest.schema.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(manifest)
    if manifest["required_call_cap"] != 20 or manifest["conditional_adjudication_cap"] != 5 or manifest["maximum_calls"] != 25:
        raise RunPlanError("D2R budgets are immutable")
    if manifest["calls_used"] != sum(call["attempts"] for call in manifest["calls"]):
        raise RunPlanError("retries and invalid attempts must count toward the total cap")
    if manifest["attempts_used"] != manifest["calls_used"]:
        raise RunPlanError("attempt and call accounting diverged")
    if manifest["calls_used"] > manifest["maximum_calls"]:
        raise RunPlanError("D2R call budget exceeded")
    if tuple(dict.fromkeys(call["case_id"] for call in manifest["calls"])) != CASES:
        raise RunPlanError("D2R case selection drift")
    for case_id in CASES:
        records = [call for call in manifest["calls"] if call["case_id"] == case_id]
        roles = [call["role"] for call in records]
        if roles != [*REQUIRED_ROLES, "adjudicator"]:
            raise RunPlanError(f"{case_id}: role plan/order drift")


def activate_adjudication(manifest: dict[str, Any], case_id: str, semantic_topics: list[str]) -> dict[str, Any]:
    allowed = {"material_semantic_disagreement", "applicability_boundary_disagreement"}
    if not semantic_topics or not set(semantic_topics) <= allowed:
        raise RunPlanError("only unresolved material semantic topics may activate adjudication")
    call = next(item for item in manifest["calls"] if item["case_id"] == case_id and item["role"] == "adjudicator")
    if call["status"] != "not_required":
        raise RunPlanError("adjudication slot is already active")
    call["status"] = "needs_adjudication"
    return call


def start_call(manifest: dict[str, Any], call_id: str) -> dict[str, Any]:
    call = next((item for item in manifest["calls"] if item["call_id"] == call_id), None)
    if call is None:
        raise RunPlanError(f"unknown call: {call_id}")
    if call["call_kind"] == "conditional" and call["status"] != "needs_adjudication":
        raise RunPlanError("conditional adjudication is not activated")
    if call["status"] not in {"planned", "schema_invalid", "paused_resource_limit", "needs_adjudication"}:
        raise RunPlanError(f"cannot start call from {call['status']}")
    if manifest["calls_used"] >= manifest["maximum_calls"]:
        raise RunPlanError("D2R call budget exhausted")
    if call["role"] == "role_c":
        prerequisites = [
            item for item in manifest["calls"]
            if item["case_id"] == call["case_id"] and item["role"] in {"role_a", "role_b"}
        ]
        if len(prerequisites) != 2 or any(item["status"] != "completed" for item in prerequisites):
            raise RunPlanError("Role C may start only after sealed Role A and Role B records")
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    call["attempts"] += 1
    call["status"] = "running"
    call["started_at"] = now
    call["completed_at"] = None
    manifest["calls_used"] = sum(item["attempts"] for item in manifest["calls"])
    manifest["attempts_used"] = manifest["calls_used"]
    manifest["status"] = "running"
    manifest["updated_at"] = now
    return call


def pause(manifest: dict[str, Any]) -> None:
    manifest["status"] = "paused_resource_limit"
    for call in manifest["calls"]:
        if call["status"] == "running":
            call["status"] = "paused_resource_limit"


def complete_call(manifest: dict[str, Any], call_id: str, output: Path) -> dict[str, Any]:
    import jsonschema

    call = next((item for item in manifest["calls"] if item["call_id"] == call_id), None)
    if call is None or call["status"] != "running":
        raise RunPlanError("call must be running before completion")
    private_root = (ROOT / "research-private" / "evaluator-calibration").resolve()
    resolved = output.resolve()
    if private_root not in resolved.parents:
        raise RunPlanError("authoritative D2R output must remain in ignored private storage")
    record = json.loads(resolved.read_text(encoding="utf-8"))
    try:
        if call["role"] in {"role_a", "role_b", "role_c"}:
            schema_name = call["role"].replace("_", "-") + ".schema.json"
            schema_path = ROOT / "evals" / "automated-triangulation" / "lean-v1" / "schemas" / schema_name
        elif call["role"] == "contrast_judge":
            schema_path = REPAIR / "schemas" / "contrast-output.schema.json"
        else:
            schema_path = REPAIR / "schemas" / "repair-adjudication.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(record)
        if call["role"] in {"role_a", "role_b", "role_c"}:
            import importlib.util
            spec = importlib.util.spec_from_file_location("sealed_lean_validators", ROOT / "tools" / "lean_triangulation.py")
            if spec is None or spec.loader is None:
                raise RunPlanError("sealed lean semantic validators unavailable")
            lean = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(lean)
            getattr(lean, f"validate_{call['role']}")(record)
        if record.get("case_id") != call["case_id"]:
            raise RunPlanError("output case does not match call")
        if record.get("prompt_hash") not in {None, call["prompt_hash"]}:
            raise RunPlanError("output prompt hash does not match call")
    except Exception:
        call["status"] = "schema_invalid"
        call["schema_valid"] = False
        call["completed_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        manifest["updated_at"] = call["completed_at"]
        raise
    call["status"] = "completed"
    call["schema_valid"] = True
    call["output_ref"] = f"private-record:{call_id}"
    call["output_sha256"] = hashlib.sha256(resolved.read_bytes()).hexdigest()
    call["completed_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    active = [item for item in manifest["calls"] if item["call_kind"] == "required" or item["status"] != "not_required"]
    manifest["status"] = "complete" if all(item["status"] == "completed" for item in active) else "running"
    manifest["updated_at"] = call["completed_at"]
    return call


def revalidate_call(manifest: dict[str, Any], call_id: str, output: Path) -> dict[str, Any]:
    call = next((item for item in manifest["calls"] if item["call_id"] == call_id), None)
    if call is None or call["status"] != "completed":
        raise RunPlanError("only a completed call may be revalidated")
    call["status"] = "running"
    try:
        return complete_call(manifest, call_id, output)
    except Exception:
        # Revalidation does not spend another attempt; the next fresh retry does.
        call["status"] = "schema_invalid"
        call["schema_valid"] = False
        raise


def invalidate_dependency(manifest: dict[str, Any], call_id: str) -> dict[str, Any]:
    call = next((item for item in manifest["calls"] if item["call_id"] == call_id), None)
    if call is None or call["status"] != "completed":
        raise RunPlanError("only a completed dependent call may be invalidated")
    call["status"] = "schema_invalid"
    call["schema_valid"] = False
    manifest["status"] = "running"
    manifest["updated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return call


def atomic_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("create", "verify", "start", "complete", "revalidate", "invalidate-dependency", "activate-adjudication", "pause", "remaining"))
    parser.add_argument("--manifest", type=Path, default=REPAIR / "runs" / "D2R.manifest.json")
    parser.add_argument("--call-id")
    parser.add_argument("--case-id")
    parser.add_argument("--topics", nargs="*")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    path = args.manifest if args.manifest.is_absolute() else ROOT / args.manifest
    if args.command == "create":
        manifest = build_manifest(datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
        validate_manifest(manifest)
        atomic_write(path, manifest)
    else:
        manifest = json.loads(path.read_text(encoding="utf-8"))
        if args.command == "start":
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
        elif args.command == "revalidate":
            if not args.call_id or not args.output:
                parser.error("revalidate requires --call-id and --output")
            try:
                revalidate_call(manifest, args.call_id, args.output if args.output.is_absolute() else ROOT / args.output)
            finally:
                atomic_write(path, manifest)
        elif args.command == "invalidate-dependency":
            if not args.call_id:
                parser.error("invalidate-dependency requires --call-id")
            invalidate_dependency(manifest, args.call_id)
            atomic_write(path, manifest)
        elif args.command == "activate-adjudication":
            if not args.case_id:
                parser.error("activate-adjudication requires --case-id")
            activate_adjudication(manifest, args.case_id, args.topics or [])
            atomic_write(path, manifest)
        elif args.command == "pause":
            pause(manifest)
            atomic_write(path, manifest)
        elif args.command == "remaining":
            print(json.dumps({"calls_used": manifest["calls_used"], "remaining": [item for item in manifest["calls"] if item["status"] not in {"completed", "not_required"}]}, indent=2))
            return
        validate_manifest(manifest)
    print(json.dumps({"manifest": str(path), "status": manifest["status"], "calls_used": manifest["calls_used"]}, indent=2))


if __name__ == "__main__":
    main()
