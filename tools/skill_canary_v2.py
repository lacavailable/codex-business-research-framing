#!/usr/bin/env python3
"""Deterministic development checks for the bounded Skill 2.2 canary.

This module intentionally contains no generation, judging, freezing, or
holdout access.  It only validates the public canary configuration and scores
rendered text against its task-local audit record.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

import jsonschema


ROOT = Path(__file__).resolve().parents[1]
CANARY = ROOT / "evals" / "skill-2.2-canary"
SKILL = ROOT / "skills" / "frame-business-research-problem"
LOCAL = ROOT / ".local-eval" / "skill-2.2-canary"
TASKS = CANARY / "tasks" / "generator-visible.json"
AUDIT = CANARY / "tasks" / "audit-only.json"
PREREG = CANARY / "preregistration.json"
MANIFEST = CANARY / "runs" / "call-manifest.json"
FREEZE = CANARY / "freeze.json"
GEN_DIR = CANARY / "outputs"
PAIR_DIR = CANARY / "blinded-pairs"
JUDGE_DIR = CANARY / "judgments"
RESULT = CANARY / "results" / "canary-result.json"
COMPLETION = CANARY / "runs" / "completion.json"

WORD = re.compile(r"\b[\w]+(?:[-'][\w]+)*\b", re.UNICODE)
HEADING = re.compile(r"(?m)^#{1,6}\s+")
BLANK_BLOCK = re.compile(r"\n\s*\n+")

# These forms identify a numeric assertion about a measured quantity.  Bare
# numerals are deliberately excluded: they are often schema, section, or
# list labels in a structured business-research answer.
EMPIRICAL_QUANTITY = re.compile(
    r"""
    (?:
        \b\d+(?:\.\d+)?\s*(?:%|percent)                  # percentage
      | [$€£¥]\s*\d+(?:,\d{3})*(?:\.\d+)?                 # currency prefix
      | \b\d+(?:,\d{3})*(?:\.\d+)?\s*(?:usd|eur|gbp|cny|rmb)\b
      | \b\d+(?:\.\d+)?\s*(?:milliseconds?|msecs?|seconds?|secs?|minutes?|mins?|hours?|hrs?|days?|weeks?|months?|years?)\b
      | \b\d+(?:\.\d+)?\s*(?:per|/)\s*\w+               # rate
      | \b\d+(?:\.\d+)?\s*(?:kg|g|mg|lb|lbs|km|miles?|meters?|metres?|cm|mm|kwh|wh|mb|gb|tb|lit(?:er|re)s?|units?)\b
      | \b\d{4}-\d{1,2}-\d{1,2}\b                        # ISO date
      | \b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+\d{1,2},?\s+\d{4}\b
      | \b(?:19|20)\d{2}\b                                # calendar year
      | \b\d+(?:\.\d+)?\s+(?:customers?|patients?|firms?|cases?|instances?|observations?|trials?|participants?|respondents?|accounts?|hospitals?|platforms?|authorities?|routes?|workers?|users?|samples?|records?|items?)\b
      | \b(?:sample(?:\s+size)?|count|n)\s*(?:of|=|:)?\s*\d+(?:\.\d+)?\b
    )
    """,
    flags=re.I | re.X,
)


class CanaryError(ValueError):
    """Raised when a supposedly frozen public canary has drifted."""


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")


def hash_value(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def hash_file(path: Path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def hash_tree(root: Path) -> str:
    digest = hashlib.sha256()
    files = [
        path
        for path in root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    ]
    for path in sorted(
        files, key=lambda item: item.relative_to(root).as_posix().casefold()
    ):
        relative = path.relative_to(root).as_posix()
        digest.update(relative.encode("utf-8") + b"\0")
        digest.update(bytes.fromhex(hash_file(path)))
    return digest.hexdigest()


def hash_git_tree(commit: str, root: str) -> str:
    paths = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", commit, "--", root],
        cwd=ROOT,
        text=True,
    ).splitlines()
    digest = hashlib.sha256()
    for path in sorted(paths, key=str.casefold):
        relative = path.removeprefix(f"{root}/")
        data = subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=ROOT)
        data = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        digest.update(relative.encode("utf-8") + b"\0")
        digest.update(hashlib.sha256(data).digest())
    return digest.hexdigest()


def validate_schema(record: Any, name: str) -> None:
    schema = _load(CANARY / "schemas" / name)
    jsonschema.Draft202012Validator(schema).validate(record)


def task_maps() -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    """Return generator-visible and audit-only tasks keyed by task ID."""
    visible = {item["task_id"]: item for item in _load(TASKS)["tasks"]}
    audit = {item["task_id"]: item for item in _load(AUDIT)["tasks"]}
    if not visible or set(visible) != set(audit):
        raise CanaryError("generator-visible and audit-only task IDs differ")
    if len(visible) != len(_load(TASKS)["tasks"]) or len(audit) != len(_load(AUDIT)["tasks"]):
        raise CanaryError("task IDs must be unique")
    return visible, audit


def validate_static() -> None:
    """Check the public canary's fixed task surface and exact call budget."""
    prereg = _load(PREREG)
    visible, audit = task_maps()
    if len(visible) != 4:
        raise CanaryError("Skill 2.2 requires exactly four public tasks")
    if {item["domain"] for item in visible.values()} != {"OM", "IS", "OR", "cross-domain"}:
        raise CanaryError("the four public domains must each appear once")
    if sorted(item["profile"] for item in visible.values()) != ["compact", "compact", "full-audit", "standard"]:
        raise CanaryError("public profile allocation drifted")
    visible_fields = {"task_id", "domain", "profile", "request"}
    if any(set(item) != visible_fields for item in visible.values()):
        raise CanaryError("generator-visible tasks contain hidden fields")
    required_audit = {
        "task_id", "profile_constraints", "answer_first_patterns",
        "required_invariants", "limitation_families",
        "supplied_empirical_numbers", "unsupported_empirical_patterns",
        "prohibited_overclaims",
    }
    if any(not required_audit.issubset(item) for item in audit.values()):
        raise CanaryError("audit-only records are incomplete")
    for item in audit.values():
        constraints = item["profile_constraints"]
        if set(constraints) != {"minimum_words", "maximum_words", "maximum_headings", "maximum_visible_blocks"}:
            raise CanaryError("profile constraints are incomplete")

    calls = _load(MANIFEST)["calls"]
    if len(calls) != 12 or len({call.get("call_id") for call in calls}) != 12:
        raise CanaryError("manifest must contain exactly twelve unique calls")
    if sum(call.get("role") == "generation" for call in calls) != 8:
        raise CanaryError("manifest must contain eight generation calls")
    if sum(call.get("role") == "blind_pairwise_judge" for call in calls) != 4:
        raise CanaryError("manifest must contain four blind judges")
    if _load(MANIFEST).get("maximum_authoritative_calls") != 12 or prereg.get("maximum_authoritative_calls") != 12:
        raise CanaryError("authoritative call cap drifted")
    if prereg.get("required_generation_calls") != 8 or prereg.get("required_judge_calls") != 4:
        raise CanaryError("preregistered call allocation drifted")


