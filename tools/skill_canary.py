#!/usr/bin/env python3
"""Validate, freeze, blind, and summarize the bounded Skill 2.1 canary."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import statistics
from pathlib import Path
from typing import Any

import jsonschema


ROOT = Path(__file__).resolve().parents[1]
CANARY = ROOT / "evals" / "skill-2.1-canary"
SKILL = ROOT / "skills" / "frame-business-research-problem"
LOCAL = ROOT / ".local-eval" / "skill-2.1-canary"
TASKS = CANARY / "tasks" / "generator-visible.json"
AUDIT = CANARY / "tasks" / "audit-only.json"
PREREG = CANARY / "preregistration.json"
MANIFEST = CANARY / "runs" / "call-manifest.json"
GEN_DIR = CANARY / "outputs"
PAIR_DIR = CANARY / "blinded-pairs"
JUDGE_DIR = CANARY / "judgments"
RESULT = CANARY / "results" / "canary-result.json"
UAT_DIR = CANARY / "user-acceptance"
WORD = re.compile(r"\b[\w]+(?:[-'][\w]+)*\b", re.UNICODE)
HEADING = re.compile(r"(?m)^#{1,6}\s+")
NEGATION = re.compile(r"\b(?:not|no|cannot|can't|doesn't|does not|without|unsupported|unproven)\b", re.I)


class CanaryError(ValueError):
    pass


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def hash_value(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def hash_file(path: Path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def hash_tree(root: Path) -> str:
    digest = hashlib.sha256()
    files = [path for path in root.rglob("*") if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"]
    for path in sorted(files, key=lambda item: item.relative_to(root).as_posix().casefold()):
        digest.update(path.relative_to(root).as_posix().encode("utf-8") + b"\0")
        digest.update(bytes.fromhex(hash_file(path)))
    return digest.hexdigest()


def validate_schema(record: Any, name: str) -> None:
    schema = load(CANARY / "schemas" / name)
    jsonschema.Draft202012Validator(schema).validate(record)


def task_maps() -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    visible = {item["task_id"]: item for item in load(TASKS)["tasks"]}
    audit = {item["task_id"]: item for item in load(AUDIT)["tasks"]}
    if set(visible) != set(audit):
        raise CanaryError("generator and audit task IDs differ")
    return visible, audit


def validate_static() -> None:
    prereg = load(PREREG)
    visible, audit = task_maps()
    if len(visible) != 8:
        raise CanaryError("exactly eight tasks are required")
    domains = [item["domain"] for item in visible.values()]
    if {domain: domains.count(domain) for domain in set(domains)} != {"OM": 2, "IS": 2, "OR": 2, "cross-domain": 2}:
        raise CanaryError("tasks must contain two cases per domain")
    profiles = [item["profile"] for item in visible.values()]
    if profiles.count("compact") != 3 or profiles.count("standard") != 3 or profiles.count("full-audit") != 2:
        raise CanaryError("profiles must be allocated 3 compact, 3 standard, 2 full-audit")
    if any(set(item) != {"task_id", "domain", "profile", "request"} for item in visible.values()):
        raise CanaryError("generator-visible tasks contain hidden fields")
    if not all(item["required_invariants"] and "issue_patterns" in item for item in audit.values()):
        raise CanaryError("audit-only records are incomplete")
    calls = load(MANIFEST)["calls"]
    if len(calls) != 24 or len({item["call_id"] for item in calls}) != 24:
        raise CanaryError("manifest must contain exactly 24 unique calls")
    if sum(item["role"] == "generation" for item in calls) != 16:
        raise CanaryError("manifest must contain sixteen generation calls")
    if sum(item["role"] == "blind_pairwise_judge" for item in calls) != 8:
        raise CanaryError("manifest must contain eight judge calls")
    if prereg["maximum_authoritative_calls"] != 24:
        raise CanaryError("authoritative call cap drifted")


def write_freeze() -> dict[str, Any]:
    validate_static()
    record = {
        "schema_version": "skill-canary-freeze-1.0",
        "preregistration_sha256": hash_file(PREREG),
        "generator_tasks_sha256": hash_file(TASKS),
        "audit_tasks_sha256": hash_file(AUDIT),
        "call_manifest_sha256": hash_file(MANIFEST),
        "tool_sha256": hash_file(Path(__file__)),
        "candidate_skill_sha256": hash_tree(SKILL),
        "baseline_tag": load(PREREG)["baseline_skill_tag"],
        "automated_holdout_opened": False,
        "expert_holdout_opened": False
    }
    dump(CANARY / "freeze.json", record)
    return record


def validate_freeze() -> None:
    record = load(CANARY / "freeze.json")
    expected = {
        "preregistration_sha256": hash_file(PREREG),
        "generator_tasks_sha256": hash_file(TASKS),
        "audit_tasks_sha256": hash_file(AUDIT),
        "call_manifest_sha256": hash_file(MANIFEST),
        "tool_sha256": hash_file(Path(__file__)),
        "candidate_skill_sha256": hash_tree(SKILL),
    }
    for field, value in expected.items():
        if record.get(field) != value:
            raise CanaryError(f"freeze drift: {field}")
    if record.get("automated_holdout_opened") or record.get("expert_holdout_opened"):
        raise CanaryError("a holdout is marked opened")


def generation_prompt(task: dict[str, Any], skill_path: Path) -> str:
    return (
        f"Use the Codex Skill at {skill_path} to answer the request below. "
        "Read only that Skill and the references it directly routes for this task. "
        "Return only the user-facing Markdown answer; do not discuss this evaluation.\n\n"
        f"Requested profile: {task['profile']}\n\n{task['request']}"
    )


def word_count(text: str) -> int:
    return len(WORD.findall(text))


def section_count(text: str) -> int:
    return len(HEADING.findall(text))


def sentence_overclaim(text: str, kind: str) -> bool:
    sentences = re.split(r"(?<=[.!?])\s+|\n+", text)
    for sentence in sentences:
        lowered = sentence.casefold()
        if NEGATION.search(sentence):
            continue
        if kind == "runtime_to_profit":
            if ("runtime" in lowered or "faster" in lowered) and "profit" in lowered and re.search(r"\b(?:raise|increase|improve|therefore|so|translate|lead)\w*\b", lowered):
                return True
        elif kind == "equivalent_formulation_changes_optimum":
            if "equivalent" in lowered and ("optimum" in lowered or "objective" in lowered) and re.search(r"\b(?:change|raise|improve)\w*\b", lowered):
                return True
        elif kind == "post_deadline_value":
            if ("after" in lowered or "post-deadline" in lowered) and ("certificate" in lowered or "proof" in lowered) and re.search(r"\b(?:improve|benefit|value|change)\w*\b", lowered):
                return True
    return False


def repeated_issue_count(text: str, audit: dict[str, Any]) -> int:
    repeats = 0
    for patterns in audit["issue_patterns"].values():
        occurrences = sum(len(re.findall(pattern, text, flags=re.I)) for pattern in patterns)
        repeats += max(0, occurrences - 1)
    return repeats


def visible_nonapplicable_count(text: str, audit: dict[str, Any]) -> int:
    lowered = text.casefold()
    return sum(lowered.count(layer.casefold()) for layer in audit["nonapplicable_layers"])


def unsupported_number_count(text: str, audit: dict[str, Any]) -> int:
    allowed = set(audit["allowed_numbers"])
    supplied = set(re.findall(r"\d+(?:\.\d+)?", text))
    return len(supplied - allowed)


def profile_compliant(text: str, profile: str) -> bool:
    words = word_count(text)
    if profile == "compact":
        return 120 <= words <= 220 and section_count(text) <= 3
    if profile == "standard":
        return 250 <= words <= 500
    required = ("actor", "timing", "information", "behavior", "constraint", "objective", "evidence", "boundar", "eligib", "mapping")
    lowered = text.casefold()
    return all(token in lowered for token in required)


def output_metrics(record: dict[str, Any], audit: dict[str, Any]) -> dict[str, Any]:
    text = record["output"]
    prohibited = {kind: sentence_overclaim(text, kind) for kind in audit["prohibited_overclaims"]}
    return {
        "word_count": word_count(text),
        "section_count": section_count(text),
        "profile_compliant": profile_compliant(text, audit["profile"]),
        "repeated_issue_count": repeated_issue_count(text, audit),
        "visible_nonapplicable_layers": visible_nonapplicable_count(text, audit),
        "unsupported_numbers": unsupported_number_count(text, audit),
        "prohibited_overclaims": prohibited,
    }


def prepare_pairs() -> None:
    validate_freeze()
    visible, _ = task_maps()
    calls = load(MANIFEST)["calls"]
    generations = [item for item in calls if item["role"] == "generation"]
    records: dict[tuple[str, str], dict[str, Any]] = {}
    for call in generations:
        record = load(GEN_DIR / f"{call['call_id']}.json")
        validate_schema(record, "generation-result.schema.json")
        records[(call["task_id"], call["condition"])] = record
    seed = load(PREREG)["pair_seed"]
    uat_seed = load(PREREG)["uat_seed"]
    key: dict[str, Any] = {"schema_version": "skill-canary-pair-key-1.0", "pairs": []}
    uat_key: dict[str, Any] = {"schema_version": "skill-canary-uat-key-1.0", "pairs": []}
    for index, task_id in enumerate(visible, 1):
        baseline = records[(task_id, "v0.2")]["output"]
        candidate = records[(task_id, "skill-2.1")]["output"]
        swap = int(hashlib.sha256(f"{seed}:{task_id}".encode()).hexdigest(), 16) % 2 == 1
        output_a, output_b = (candidate, baseline) if swap else (baseline, candidate)
        pair = {
            "schema_version": "skill-canary-pair-1.0",
            "pair_id": f"PAIR-{index:02d}",
            "task_id": task_id,
            "request": visible[task_id]["request"],
            "output_a": output_a,
            "output_b": output_b,
        }
        pair["pair_sha256"] = hash_value(pair)
        validate_schema(pair, "blinded-pair.schema.json")
        dump(PAIR_DIR / f"PAIR-{index:02d}.json", pair)
        key["pairs"].append({"pair_id": pair["pair_id"], "task_id": task_id, "a": "skill-2.1" if swap else "v0.2", "b": "v0.2" if swap else "skill-2.1"})
        uat_swap = int(hashlib.sha256(f"{uat_seed}:{task_id}".encode()).hexdigest(), 16) % 2 == 1
        uat_a, uat_b = (candidate, baseline) if uat_swap else (baseline, candidate)
        packet = (
            f"# Product-owner review {index:02d}\n\n"
            f"**Task ID:** `{task_id}`\n\n"
            f"## Request\n\n{visible[task_id]['request']}\n\n"
            f"## Output A\n\n{uat_a}\n\n"
            f"## Output B\n\n{uat_b}\n"
        )
        packet_path = UAT_DIR / "pairs" / f"UAT-{index:02d}.md"
        packet_path.parent.mkdir(parents=True, exist_ok=True)
        packet_path.write_text(packet, encoding="utf-8", newline="\n")
        uat_key["pairs"].append({"packet_id": f"UAT-{index:02d}", "task_id": task_id, "a": "skill-2.1" if uat_swap else "v0.2", "b": "v0.2" if uat_swap else "skill-2.1"})
    dump(LOCAL / "pair-key.json", key)
    dump(LOCAL / "uat-key.json", uat_key)
    form = (
        "# Product-owner user acceptance review\n\n"
        "Review each numbered pair without inspecting repository condition keys or "
        "condition-specific results. Record a preference before requesting the key.\n\n"
        "| Pair | Preferred output (A/B/tie) | Easier to use | Less repetitive | "
        "Model meaning preserved | Suitable length | Serious error observed | Short note |\n"
        "|---|---|---|---|---|---|---|---|\n"
        + "".join(f"| UAT-{index:02d} |  |  |  |  |  |  |  |\n" for index in range(1, 9))
        + "\nThis is product-owner review, not expert review or formal validation.\n"
    )
    (UAT_DIR / "review-form.md").write_text(form, encoding="utf-8", newline="\n")


def reduction(baseline: float, candidate: float) -> float:
    if baseline == 0:
        return 0.0 if candidate > 0 else 1.0
    return (baseline - candidate) / baseline


def summarize() -> dict[str, Any]:
    validate_freeze()
    visible, audits = task_maps()
    key = {item["pair_id"]: item for item in load(LOCAL / "pair-key.json")["pairs"]}
    calls = load(MANIFEST)["calls"]
    metrics: dict[str, dict[str, Any]] = {}
    for call in [item for item in calls if item["role"] == "generation"]:
        record = load(GEN_DIR / f"{call['call_id']}.json")
        validate_schema(record, "generation-result.schema.json")
        metrics.setdefault(call["task_id"], {})[call["condition"]] = output_metrics(record, audits[call["task_id"]])
    judgments: list[dict[str, Any]] = []
    decoded: list[dict[str, Any]] = []
    for index in range(1, 9):
        pair_id = f"PAIR-{index:02d}"
        judgment = load(JUDGE_DIR / f"JUDGE-{index:02d}.json")
        validate_schema(judgment, "judge-result.schema.json")
        judgments.append(judgment)
        mapping = key[pair_id]
        preference = judgment["overall_preference"]
        winner = "tie" if preference == "tie" else mapping["a" if preference == "A better" else "b"]
        candidate_side = "a" if mapping["a"] == "skill-2.1" else "b"
        baseline_side = "b" if candidate_side == "a" else "a"
        decoded.append({
            "task_id": judgment["task_id"],
            "winner": winner,
            "candidate_material_fidelity_issue": judgment[f"material_fidelity_issue_in_{candidate_side}"],
            "baseline_material_fidelity_issue": judgment[f"material_fidelity_issue_in_{baseline_side}"],
        })
    compact = [task_id for task_id, task in visible.items() if task["profile"] == "compact"]
    compact_baseline = statistics.median(metrics[task]["v0.2"]["word_count"] for task in compact)
    compact_candidate = statistics.median(metrics[task]["skill-2.1"]["word_count"] for task in compact)
    baseline_repeats = sum(item["v0.2"]["repeated_issue_count"] for item in metrics.values())
    candidate_repeats = sum(item["skill-2.1"]["repeated_issue_count"] for item in metrics.values())
    baseline_layers = sum(item["v0.2"]["visible_nonapplicable_layers"] for item in metrics.values())
    candidate_layers = sum(item["skill-2.1"]["visible_nonapplicable_layers"] for item in metrics.values())
    profile_rate = sum(item["skill-2.1"]["profile_compliant"] for item in metrics.values()) / 8
    new_fidelity = sum(item["candidate_material_fidelity_issue"] and not item["baseline_material_fidelity_issue"] for item in decoded)
    unsupported = sum(item["skill-2.1"]["unsupported_numbers"] for item in metrics.values())
    runtime_claims = sum(item["skill-2.1"]["prohibited_overclaims"].get("runtime_to_profit", False) or item["skill-2.1"]["prohibited_overclaims"].get("equivalent_formulation_changes_optimum", False) for item in metrics.values())
    deadline_claims = sum(item["skill-2.1"]["prohibited_overclaims"].get("post_deadline_value", False) for item in metrics.values())
    compact_standard = {task_id for task_id, task in visible.items() if task["profile"] in {"compact", "standard"}}
    non_tied = [item for item in decoded if item["task_id"] in compact_standard and item["winner"] != "tie"]
    wins = sum(item["winner"] == "skill-2.1" for item in non_tied)
    win_rate = None if not non_tied else wins / len(non_tied)
    full_tasks = {task_id for task_id, task in visible.items() if task["profile"] == "full-audit"}
    full_noninferior = all(
        not item["candidate_material_fidelity_issue"] or item["baseline_material_fidelity_issue"]
        for item in decoded if item["task_id"] in full_tasks
    ) and all(metrics[task]["skill-2.1"]["profile_compliant"] for task in full_tasks)
    observed = {
        "new_fidelity_contradictions": new_fidelity,
        "new_unsupported_facts": unsupported,
        "runtime_to_profit_overclaims": runtime_claims,
        "post_deadline_value_overclaims": deadline_claims,
        "compact_baseline_median_words": compact_baseline,
        "compact_candidate_median_words": compact_candidate,
        "compact_median_reduction": reduction(compact_baseline, compact_candidate),
        "baseline_repeated_limitations": baseline_repeats,
        "candidate_repeated_limitations": candidate_repeats,
        "repeated_limitation_reduction": reduction(baseline_repeats, candidate_repeats),
        "profile_compliance": profile_rate,
        "baseline_visible_nonapplicable_layers": baseline_layers,
        "candidate_visible_nonapplicable_layers": candidate_layers,
        "visible_nonapplicable_layer_reduction": reduction(baseline_layers, candidate_layers),
        "compact_standard_non_tied": len(non_tied),
        "compact_standard_candidate_wins": wins,
        "compact_standard_non_tied_win_rate": win_rate,
        "full_audit_safeguards_noninferior": full_noninferior,
    }
    gates = {
        "new_fidelity_contradictions": new_fidelity == 0,
        "new_unsupported_facts": unsupported == 0,
        "runtime_to_profit_overclaims": runtime_claims == 0,
        "post_deadline_value_overclaims": deadline_claims == 0,
        "compact_median_reduction": observed["compact_median_reduction"] >= 0.30,
        "repeated_limitation_reduction": observed["repeated_limitation_reduction"] >= 0.40,
        "profile_compliance": profile_rate >= 0.90,
        "visible_nonapplicable_layer_reduction": observed["visible_nonapplicable_layer_reduction"] >= 0.75,
        "compact_standard_non_tied_win_rate": win_rate is not None and win_rate >= 0.60,
        "full_audit_safeguards_noninferior": full_noninferior,
    }
    result = {
        "schema_version": "skill-canary-result-1.0",
        "status": "pass" if all(gates.values()) else "fail",
        "experimental_merge_authorized": all(gates.values()),
        "validation_authorized": False,
        "release_authorized": False,
        "authoritative_calls_used": 24,
        "observed": observed,
        "gates": gates,
        "per_output_metrics": metrics,
        "decoded_pairwise_results": decoded,
        "automated_holdout_opened": False,
        "expert_holdout_opened": False,
        "no_human_experts": True,
    }
    dump(RESULT, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["validate", "freeze", "validate-freeze", "prepare-pairs", "summarize"])
    args = parser.parse_args()
    if args.command == "validate":
        validate_static()
    elif args.command == "freeze":
        write_freeze()
    elif args.command == "validate-freeze":
        validate_freeze()
    elif args.command == "prepare-pairs":
        prepare_pairs()
    else:
        summarize()
    print(f"Skill canary {args.command} passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
