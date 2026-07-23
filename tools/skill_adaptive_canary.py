#!/usr/bin/env python3
"""Prepare, freeze, blind, and summarize the bounded Skill 2.2 adaptive canary."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import jsonschema


ROOT = Path(__file__).resolve().parents[1]
CANARY = ROOT / "evals" / "skill-2.2-canary"
OLD = ROOT / "evals" / "skill-2.1-canary"
SKILL = ROOT / "skills" / "frame-business-research-problem"
LOCAL = ROOT / ".local-eval" / "skill-2.2-canary"
TASKS = CANARY / "tasks" / "generator-visible.json"
AUDIT = CANARY / "tasks" / "audit-only.json"
PREREG = CANARY / "preregistration.json"
METRICS = CANARY / "metric-definitions.json"
MANIFEST = CANARY / "runs" / "call-manifest.json"
BASELINES = CANARY / "baseline-manifest.json"
GEN_DIR = CANARY / "outputs"
PAIR_DIR = CANARY / "blinded-pairs"
JUDGE_DIR = CANARY / "judgments"
RESULT = CANARY / "results" / "canary-result.json"
UAT = CANARY / "user-acceptance"
WORD = re.compile(r"\b[\w]+(?:[-'][\w]+)*\b", re.UNICODE)
HEADING = re.compile(r"(?m)^#{1,6}\s+")
TABLE_ROW = re.compile(r"(?m)^\s*\|.+\|\s*$")
NEGATION = re.compile(r"\b(?:not|no|cannot|does not|without|unsupported|unproven)\b", re.I)
STRUCTURAL_NUMBER = re.compile(
    r"(?:BusinessBrief|DFC|schema|version|stage|step|section|profile|gate|row|rule)\s*[-:]?\s*\d",
    re.I,
)


class CanaryError(ValueError):
    pass


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def hash_file(path: Path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def hash_text(text: str) -> str:
    return hashlib.sha256(text.replace("\r\n", "\n").encode("utf-8")).hexdigest()


def hash_tree(root: Path) -> str:
    digest = hashlib.sha256()
    files = [
        path for path in root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    ]
    for path in sorted(files, key=lambda item: item.relative_to(root).as_posix().casefold()):
        digest.update(path.relative_to(root).as_posix().encode("utf-8") + b"\0")
        digest.update(bytes.fromhex(hash_file(path)))
    return digest.hexdigest()


def validate_schema(record: Any, schema_name: str) -> None:
    schema = load(CANARY / "schemas" / schema_name)
    jsonschema.Draft202012Validator(schema).validate(record)


def generation_prompt(task: dict[str, Any]) -> str:
    return (
        "You are performing one frozen Skill 2.2 adaptive product-development call. "
        "Do not edit files and do not discuss the evaluation. Read "
        "skills/frame-business-research-problem/SKILL.md and only the references it "
        "routes for this request. Follow the Skill exactly. Return only the final "
        "user-facing Markdown deliverable, with no preface or afterword.\n\n"
        f"Task ID: {task['task_id']}\n"
        f"Requested profile: {task['profile']}\n"
        f"Requested deliverable: {task['deliverable']}\n\n"
        f"{task['request']}\n"
    )


def judge_prompt(task: dict[str, Any], index: int) -> str:
    return (
        "You are the sole blinded pairwise judge for one frozen product-development "
        "comparison. Do not edit files. The condition identities are hidden. Assess "
        "only the request and Outputs A/B. Do not infer condition identity. If you "
        "genuinely cannot distinguish them, return a tie; uncertainty is a tie. "
        "Judge model fidelity, deliverable fit, usability, information organization, "
        "prose economy, substantive repetition, claim scope, and evidence boundaries. "
        "Necessary technical-term recurrence and table labels are not repetition. "
        "An unsupported factual claim means an unsupported empirical magnitude, "
        "prevalence, market/company fact, causal effect, literature fact, observed "
        "performance, or generalized benchmark claim—not schema/stage numbers, "
        "supplied times, or transparent arithmetic. Return exactly one JSON object "
        "matching schemas/judge-result.schema.json, with no Markdown fence.\n\n"
        f"Judge call: JUDGE-{index:02d}\n"
        f"Task ID: {task['task_id']}\n"
        f"Requested profile: {task['profile']}\n"
        f"Requested deliverable: {task['deliverable']}\n"
        f"Request: {task['request']}\n\n"
        "At call time, append the frozen blinded pair JSON verbatim. Do not change "
        "this rubric or add another judge.\n"
    )


def prepare() -> None:
    if any(GEN_DIR.glob("GEN-*.json")) or any(JUDGE_DIR.glob("JUDGE-*.json")):
        raise CanaryError("authoritative records already exist; prepare will not overwrite them")

    old_tasks = load(OLD / "tasks" / "generator-visible.json")["tasks"]
    deliverables = {
        "OM-C01": "manuscript-ready business-problem paragraph",
        "OM-S02": "diagnosis and replacement framing",
        "IS-C01": "manuscript-ready platform-governance paragraph",
        "IS-S02": "diagnosis, compact mapping, and replacement framing",
        "OR-C01": "computational-contribution paragraph",
        "OR-S02": "computational-contribution explanation",
        "XD-F01": "full fidelity and framing audit",
        "XD-F02": "full contribution-framing audit",
    }
    tasks = []
    for item in old_tasks:
        record = dict(item)
        record["deliverable"] = deliverables[item["task_id"]]
        tasks.append(record)
    dump(TASKS, {"schema_version": "skill-2.2-canary-tasks-1.0", "tasks": tasks})

    old_audit = {item["task_id"]: item for item in load(OLD / "tasks" / "audit-only.json")["tasks"]}
    audit = []
    for item in tasks:
        base = old_audit[item["task_id"]]
        audit.append({
            "task_id": item["task_id"],
            "profile": item["profile"],
            "deliverable": item["deliverable"],
            "required_invariants": base["required_invariants"],
            "task_supplied_numbers": base["allowed_numbers"],
            "prohibited_overclaims": base["prohibited_overclaims"],
            "full_audit": item["profile"] == "full-audit",
            "is_standard_mapping_task": item["task_id"] == "IS-S02",
            "is_or_standard_task": item["task_id"] == "OR-S02",
        })
    dump(AUDIT, {"schema_version": "skill-2.2-canary-audit-1.0", "tasks": audit})

    baseline_ids = ["01", "03", "05", "07", "09", "11", "13", "15"]
    skill21_full_ids = {"XD-F01": "14", "XD-F02": "16"}
    baseline_records = []
    for task, suffix in zip(tasks, baseline_ids):
        path = OLD / "outputs" / f"GEN-{suffix}.json"
        record = load(path)
        baseline_records.append({
            "task_id": task["task_id"],
            "condition": "v0.2",
            "path": path.relative_to(ROOT).as_posix(),
            "file_sha256": hash_file(path),
            "output_sha256": hash_text(record["output"]),
        })
    skill21_refs = []
    for task_id, suffix in skill21_full_ids.items():
        path = OLD / "outputs" / f"GEN-{suffix}.json"
        record = load(path)
        skill21_refs.append({
            "task_id": task_id,
            "condition": "skill-2.1-full-audit-reference",
            "path": path.relative_to(ROOT).as_posix(),
            "file_sha256": hash_file(path),
            "output_sha256": hash_text(record["output"]),
        })
    dump(BASELINES, {
        "schema_version": "skill-2.2-baselines-1.0",
        "baseline_commit": "c7a6e0245f682fc0f8609a69e546d7cb39f35e49",
        "baseline_tag": "v0.2.0-beta",
        "source_canary": "evals/skill-2.1-canary",
        "baseline_outputs": baseline_records,
        "skill_2_1_full_audit_references": skill21_refs,
    })

    calls = []
    for index, task in enumerate(tasks, 1):
        calls.append({
            "call_id": f"GEN-{index:02d}",
            "task_id": task["task_id"],
            "role": "generation",
            "condition": "skill-2.2-adaptive",
            "model": "gpt-5.6-terra",
            "reasoning": "high",
            "status": "planned",
        })
    for index, task in enumerate(tasks, 1):
        calls.append({
            "call_id": f"JUDGE-{index:02d}",
            "task_id": task["task_id"],
            "role": "blind_pairwise_judge",
            "condition": "blinded",
            "model": "gpt-5.6-sol",
            "reasoning": "high",
            "status": "planned",
        })
    dump(MANIFEST, {
        "schema_version": "skill-2.2-run-1.0",
        "maximum_authoritative_calls": 16,
        "baseline_generation_calls": 0,
        "replacement_calls_allowed": False,
        "adjudication_allowed": False,
        "additional_model_roles_allowed": False,
        "calls": calls,
    })

    acceptance = {
        "1_new_material_fidelity_contradictions": {"operator": "==", "threshold": 0},
        "2_new_unsupported_factual_claims": {"operator": "==", "threshold": 0},
        "3_runtime_to_profit_conversions": {"operator": "==", "threshold": 0},
        "4_post_deadline_same_cycle_value_claims": {"operator": "==", "threshold": 0},
        "5_scope_or_generalization_errors": {"operator": "==", "threshold": 0},
        "6_candidate_visible_nonapplicable_layers": {"operator": "==", "threshold": 0},
        "7_adaptive_contract_compliance": {"operator": ">=", "threshold": 7, "denominator": 8},
        "8_outputs_without_avoidable_repetition": {"operator": ">=", "threshold": 5, "denominator": 8},
        "9_non_full_audit_candidate_wins": {"operator": ">=", "threshold": 4, "denominator": 6},
        "10_full_audit_fidelity_or_safeguard_losses": {"operator": "==", "threshold": 0},
        "11_full_audit_simplification": {"operator": ">=", "threshold": 1, "denominator": 2},
        "12_or_standard_safeguards": {"operator": "==", "threshold": True},
        "13_is_standard_mapping_fit": {"operator": "==", "threshold": True},
        "14_deterministic_checks": {"operator": "==", "threshold": True},
    }
    dump(PREREG, {
        "schema_version": "skill-2.2-preregistration-1.0",
        "frozen_before_generation": True,
        "candidate_name": "Skill 2.2 adaptive experimental",
        "source_pr_7_commit": "323ea17b8f98059b71801b6a1bf9241188be4fee",
        "generator_model": "gpt-5.6-terra",
        "generator_reasoning": "high",
        "judge_model": "gpt-5.6-sol",
        "judge_reasoning": "high",
        "model_relationship": "same-family variants; independence not established",
        "required_candidate_generation_calls": 8,
        "required_blind_judge_calls": 8,
        "maximum_authoritative_calls": 16,
        "pair_seed": "skill-2.2-adaptive-pairs-2026-07-23",
        "uat_seed": "skill-2.2-adaptive-product-owner-2026-07-23",
        "acceptance_rules": acceptance,
        "scope": "public product-development iteration; not independent validation",
        "prohibited_actions": [
            "v0.2 regeneration",
            "retry or replacement call",
            "adjudication",
            "additional model role",
            "calibration evaluator modification or rerun",
            "validation or holdout access",
            "silver labels",
            "expert-validation or superiority claim",
            "tag or release",
        ],
    })
    dump(METRICS, {
        "schema_version": "skill-2.2-metrics-1.0",
        "profile_compliance": {
            "definition": "required content and deliverable fit from the blind judge, plus prohibited-scaffolding and soft-maximum checks; no minimum word count",
            "soft_maximums": {"micro": 120, "compact": 220, "standard": 500, "full-audit": None},
            "compact_prohibited_scaffolding": ["visible DFC-12", "full gate inventory", "BusinessBrief envelope"],
        },
        "unsupported_factual_claim": {
            "counted": [
                "empirical magnitude", "prevalence", "market fact", "company fact",
                "causal effect", "observed performance", "literature fact",
                "generalized benchmark claim",
            ],
            "excluded": [
                "schema version", "list number", "stage label", "supplied time",
                "task-supplied quantity", "transparent arithmetic",
            ],
        },
        "repetition": {
            "definition": "blind-judge finding that the same substantive limitation is avoidably restated or scaffolding can be deleted without changing meaning",
            "excluded": ["necessary technical nouns", "table labels", "requested schema fields"],
        },
        "structural_complexity": ["word_count", "heading_count", "table_count", "table_data_rows", "bullet_count"],
        "nonapplicable_layers": {"absolute_candidate_requirement": 0},
        "ties": "uncertainty or genuine indistinguishability; no second judge",
    })

    for index, task in enumerate(tasks, 1):
        path = CANARY / "prompts" / "generation" / f"GEN-{index:02d}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(generation_prompt(task), encoding="utf-8", newline="\n")
        path = CANARY / "prompts" / "judging" / f"JUDGE-{index:02d}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(judge_prompt(task, index), encoding="utf-8", newline="\n")

    validate_static()
    write_freeze()


def tracked_freeze_inputs() -> dict[str, str]:
    paths = [
        PREREG, METRICS, TASKS, AUDIT, MANIFEST, BASELINES, Path(__file__),
        CANARY / "schemas" / "generation-result.schema.json",
        CANARY / "schemas" / "blinded-pair.schema.json",
        CANARY / "schemas" / "judge-result.schema.json",
    ]
    paths.extend(sorted((CANARY / "prompts").rglob("*.md")))
    return {path.relative_to(ROOT).as_posix(): hash_file(path) for path in paths}


def write_freeze() -> None:
    record = {
        "schema_version": "skill-2.2-freeze-1.0",
        "candidate_skill_sha256": hash_tree(SKILL),
        "frozen_inputs_sha256": tracked_freeze_inputs(),
        "baseline_output_hashes": {
            item["task_id"]: item["output_sha256"]
            for item in load(BASELINES)["baseline_outputs"]
        },
        "task_hashes": {
            item["task_id"]: hash_text(item["request"])
            for item in load(TASKS)["tasks"]
        },
        "generation_prompt_hashes": {
            path.stem: hash_file(path)
            for path in sorted((CANARY / "prompts" / "generation").glob("GEN-*.md"))
        },
        "judge_prompt_hashes": {
            path.stem: hash_file(path)
            for path in sorted((CANARY / "prompts" / "judging").glob("JUDGE-*.md"))
        },
        "automated_holdout_opened": False,
        "expert_holdout_opened": False,
        "authoritative_calls_used_at_freeze": 0,
    }
    dump(CANARY / "freeze.json", record)


def validate_static() -> None:
    tasks = load(TASKS)["tasks"]
    if len(tasks) != 8 or len({item["task_id"] for item in tasks}) != 8:
        raise CanaryError("exactly eight unique reused tasks are required")
    old = load(OLD / "tasks" / "generator-visible.json")["tasks"]
    if [(x["task_id"], x["domain"], x["profile"], x["request"]) for x in tasks] != [
        (x["task_id"], x["domain"], x["profile"], x["request"]) for x in old
    ]:
        raise CanaryError("task requests drifted from the frozen Skill 2.1 canary")
    calls = load(MANIFEST)["calls"]
    if len(calls) != 16 or len({item["call_id"] for item in calls}) != 16:
        raise CanaryError("manifest must contain exactly sixteen unique calls")
    if sum(item["role"] == "generation" for item in calls) != 8:
        raise CanaryError("manifest must contain eight candidate generations")
    if sum(item["role"] == "blind_pairwise_judge" for item in calls) != 8:
        raise CanaryError("manifest must contain eight blind judgments")
    if load(MANIFEST)["baseline_generation_calls"] != 0:
        raise CanaryError("v0.2 regeneration is prohibited")
    baselines = load(BASELINES)
    if len(baselines["baseline_outputs"]) != 8:
        raise CanaryError("eight frozen v0.2 outputs are required")
    for item in baselines["baseline_outputs"] + baselines["skill_2_1_full_audit_references"]:
        path = ROOT / item["path"]
        if hash_file(path) != item["file_sha256"] or hash_text(load(path)["output"]) != item["output_sha256"]:
            raise CanaryError(f"frozen historical output drifted: {item['task_id']}")
    if len(load(PREREG)["acceptance_rules"]) != 14:
        raise CanaryError("all fourteen acceptance rules must be frozen")


def validate_freeze() -> None:
    validate_static()
    freeze = load(CANARY / "freeze.json")
    if freeze["candidate_skill_sha256"] != hash_tree(SKILL):
        raise CanaryError("candidate Skill drifted after freeze")
    if freeze["frozen_inputs_sha256"] != tracked_freeze_inputs():
        raise CanaryError("a frozen canary input drifted")
    if freeze["automated_holdout_opened"] or freeze["expert_holdout_opened"]:
        raise CanaryError("an official holdout is marked opened")


def word_count(text: str) -> int:
    return len(WORD.findall(text))


def structure(text: str) -> dict[str, int]:
    rows = TABLE_ROW.findall(text)
    separators = sum(bool(re.match(r"^\s*\|?\s*:?-+", row)) for row in rows)
    return {
        "word_count": word_count(text),
        "heading_count": len(HEADING.findall(text)),
        "table_count": 1 if rows else 0,
        "table_data_rows": max(0, len(rows) - separators - (1 if rows else 0)),
        "bullet_count": len(re.findall(r"(?m)^\s*[-*]\s+", text)),
    }


def sentence_overclaim(text: str, kind: str) -> bool:
    for sentence in re.split(r"(?<=[.!?])\s+|\n+", text):
        lower = sentence.casefold()
        if NEGATION.search(sentence):
            continue
        if kind == "runtime_to_profit" and (
            ("runtime" in lower or "faster" in lower)
            and "profit" in lower
            and re.search(r"\b(?:raise|increase|improve|therefore|so|translate|lead)\w*\b", lower)
        ):
            return True
        if kind == "post_deadline_value" and (
            ("after" in lower or "post-deadline" in lower)
            and ("certificate" in lower or "proof" in lower)
            and re.search(r"\b(?:improve|benefit|value|change)\w*\b", lower)
        ):
            return True
    return False


def deterministic_unsupported_claims(text: str, request: str) -> list[str]:
    flags = []
    request_numbers = set(re.findall(r"\d+(?:\.\d+)?", request))
    for match in re.finditer(r"\d+(?:\.\d+)?%?", text):
        token = match.group(0).rstrip("%")
        context = text[max(0, match.start() - 36):match.end() + 36]
        if token in request_numbers or STRUCTURAL_NUMBER.search(context):
            continue
        if re.search(
            r"\b(?:market|company|firms?|users?|customers?|profit|revenue|cost|runtime|faster|slower|effect|increase|decrease|prevalence|billion|million|percent)\b",
            context,
            re.I,
        ):
            flags.append(f"unsupported empirical quantity: {match.group(0)}")
    for pattern, label in (
        (r"\b(?:widely|commonly|rapidly|typically)\s+(?:increasing|observed|used|adopted)\b", "unsupported prevalence"),
        (r"\b(?:first study|no prior research|literature has not)\b", "unsupported literature fact"),
        (r"\b(?:causes?|caused|leads? to)\b", "unsupported causal wording"),
    ):
        if re.search(pattern, text, re.I) and not re.search(pattern, request, re.I):
            flags.append(label)
    return sorted(set(flags))


def deterministic_profile_render(text: str, profile: str) -> bool:
    info = structure(text)
    limits = {"micro": 120, "compact": 220, "standard": 500}
    if profile in limits and info["word_count"] > limits[profile]:
        return False
    if profile in {"micro", "compact"} and info["heading_count"] > 0:
        return False
    if profile == "standard" and info["table_count"] > 1:
        return False
    if profile == "standard" and info["table_count"] and not 3 <= info["table_data_rows"] <= 8:
        return False
    return True


def prepare_pairs() -> None:
    validate_freeze()
    tasks = load(TASKS)["tasks"]
    baseline_map = {
        item["task_id"]: load(ROOT / item["path"])["output"]
        for item in load(BASELINES)["baseline_outputs"]
    }
    candidate_map = {}
    for index, task in enumerate(tasks, 1):
        record = load(GEN_DIR / f"GEN-{index:02d}.json")
        validate_schema(record, "generation-result.schema.json")
        candidate_map[task["task_id"]] = record["output"]

    pair_key = {"schema_version": "skill-2.2-condition-key-1.0", "pairs": []}
    uat_key = {"schema_version": "skill-2.2-uat-key-1.0", "pairs": []}
    for index, task in enumerate(tasks, 1):
        task_id = task["task_id"]
        swap = int(hashlib.sha256(
            f"{load(PREREG)['pair_seed']}:{task_id}".encode()
        ).hexdigest(), 16) % 2 == 1
        a, b = (
            (candidate_map[task_id], baseline_map[task_id])
            if swap else (baseline_map[task_id], candidate_map[task_id])
        )
        pair = {
            "schema_version": "skill-2.2-pair-1.0",
            "pair_id": f"PAIR-{index:02d}",
            "task_id": task_id,
            "profile": task["profile"],
            "deliverable": task["deliverable"],
            "request": task["request"],
            "output_a": a,
            "output_b": b,
        }
        pair["pair_sha256"] = hash_text(json.dumps(pair, sort_keys=True, ensure_ascii=False))
        validate_schema(pair, "blinded-pair.schema.json")
        dump(PAIR_DIR / f"PAIR-{index:02d}.json", pair)
        pair_key["pairs"].append({
            "pair_id": pair["pair_id"],
            "task_id": task_id,
            "a": "skill-2.2-adaptive" if swap else "v0.2",
            "b": "v0.2" if swap else "skill-2.2-adaptive",
        })

        uat_swap = int(hashlib.sha256(
            f"{load(PREREG)['uat_seed']}:{task_id}".encode()
        ).hexdigest(), 16) % 2 == 1
        ua, ub = (
            (candidate_map[task_id], baseline_map[task_id])
            if uat_swap else (baseline_map[task_id], candidate_map[task_id])
        )
        packet = (
            f"# Product-owner development review {index:02d}\n\n"
            f"**Task:** `{task_id}`\n\n## Request\n\n{task['request']}\n\n"
            f"## Output A\n\n{ua}\n\n## Output B\n\n{ub}\n"
        )
        path = UAT / "pairs" / f"UAT-{index:02d}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(packet, encoding="utf-8", newline="\n")
        uat_key["pairs"].append({
            "packet_id": f"UAT-{index:02d}",
            "task_id": task_id,
            "a": "skill-2.2-adaptive" if uat_swap else "v0.2",
            "b": "v0.2" if uat_swap else "skill-2.2-adaptive",
        })
    dump(LOCAL / "condition-key.json", pair_key)
    dump(LOCAL / "uat-condition-key.json", uat_key)
    form = (
        "# Product-owner development review\n\n"
        "Review the eight blinded pairs without inspecting any condition key. This "
        "is product development review, not expert review or validation.\n\n"
        "| Pair | Preferred (A/B/tie) | Better suited to deliverable | Easier to use | "
        "Better organized | Less repetitive | Model meaning preserved | Evidence "
        "boundaries preserved | Serious error | Short note |\n"
        "|---|---|---|---|---|---|---|---|---|---|\n"
        + "".join(f"| UAT-{i:02d} |  |  |  |  |  |  |  |  |  |\n" for i in range(1, 9))
    )
    (UAT / "review-form.md").write_text(form, encoding="utf-8", newline="\n")


def decode_judgments() -> list[dict[str, Any]]:
    key = {
        item["pair_id"]: item
        for item in load(LOCAL / "condition-key.json")["pairs"]
    }
    decoded = []
    for index in range(1, 9):
        judgment = load(JUDGE_DIR / f"JUDGE-{index:02d}.json")
        validate_schema(judgment, "judge-result.schema.json")
        mapping = key[f"PAIR-{index:02d}"]
        candidate_side = "a" if mapping["a"] == "skill-2.2-adaptive" else "b"
        baseline_side = "b" if candidate_side == "a" else "a"
        preference = judgment["overall_preference"]
        winner = "tie" if preference == "tie" else mapping[
            "a" if preference == "A better" else "b"
        ]
        decoded.append({
            "task_id": judgment["task_id"],
            "winner": winner,
            "candidate_material_fidelity_defect": judgment[f"material_fidelity_defect_in_{candidate_side}"],
            "baseline_material_fidelity_defect": judgment[f"material_fidelity_defect_in_{baseline_side}"],
            "candidate_unsupported_factual_claim": judgment[f"unsupported_factual_claim_in_{candidate_side}"],
            "baseline_unsupported_factual_claim": judgment[f"unsupported_factual_claim_in_{baseline_side}"],
            "candidate_scope_generalization_error": judgment[f"scope_generalization_error_in_{candidate_side}"],
            "baseline_scope_generalization_error": judgment[f"scope_generalization_error_in_{baseline_side}"],
            "candidate_profile_compliant": judgment[f"profile_compliant_{candidate_side}"],
            "candidate_avoidable_repetition": judgment[f"avoidable_substantive_repetition_in_{candidate_side}"],
            "candidate_visible_nonapplicable_layers": judgment[f"visible_nonapplicable_layers_in_{candidate_side}"],
            "candidate_missing_safeguard": judgment[f"missing_required_safeguard_in_{candidate_side}"],
            "candidate_or_standard_safeguards": judgment[f"or_standard_safeguards_in_{candidate_side}"],
            "candidate_is_mapping_fit": judgment[f"is_mapping_fit_in_{candidate_side}"],
            "rationale": judgment["rationale"],
        })
    return decoded


def summarize(deterministic_checks_passed: bool) -> dict[str, Any]:
    validate_freeze()
    tasks = load(TASKS)["tasks"]
    task_map = {item["task_id"]: item for item in tasks}
    outputs = {}
    for index, task in enumerate(tasks, 1):
        record = load(GEN_DIR / f"GEN-{index:02d}.json")
        validate_schema(record, "generation-result.schema.json")
        text = record["output"]
        outputs[task["task_id"]] = {
            **structure(text),
            "deterministic_render_compliant": deterministic_profile_render(text, task["profile"]),
            "deterministic_unsupported_claims": deterministic_unsupported_claims(text, task["request"]),
            "runtime_to_profit": sentence_overclaim(text, "runtime_to_profit"),
            "post_deadline_same_cycle_value": sentence_overclaim(text, "post_deadline_value"),
        }
    decoded = decode_judgments()
    by_task = {item["task_id"]: item for item in decoded}

    new_fidelity = sum(
        item["candidate_material_fidelity_defect"]
        and not item["baseline_material_fidelity_defect"]
        for item in decoded
    )
    unsupported = sum(
        bool(outputs[item["task_id"]]["deterministic_unsupported_claims"])
        or (item["candidate_unsupported_factual_claim"] and not item["baseline_unsupported_factual_claim"])
        for item in decoded
    )
    scope = sum(
        item["candidate_scope_generalization_error"]
        and not item["baseline_scope_generalization_error"]
        for item in decoded
    )
    runtime = sum(item["runtime_to_profit"] for item in outputs.values())
    post_deadline = sum(item["post_deadline_same_cycle_value"] for item in outputs.values())
    nonapp = sum(item["candidate_visible_nonapplicable_layers"] for item in decoded)
    compliant = sum(
        outputs[item["task_id"]]["deterministic_render_compliant"]
        and item["candidate_profile_compliant"]
        for item in decoded
    )
    no_repeat = sum(not item["candidate_avoidable_repetition"] for item in decoded)
    non_full = [item for item in decoded if task_map[item["task_id"]]["profile"] != "full-audit"]
    wins = sum(item["winner"] == "skill-2.2-adaptive" for item in non_full)
    full = [item for item in decoded if task_map[item["task_id"]]["profile"] == "full-audit"]
    full_losses = sum(
        item["winner"] == "v0.2"
        and (item["candidate_material_fidelity_defect"] or item["candidate_missing_safeguard"])
        for item in full
    )

    refs = {
        item["task_id"]: load(ROOT / item["path"])["output"]
        for item in load(BASELINES)["skill_2_1_full_audit_references"]
    }
    simplified = 0
    for item in full:
        task_id = item["task_id"]
        candidate = outputs[task_id]
        old_structure = structure(refs[task_id])
        if (
            not item["candidate_missing_safeguard"]
            and not item["candidate_material_fidelity_defect"]
            and (
                candidate["word_count"] < old_structure["word_count"]
                or candidate["heading_count"] + candidate["table_count"]
                < old_structure["heading_count"] + old_structure["table_count"]
            )
        ):
            simplified += 1
    or_ok = by_task["OR-S02"]["candidate_or_standard_safeguards"]
    is_ok = by_task["IS-S02"]["candidate_is_mapping_fit"]
    observed = {
        "new_material_fidelity_contradictions": new_fidelity,
        "new_unsupported_factual_claims": unsupported,
        "runtime_to_profit_conversions": runtime,
        "post_deadline_same_cycle_value_claims": post_deadline,
        "scope_or_generalization_errors": scope,
        "candidate_visible_nonapplicable_layers": nonapp,
        "adaptive_contract_compliant_outputs": compliant,
        "outputs_without_avoidable_repetition": no_repeat,
        "non_full_audit_candidate_wins": wins,
        "non_full_audit_ties": sum(item["winner"] == "tie" for item in non_full),
        "full_audit_fidelity_or_safeguard_losses": full_losses,
        "full_audit_simplified_outputs": simplified,
        "or_standard_safeguards": or_ok,
        "is_standard_mapping_fit": is_ok,
        "deterministic_checks_passed": deterministic_checks_passed,
    }
    gates = {
        "1_new_material_fidelity_contradictions": new_fidelity == 0,
        "2_new_unsupported_factual_claims": unsupported == 0,
        "3_runtime_to_profit_conversions": runtime == 0,
        "4_post_deadline_same_cycle_value_claims": post_deadline == 0,
        "5_scope_or_generalization_errors": scope == 0,
        "6_candidate_visible_nonapplicable_layers": nonapp == 0,
        "7_adaptive_contract_compliance": compliant >= 7,
        "8_outputs_without_avoidable_repetition": no_repeat >= 5,
        "9_non_full_audit_candidate_wins": wins >= 4,
        "10_full_audit_fidelity_or_safeguard_losses": full_losses == 0,
        "11_full_audit_simplification": simplified >= 1,
        "12_or_standard_safeguards": or_ok,
        "13_is_standard_mapping_fit": is_ok,
        "14_deterministic_checks": deterministic_checks_passed,
    }
    passed = all(gates.values())
    result = {
        "schema_version": "skill-2.2-canary-result-1.0",
        "status": "pass" if passed else "fail",
        "development_merge_eligible": passed,
        "validation_authorized": False,
        "release_authorized": False,
        "authoritative_calls_planned": 16,
        "authoritative_calls_used": 16,
        "baseline_generation_calls": 0,
        "retries": 0,
        "replacements": 0,
        "adjudications": 0,
        "additional_model_roles": 0,
        "observed": observed,
        "gates": gates,
        "per_task_metrics": outputs,
        "decoded_pairwise_results": decoded,
        "automated_holdout_opened": False,
        "expert_holdout_opened": False,
        "no_human_experts": True,
    }
    dump(RESULT, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=["prepare", "validate", "validate-freeze", "prepare-pairs", "summarize"],
    )
    parser.add_argument(
        "--deterministic-checks-passed",
        action="store_true",
        help="Record the preregistered deterministic repository gate as passed.",
    )
    args = parser.parse_args()
    if args.command == "prepare":
        prepare()
    elif args.command == "validate":
        validate_static()
    elif args.command == "validate-freeze":
        validate_freeze()
    elif args.command == "prepare-pairs":
        prepare_pairs()
    else:
        summarize(args.deterministic_checks_passed)
    print(f"Skill 2.2 adaptive canary {args.command} passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