def write_freeze() -> dict[str, Any]:
    """Freeze the evaluator and candidate after implementation, before calls."""
    validate_static()
    if any(GEN_DIR.glob("GEN-*.json")) or any(JUDGE_DIR.glob("JUDGE-*.json")):
        raise CanaryError("authoritative records already exist")
    prereg = _load(PREREG)
    candidate_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    record = {
        "schema_version": "skill-canary-freeze-2.0",
        "preregistration_sha256": hash_file(PREREG),
        "generator_tasks_sha256": hash_file(TASKS),
        "audit_tasks_sha256": hash_file(AUDIT),
        "call_manifest_sha256": hash_file(MANIFEST),
        "tool_sha256": hash_file(Path(__file__)),
        "candidate_skill_sha256": hash_tree(SKILL),
        "baseline_skill_sha256": hash_git_tree(
            prereg["baseline_commit"], "skills/frame-business-research-problem"
        ),
        "candidate_commit": candidate_commit,
        "baseline_commit": prereg["baseline_commit"],
        "automated_holdout_opened": False,
        "expert_holdout_opened": False,
    }
    _dump(FREEZE, record)
    return record


def validate_freeze() -> None:
    record = _load(FREEZE)
    prereg = _load(PREREG)
    expected = {
        "preregistration_sha256": hash_file(PREREG),
        "generator_tasks_sha256": hash_file(TASKS),
        "audit_tasks_sha256": hash_file(AUDIT),
        "call_manifest_sha256": hash_file(MANIFEST),
        "tool_sha256": hash_file(Path(__file__)),
        "candidate_skill_sha256": hash_tree(SKILL),
        "baseline_skill_sha256": hash_git_tree(
            prereg["baseline_commit"], "skills/frame-business-research-problem"
        ),
        "baseline_commit": prereg["baseline_commit"],
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


def _normalise_quantity(value: str) -> str:
    value = value.casefold().replace(",", "")
    value = re.sub(r"\s+", "", value)
    value = value.replace("percent", "%")
    return value


def _structural_number_context(text: str, start: int, end: int) -> bool:
    """Return whether a numeral is functioning as an explicit structure label."""
    before = text[max(0, start - 45):start]
    after = text[end:min(len(text), end + 35)]
    context = f"{before}{after}".casefold()
    line_start = text.rfind("\n", 0, start) + 1
    line_prefix = text[line_start:start]
    bare_number = bool(re.fullmatch(r"\d+(?:\.\d+)?", text[start:end]))
    return bool(
        re.search(r"(?:businessbrief|schema(?:\s+version)?|version)\s*$", before, re.I)
        or re.search(r"(?:dfc|stage|section|gate)\s*-?\s*$", before, re.I)
        or (bare_number and re.match(r"\s*(?:[.)]|[-:])", after))
        or (bare_number and re.match(r"\s*\d+[.)]\s*$", line_prefix))
        or re.search(r"\b(?:all|the)\s+(?:six|\d+)\s+gates\b", context, re.I)
        or re.search(r"\b\d+\s+gates?\b", context, re.I)
    )


def unsupported_empirical_facts(text: str, audit: dict[str, Any]) -> list[str]:
    """Flag candidate-added empirical quantities and prohibited fact phrases.

    Task-supplied quantities are permitted.  Numeric structural labels are not
    empirical assertions and therefore do not enter the detector at all.
    """
    allowed = {_normalise_quantity(value) for value in audit.get("supplied_empirical_numbers", [])}
    findings: list[str] = []
    seen: set[str] = set()
    for match in EMPIRICAL_QUANTITY.finditer(text):
        quantity = match.group(0)
        if _structural_number_context(text, match.start(), match.end()):
            continue
        if _normalise_quantity(quantity) not in allowed:
            key = f"quantity:{_normalise_quantity(quantity)}"
            if key not in seen:
                findings.append(quantity)
                seen.add(key)
    for pattern in audit.get("unsupported_empirical_patterns", []):
        if re.search(re.escape(pattern), text, flags=re.I):
            key = f"pattern:{pattern.casefold()}"
            if key not in seen:
                findings.append(pattern)
                seen.add(key)
    return findings


def _visible_units(text: str) -> list[str]:
    """Split prose into user-visible blocks, treating each list item as a unit."""
    units: list[str] = []
    for block in BLANK_BLOCK.split(text.strip()):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        prose: list[str] = []
        for line in lines:
            if re.match(r"(?:[-*+]\s+|\d+[.)]\s+)", line):
                if prose:
                    units.append(" ".join(prose))
                    prose = []
                units.append(re.sub(r"^(?:[-*+]\s+|\d+[.)]\s+)", "", line))
            else:
                prose.append(line)
        if prose:
            units.append(" ".join(prose))
    return units


def duplicate_limitation_units(text: str, audit: dict[str, Any]) -> int:
    """Count repeated limitation *blocks*, never repeated topic words."""
    units = _visible_units(text)
    duplicates = 0
    for patterns in audit.get("limitation_families", {}).values():
        matched_units = sum(
            any(re.search(pattern, unit, flags=re.I | re.S) for pattern in patterns)
            for unit in units
        )
        duplicates += max(0, matched_units - 1)
    return duplicates


def profile_compliant(text: str, constraints: dict[str, int | None]) -> bool:
    """Check task-specific word, heading, and visible-block ceilings."""
    words = len(WORD.findall(text))
    lower = constraints.get("minimum_words")
    upper = constraints.get("maximum_words")
    if lower is not None and words < lower:
        return False
    if upper is not None and words > upper:
        return False
    heading_limit = constraints.get("maximum_headings")
    if heading_limit is not None and len(HEADING.findall(text)) > heading_limit:
        return False
    block_limit = constraints.get("maximum_visible_blocks")
    return block_limit is None or len(_visible_units(text)) <= block_limit


def usable_answer_first(text: str, audit: dict[str, Any]) -> bool:
    """Require the first substantive visible block to match a task answer cue."""
    for unit in _visible_units(text):
        substantive = re.sub(r"(?m)^#{1,6}\s+.*$", "", unit).strip()
        if substantive:
            return any(re.search(pattern, substantive, flags=re.I) for pattern in audit.get("answer_first_patterns", []))
    return False


NEGATION = re.compile(
    r"\b(?:not|no|cannot|can't|doesn't|does not|without|unsupported|unproven)\b",
    re.I,
)


def sentence_overclaim(text: str, kind: str) -> bool:
    for sentence in re.split(r"(?<=[.!?])\s+|\n+", text):
        lowered = sentence.casefold()
        if NEGATION.search(sentence):
            continue
        if kind == "runtime_to_profit":
            if (
                ("runtime" in lowered or "faster" in lowered)
                and ("profit" in lowered or "service" in lowered)
                and re.search(
                    r"\b(?:raise|increase|improve|therefore|so|translate|lead)\w*\b",
                    lowered,
                )
            ):
                return True
        elif kind == "equivalent_formulation_changes_optimum":
            if (
                "equivalent" in lowered
                and ("optimum" in lowered or "objective" in lowered)
                and re.search(r"\b(?:change|raise|improve)\w*\b", lowered)
            ):
                return True
        elif kind == "post_deadline_value":
            if (
                ("after" in lowered or "post-deadline" in lowered or "later" in lowered)
                and ("certificate" in lowered or "proof" in lowered)
                and re.search(r"\b(?:improve|benefit|value|change)\w*\b", lowered)
            ):
                return True
    return False


def output_metrics(record: dict[str, Any], audit: dict[str, Any]) -> dict[str, Any]:
    text = record["output"]
    constraints = audit["profile_constraints"]
    required = {
        pattern: bool(re.search(pattern, text, flags=re.I))
        for pattern in audit["required_invariants"]
    }
    overclaims = {
        kind: sentence_overclaim(text, kind)
        for kind in audit["prohibited_overclaims"]
    }
    return {
        "word_count": len(WORD.findall(text)),
        "section_count": len(HEADING.findall(text)),
        "visible_block_count": len(_visible_units(text)),
        "profile_compliant": profile_compliant(text, constraints),
        "usable_answer_first": usable_answer_first(text, audit),
        "duplicate_limitation_units": duplicate_limitation_units(text, audit),
        "unsupported_empirical_facts": unsupported_empirical_facts(text, audit),
        "required_invariants": required,
        "required_invariants_present": all(required.values()),
        "prohibited_overclaims": overclaims,
    }


def _pair_swap(seed: str, task_id: str) -> bool:
    digest = hashlib.sha256(f"{seed}:{task_id}".encode("utf-8")).digest()
    return bool(digest[0] & 1)


def prepare_pairs() -> list[dict[str, Any]]:
    validate_freeze()
    visible, _ = task_maps()
    records: dict[tuple[str, str], dict[str, Any]] = {}
    for call in _load(MANIFEST)["calls"]:
        if call["role"] != "generation":
            continue
        record = _load(GEN_DIR / f"{call['call_id']}.json")
        validate_schema(record, "generation-result.schema.json")
        if (
            record["task_id"] != call["task_id"]
            or record["condition"] != call["condition"]
            or record["model"] != call["model"]
            or record["reasoning"] != call["reasoning"]
        ):
            raise CanaryError(f"generation metadata mismatch: {call['call_id']}")
        records[(call["task_id"], call["condition"])] = record

    seed = _load(PREREG)["pair_seed"]
    local_key = {"schema_version": "skill-canary-key-2.0", "pairs": []}
    pairs: list[dict[str, Any]] = []
    for index, (task_id, task) in enumerate(visible.items(), start=1):
        baseline = records[(task_id, "skill-2.1")]["output"]
        candidate = records[(task_id, "skill-2.2")]["output"]
        swap = _pair_swap(seed, task_id)
        output_a, output_b = (
            (candidate, baseline) if swap else (baseline, candidate)
        )
        pair_id = f"PAIR-{index:02d}"
        payload = {
            "task_id": task_id,
            "request": task["request"],
            "output_a": output_a,
            "output_b": output_b,
        }
        pair = {
            "schema_version": "skill-canary-pair-2.0",
            "pair_id": pair_id,
            **payload,
            "pair_sha256": hash_value(payload),
        }
        validate_schema(pair, "blinded-pair.schema.json")
        _dump(PAIR_DIR / f"{pair_id}.json", pair)
        local_key["pairs"].append(
            {
                "pair_id": pair_id,
                "task_id": task_id,
                "a": "skill-2.2" if swap else "skill-2.1",
                "b": "skill-2.1" if swap else "skill-2.2",
            }
        )
        pairs.append(pair)
    _dump(LOCAL / "pair-key.json", local_key)
    return pairs


def judge_prompt(pair: dict[str, Any]) -> str:
    return (
        "Blindly compare two answers to the same business-research framing request. "
        "Do not infer which system produced either answer. Judge usability, model "
        "fidelity, managerial clarity, and prose economy. A material fidelity issue "
        "changes or invents the actor, decision, timing, information, feasible set, "
        "mechanism, objective, or evidence boundary. Return only one JSON object with "
        "these exact keys: schema_version='skill-canary-judge-2.0', "
        f"call_id, pair_id='{pair['pair_id']}', task_id='{pair['task_id']}', "
        f"pair_sha256='{pair['pair_sha256']}', model='gpt-5.6-sol', reasoning='high', "
        "criteria={usability,model_fidelity,managerial_clarity,prose_economy} where "
        "each value is 'A better', 'B better', or 'tie'; overall_preference with the "
        "same vocabulary; material_fidelity_issue_in_a boolean; "
        "material_fidelity_issue_in_b boolean; rationale string. "
        "Set call_id to the JUDGE number corresponding to the PAIR number.\n\n"
        f"REQUEST:\n{pair['request']}\n\nOUTPUT A:\n{pair['output_a']}\n\n"
        f"OUTPUT B:\n{pair['output_b']}"
    )


def _full_audit_labels_present(text: str, audit: dict[str, Any]) -> bool:
    if not audit.get("required_structural_labels"):
        return True
    return bool(
        re.search(r"BusinessBrief\s+2\.0", text, re.I)
        and re.search(r"DFC-12", text, re.I)
        and re.search(r"(?:six|6).{0,20}gates", text, re.I)
    )


def score() -> dict[str, Any]:
    validate_freeze()
    visible, audit = task_maps()
    metrics: dict[str, dict[str, Any]] = {}
    for task_id in visible:
        metrics[task_id] = {}
        for condition in ("skill-2.1", "skill-2.2"):
            call = next(
                item
                for item in _load(MANIFEST)["calls"]
                if item["role"] == "generation"
                and item["task_id"] == task_id
                and item["condition"] == condition
            )
            record = _load(GEN_DIR / f"{call['call_id']}.json")
            validate_schema(record, "generation-result.schema.json")
            metrics[task_id][condition] = output_metrics(record, audit[task_id])

    key = _load(LOCAL / "pair-key.json")
    mapping = {item["task_id"]: item for item in key["pairs"]}
    decoded: list[dict[str, Any]] = []
    for index, task_id in enumerate(visible, start=1):
        judgment = _load(JUDGE_DIR / f"JUDGE-{index:02d}.json")
        validate_schema(judgment, "judge-result.schema.json")
        pair = _load(PAIR_DIR / f"PAIR-{index:02d}.json")
        if judgment["pair_sha256"] != pair["pair_sha256"]:
            raise CanaryError(f"judge pair hash mismatch: {task_id}")
        item = mapping[task_id]
        candidate_side = "a" if item["a"] == "skill-2.2" else "b"
        baseline_side = "b" if candidate_side == "a" else "a"
        preference = judgment["overall_preference"]
        if preference == "tie":
            winner = "tie"
        else:
            preferred_side = "a" if preference == "A better" else "b"
            winner = item[preferred_side]
        decoded.append(
            {
                "task_id": task_id,
                "winner": winner,
                "candidate_material_fidelity_issue": judgment[
                    f"material_fidelity_issue_in_{candidate_side}"
                ],
                "baseline_material_fidelity_issue": judgment[
                    f"material_fidelity_issue_in_{baseline_side}"
                ],
            }
        )

    candidate = [metrics[task]["skill-2.2"] for task in visible]
    prose_tasks = [
        task for task, item in visible.items() if item["profile"] != "full-audit"
    ]
    profile_rate = sum(item["profile_compliant"] for item in candidate) / len(candidate)
    answer_rate = sum(item["usable_answer_first"] for item in candidate) / len(candidate)
    duplicates = sum(
        metrics[task]["skill-2.2"]["duplicate_limitation_units"]
        for task in prose_tasks
    )
    unsupported = sum(
        len(item["unsupported_empirical_facts"]) for item in candidate
    )
    overclaims = sum(
        any(item["prohibited_overclaims"].values()) for item in candidate
    )
    new_fidelity = sum(
        item["candidate_material_fidelity_issue"]
        and not item["baseline_material_fidelity_issue"]
        for item in decoded
    )
    full_task = next(
        task for task, item in visible.items() if item["profile"] == "full-audit"
    )
    full_metrics = metrics[full_task]["skill-2.2"]
    full_judgment = next(item for item in decoded if item["task_id"] == full_task)
    full_noninferior = (
        full_metrics["required_invariants_present"]
        and _full_audit_labels_present(
            _load(
                GEN_DIR
                / f"{next(item['call_id'] for item in _load(MANIFEST)['calls'] if item['task_id'] == full_task and item['condition'] == 'skill-2.2')}.json"
            )["output"],
            audit[full_task],
        )
        and not full_judgment["candidate_material_fidelity_issue"]
    )
    completion = _load(COMPLETION)
    calls_complete = (
        completion["authoritative_calls_used"] == 12
        and completion["completed_generation_calls"] == 8
        and completion["completed_judge_calls"] == 4
        and completion["retries"] == 0
        and completion["replacement_calls"] == 0
        and completion["adjudication_calls"] == 0
    )
    observed = {
        "completed_authoritative_calls": completion["authoritative_calls_used"],
        "profile_compliance": profile_rate,
        "usable_answer_first": answer_rate,
        "duplicate_limitation_units": duplicates,
        "unsupported_empirical_facts": unsupported,
        "prohibited_overclaims": overclaims,
        "new_material_fidelity_regressions": new_fidelity,
        "full_audit_safeguards_noninferior": full_noninferior,
        "candidate_vs_baseline_word_delta": {
            task: metrics[task]["skill-2.2"]["word_count"]
            - metrics[task]["skill-2.1"]["word_count"]
            for task in visible
        },
        "pairwise_preference": {
            "skill-2.2": sum(item["winner"] == "skill-2.2" for item in decoded),
            "skill-2.1": sum(item["winner"] == "skill-2.1" for item in decoded),
            "tie": sum(item["winner"] == "tie" for item in decoded),
        },
    }
    gates = {
        "completed_authoritative_calls": calls_complete,
        "profile_compliance": profile_rate == 1.0,
        "usable_answer_first": answer_rate == 1.0,
        "duplicate_limitation_units": duplicates == 0,
        "unsupported_empirical_facts": unsupported == 0,
        "prohibited_overclaims": overclaims == 0,
        "new_material_fidelity_regressions": new_fidelity == 0,
        "full_audit_safeguards_noninferior": full_noninferior,
    }
    passed = all(gates.values())
    result = {
        "schema_version": "skill-canary-result-2.0",
        "status": "pass" if passed else "fail",
        "experimental_merge_authorized": passed,
        "validation_authorized": False,
        "release_authorized": False,
        "authoritative_calls_used": completion["authoritative_calls_used"],
        "observed": observed,
        "gates": gates,
        "per_output_metrics": metrics,
        "decoded_pairwise_results": decoded,
        "automated_holdout_opened": False,
        "expert_holdout_opened": False,
        "no_human_experts": True,
        "claim_boundary": _load(PREREG)["claim_boundary"],
    }
    _dump(RESULT, result)
    return result
