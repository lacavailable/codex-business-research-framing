#!/usr/bin/env python3
"""Deterministic orchestration for the business-framing benchmark.

This script prepares prompts and aggregates externally generated responses and
scores. It never calls a language model and never fabricates missing results.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

SCHEMA_VERSION = "1.0.0"
CONDITIONS = ("no_skill", "v0_1_0_alpha", "v0_2_0_beta")
DOMAINS = ("OM", "IS", "OR")
CASES_PER_DOMAIN = 14
EXPECTED_ADVERSARIAL = 23


class EvaluationError(ValueError):
    """Raised for invalid or incomplete benchmark artifacts."""


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvaluationError(f"Cannot read JSON {path}: {exc}") from exc


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        for record in records:
            stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[1]


def load_cases(root: Path) -> list[dict[str, Any]]:
    paths = sorted((root / "evals" / "cases").glob("*.json"))
    cases = [read_json(path) for path in paths]
    expected_cases = CASES_PER_DOMAIN * len(DOMAINS)
    if len(cases) != expected_cases:
        raise EvaluationError(f"Expected exactly {expected_cases} cases, found {len(cases)}")
    ids = [case.get("id") for case in cases]
    if len(ids) != len(set(ids)):
        raise EvaluationError("Case IDs are not unique")
    counts = Counter(case.get("domain") for case in cases)
    if counts != Counter({domain: CASES_PER_DOMAIN for domain in DOMAINS}):
        raise EvaluationError(f"Expected {CASES_PER_DOMAIN} cases per domain, found {dict(counts)}")
    adversarial = sum(case.get("adversarial") is True for case in cases)
    if adversarial != EXPECTED_ADVERSARIAL:
        raise EvaluationError(f"Expected exactly {EXPECTED_ADVERSARIAL} adversarial cases, found {adversarial}")
    return cases


def load_rubric(root: Path) -> dict[str, Any]:
    rubric = read_json(root / "evals" / "rubrics" / "business-framing-v2.json")
    weights = [item["weight"] for item in rubric["categories"]]
    if sum(weights) != 100:
        raise EvaluationError(f"Rubric weights sum to {sum(weights)}, not 100")
    if rubric["hard_failure_cap"] >= rubric["passing_score"]:
        raise EvaluationError("Hard-failure cap must be below the passing score")
    if any(item["minimum"] > item["weight"] for item in rubric["categories"]):
        raise EvaluationError("A layer minimum cannot exceed its weight")
    return rubric


def validate_with_jsonschema(instance: Any, schema_path: Path, label: str) -> None:
    try:
        import jsonschema  # type: ignore
    except ImportError:
        return
    schema = read_json(schema_path)
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    errors = sorted(validator.iter_errors(instance), key=lambda error: list(error.path))
    if errors:
        locations = ["/".join(map(str, error.path)) or "<root>" for error in errors]
        details = "; ".join(f"{where}: {error.message}" for where, error in zip(locations, errors))
        raise EvaluationError(f"Schema failure for {label}: {details}")


def validate_repository(root: Path) -> dict[str, Any]:
    cases = load_cases(root)
    rubric = load_rubric(root)
    schema_dir = root / "evals" / "schemas"
    for case in cases:
        validate_with_jsonschema(case, schema_dir / "case.schema.json", case["id"])
        prefix = case["id"].split("-")[0].upper()
        if prefix != case["domain"]:
            raise EvaluationError(f"Case ID/domain mismatch: {case['id']} and {case['domain']}")
    validate_with_jsonschema(rubric, schema_dir / "rubric.schema.json", "rubric")
    prompts = read_json(root / "evals" / "prompts" / "conditions.json")
    if tuple(prompts.get("conditions", {}).keys()) != CONDITIONS:
        raise EvaluationError("Prompt conditions must be ordered no-skill, v0.1, v0.2")
    return {
        "cases": len(cases),
        "domains": dict(sorted(Counter(case["domain"] for case in cases).items())),
        "conditions": len(CONDITIONS),
        "expected_generations": len(cases) * len(CONDITIONS),
        "rubric_points": sum(category["weight"] for category in rubric["categories"]),
        "jsonschema": _jsonschema_available(),
    }


def _jsonschema_available() -> bool:
    try:
        import jsonschema  # noqa: F401
    except ImportError:
        return False
    return True


def validate_committed_artifacts(root: Path) -> dict[str, Any]:
    base = root / "evals" / "artifacts" / "v0.2.0-beta"
    mappings = load_json_files(base / "blind-mappings")
    prompts = load_json_files(base / "prompts")
    outputs = load_json_files(base / "outputs")
    scores = load_json_files(base / "scores")
    expected_outputs = CASES_PER_DOMAIN * len(DOMAINS) * len(CONDITIONS)
    if len(mappings) != expected_outputs or len(prompts) != expected_outputs or len(outputs) != expected_outputs:
        raise EvaluationError(
            f"Committed artifacts require {expected_outputs} mappings, prompts, and outputs; "
            f"found {len(mappings)}, {len(prompts)}, and {len(outputs)}"
        )
    mapping_by_blind: dict[str, dict[str, Any]] = {}
    for path, item in mappings:
        required = {"schema_version", "blind_id", "case_id", "domain", "condition"}
        if set(item) != required or item["condition"] not in CONDITIONS or item["domain"] not in DOMAINS:
            raise EvaluationError(f"Invalid blind mapping: {path}")
        if item["blind_id"] in mapping_by_blind:
            raise EvaluationError(f"Duplicate mapping blind ID: {item['blind_id']}")
        mapping_by_blind[item["blind_id"]] = item
    for path, item in prompts:
        required = {"schema_version", "blind_id", "case_id", "domain", "prompt"}
        if set(item) != required or not isinstance(item["prompt"], str) or not item["prompt"].strip():
            raise EvaluationError(f"Invalid committed prompt: {path}")
        if item["blind_id"] not in mapping_by_blind:
            raise EvaluationError(f"Prompt has unknown blind ID: {path}")
    output_blinds: set[str] = set()
    for path, item in outputs:
        validate_with_jsonschema(item, root / "evals/schemas/output.schema.json", str(path))
        if item["blind_id"] in output_blinds or item["blind_id"] not in mapping_by_blind:
            raise EvaluationError(f"Duplicate or unknown output blind ID: {path}")
        output_blinds.add(item["blind_id"])
    coverage: dict[str, set[str]] = defaultdict(set)
    primary_scores = 0
    for path, item in scores:
        validate_with_jsonschema(item, root / "evals/schemas/score.schema.json", str(path))
        if item["blind_id"] not in mapping_by_blind:
            raise EvaluationError(f"Score has unknown blind ID: {path}")
        key = item["judge_id"]
        if key in coverage[item["blind_id"]]:
            raise EvaluationError(f"Duplicate judge score for {item['blind_id']}: {key}")
        coverage[item["blind_id"]].add(key)
        if key in {"judge_a", "judge_b"}:
            primary_scores += 1
    missing = [blind for blind in mapping_by_blind if not {"judge_a", "judge_b"} <= coverage[blind]]
    if missing or primary_scores != expected_outputs * 2:
        raise EvaluationError(
            f"Committed scores require {expected_outputs * 2} primary records and two-judge coverage; "
            f"found {primary_scores} with {len(missing)} incomplete outputs"
        )
    status_path = root / "evals/reports/v0.2.0-beta.status.json"
    status = read_json(status_path)
    if status.get("status") != "complete" or status.get("outputs") != expected_outputs or status.get("primary_scores") != expected_outputs * 2:
        raise EvaluationError("Published evaluation status is absent or incomplete")
    return {
        "outputs": expected_outputs,
        "primary_scores": primary_scores,
        "adjudicator_scores": len(scores) - primary_scores,
    }


def blind_id(seed: str, case_id: str, condition: str) -> str:
    digest = hashlib.sha256(f"{seed}\0{case_id}\0{condition}".encode()).hexdigest()[:12]
    return f"B{digest}"


def render_prompt(shared: str, instruction: str, case: dict[str, Any]) -> str:
    serialized = json.dumps(case, indent=2, ensure_ascii=False, sort_keys=True)
    return f"{shared}\n\nCondition instructions:\n{instruction}\n\nBenchmark case:\n```json\n{serialized}\n```\n"


def prepare(root: Path, run_dir: Path, seed: str) -> dict[str, Any]:
    summary = validate_repository(root)
    cases = load_cases(root)
    prompts = read_json(root / "evals" / "prompts" / "conditions.json")
    records: list[dict[str, Any]] = []
    for case in cases:
        for condition in CONDITIONS:
            run_id = f"{case['id']}.{condition}"
            records.append({
                "schema_version": SCHEMA_VERSION,
                "run_id": run_id,
                "blind_id": blind_id(seed, case["id"], condition),
                "case_id": case["id"],
                "domain": case["domain"],
                "condition": condition,
                "prompt": render_prompt(prompts["shared_task"], prompts["conditions"][condition]["instruction"], case),
            })
    rng = random.Random(seed)
    rng.shuffle(records)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "benchmark": "business-framing-v2",
        "seed": seed,
        "status": "prepared_not_generated",
        "expected_generations": len(records),
        "records": records,
    }
    write_json(run_dir / "private-manifest.json", manifest)
    for domain in DOMAINS:
        for condition in CONDITIONS:
            packet = [record for record in records if record["domain"] == domain and record["condition"] == condition]
            write_jsonl(run_dir / "generator-packets" / domain.lower() / f"{condition}.jsonl", packet)
    (run_dir / "outputs").mkdir(parents=True, exist_ok=True)
    (run_dir / "scores").mkdir(parents=True, exist_ok=True)
    write_json(run_dir / "run-status.json", {
        **summary,
        "status": "prepared_not_generated",
        "seed": seed,
        "manifest": "private-manifest.json",
        "warning": "Condition mapping is private to orchestration. Do not give private-manifest.json to judges.",
    })
    return {"run_dir": str(run_dir), "packets": 9, "records": len(records), "seed": seed}


def load_json_files(directory: Path) -> list[tuple[Path, dict[str, Any]]]:
    if not directory.exists():
        raise EvaluationError(f"Directory does not exist: {directory}")
    return [(path, read_json(path)) for path in sorted(directory.glob("*.json"))]


def create_judge_packets(root: Path, manifest_path: Path, outputs_dir: Path, packet_dir: Path, allow_partial: bool) -> dict[str, Any]:
    manifest = read_json(manifest_path)
    rubric = load_rubric(root)
    cases = {case["id"]: case for case in load_cases(root)}
    by_blind = {record["blind_id"]: record for record in manifest["records"]}
    outputs = load_json_files(outputs_dir)
    seen: set[str] = set()
    packets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for path, output in outputs:
        validate_with_jsonschema(output, root / "evals" / "schemas" / "output.schema.json", str(path))
        blind = output["blind_id"]
        if blind in seen:
            raise EvaluationError(f"Duplicate output blind ID: {blind}")
        if blind not in by_blind:
            raise EvaluationError(f"Output has unknown blind ID: {blind}")
        record = by_blind[blind]
        if output["case_id"] != record["case_id"] or output["run_id"] != record["run_id"]:
            raise EvaluationError(f"Output identity mismatch in {path}")
        seen.add(blind)
        packets[record["domain"]].append({
            "schema_version": SCHEMA_VERSION,
            "blind_id": blind,
            "case": cases[record["case_id"]],
            "response": output["response"],
            "rubric": rubric,
            "judge_instruction": "Score independently. Do not infer the generation condition. Return one score JSON matching evals/schemas/score.schema.json.",
        })
    missing = set(by_blind) - seen
    if missing and not allow_partial:
        raise EvaluationError(f"Missing {len(missing)} of {len(by_blind)} outputs; use --allow-partial only for debugging")
    judge_ids = ("judge_a", "judge_b")
    for domain in DOMAINS:
        for judge_id in judge_ids:
            judge_records = []
            for record in packets[domain]:
                copied = dict(record)
                copied["judge_id"] = judge_id
                copied["judge_instruction"] = (
                    "Score independently without inferring the generation condition. "
                    f"Set judge_id to {judge_id!r} and return one JSON object matching "
                    "evals/schemas/score.schema.json."
                )
                judge_records.append(copied)
            rng = random.Random(f"{manifest['seed']}\0{judge_id}\0{domain}")
            rng.shuffle(judge_records)
            write_jsonl(packet_dir / f"{domain.lower()}.{judge_id}.jsonl", judge_records)
    return {"outputs": len(seen), "missing": len(missing), "judge_packets": len(DOMAINS) * len(judge_ids)}


def normalize_score(score: dict[str, Any], rubric: dict[str, Any], label: str) -> dict[str, Any]:
    expected = {category["id"]: category["weight"] for category in rubric["categories"]}
    supplied = score.get("category_scores", {})
    if set(supplied) != set(expected):
        raise EvaluationError(f"{label}: category keys do not match rubric")
    for category, value in supplied.items():
        if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= expected[category]:
            raise EvaluationError(f"{label}: {category} score {value!r} is outside 0..{expected[category]}")
    valid_failures = {failure["id"] for failure in rubric["hard_failures"]}
    failures = score.get("hard_failures", [])
    if not set(failures) <= valid_failures:
        raise EvaluationError(f"{label}: unknown hard failure {set(failures) - valid_failures}")
    raw = sum(supplied.values())
    capped = min(raw, rubric["hard_failure_cap"]) if failures else raw
    minima_pass = all(
        supplied[category["id"]] >= category["minimum"]
        for category in rubric["categories"]
    )
    passed = capped >= rubric["passing_score"] and minima_pass and not failures
    if score.get("raw_total") != raw or score.get("capped_total") != capped or score.get("pass") != passed:
        raise EvaluationError(f"{label}: reported totals/pass do not reconcile; expected raw={raw}, capped={capped}, pass={passed}")
    if score.get("rubric_version") != rubric["version"]:
        raise EvaluationError(f"{label}: rubric version mismatch")
    return score


def mean(values: list[int]) -> float | None:
    return round(statistics.fmean(values), 3) if values else None


def correlation(xs: list[int], ys: list[int]) -> float | None:
    if len(xs) < 2 or len(xs) != len(ys):
        return None
    mean_x, mean_y = statistics.fmean(xs), statistics.fmean(ys)
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    denominator = (
        sum((x - mean_x) ** 2 for x in xs) * sum((y - mean_y) ** 2 for y in ys)
    ) ** 0.5
    return round(numerator / denominator, 3) if denominator else None


def reconcile_scores(primary: list[dict[str, Any]], adjudicator: dict[str, Any] | None, rubric: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    categories = {item["id"]: item for item in rubric["categories"]}
    first, second = primary
    material_dimension_difference = any(
        abs(first["category_scores"][key] - second["category_scores"][key]) > 0.2 * details["weight"]
        for key, details in categories.items()
    )
    hard_failure_disagreement = set(first["hard_failures"]) != set(second["hard_failures"])
    needs_adjudication = material_dimension_difference or hard_failure_disagreement
    if needs_adjudication and adjudicator is None:
        raise EvaluationError("A third adjudicator is required for material or hard-failure disagreement")
    judges = primary + ([adjudicator] if adjudicator is not None and needs_adjudication else [])
    category_scores = {
        key: round(statistics.median(score["category_scores"][key] for score in judges))
        for key in categories
    }
    if hard_failure_disagreement and adjudicator is not None:
        failures = adjudicator["hard_failures"]
    else:
        failures = first["hard_failures"] if set(first["hard_failures"]) == set(second["hard_failures"]) else []
    raw = sum(category_scores.values())
    capped = min(raw, rubric["hard_failure_cap"]) if failures else raw
    minima_pass = all(category_scores[key] >= details["minimum"] for key, details in categories.items())
    return ({
        "category_scores": category_scores,
        "hard_failures": failures,
        "raw_total": raw,
        "capped_total": capped,
        "pass": capped >= rubric["passing_score"] and minima_pass and not failures,
    }, needs_adjudication)


def aggregate(root: Path, manifest_path: Path, scores_dir: Path, output_dir: Path, allow_partial: bool) -> dict[str, Any]:
    manifest = read_json(manifest_path)
    rubric = load_rubric(root)
    mapping = {record["blind_id"]: record for record in manifest["records"]}
    score_files = load_json_files(scores_dir)
    score_groups: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for path, score in score_files:
        validate_with_jsonschema(score, root / "evals" / "schemas" / "score.schema.json", str(path))
        blind = score["blind_id"]
        if blind not in mapping:
            raise EvaluationError(f"Score has unknown blind ID: {blind}")
        judge_id = score["judge_id"]
        if judge_id in score_groups[blind]:
            raise EvaluationError(f"Duplicate {judge_id} score for blind ID {blind}")
        score_groups[blind][judge_id] = normalize_score(score, rubric, str(path))

    missing_primary: list[str] = []
    combined: dict[str, dict[str, Any]] = {}
    adjudicated = 0
    primary_pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for blind in mapping:
        group = score_groups.get(blind, {})
        if "judge_a" not in group or "judge_b" not in group:
            missing_primary.append(blind)
            continue
        primary = [group["judge_a"], group["judge_b"]]
        primary_pairs.append((primary[0], primary[1]))
        try:
            combined[blind], required = reconcile_scores(primary, group.get("adjudicator"), rubric)
        except EvaluationError:
            if allow_partial:
                missing_primary.append(blind)
                continue
            raise EvaluationError(f"{blind}: third adjudicator required by disagreement rule")
        adjudicated += int(required)
    if missing_primary and not allow_partial:
        raise EvaluationError(
            f"Missing complete two-judge coverage for {len(missing_primary)} of {len(mapping)} outputs"
        )

    categories = [category["id"] for category in rubric["categories"]]
    cells: dict[str, dict[str, Any]] = {}
    for domain in DOMAINS:
        for condition in CONDITIONS:
            selected = [(blind, score) for blind, score in combined.items() if mapping[blind]["domain"] == domain and mapping[blind]["condition"] == condition]
            key = f"{domain}:{condition}"
            cells[key] = {
                "n": len(selected),
                "mean_raw_total": mean([score["raw_total"] for _, score in selected]),
                "mean_capped_total": mean([score["capped_total"] for _, score in selected]),
                "pass_rate": round(sum(score["pass"] for _, score in selected) / len(selected), 3) if selected else None,
                "hard_failure_rate": round(sum(bool(score["hard_failures"]) for _, score in selected) / len(selected), 3) if selected else None,
                "category_means": {category: mean([score["category_scores"][category] for _, score in selected]) for category in categories},
            }

    paired: list[dict[str, Any]] = []
    by_case_condition: dict[tuple[str, str], dict[str, Any]] = {}
    for blind, score in combined.items():
        record = mapping[blind]
        by_case_condition[(record["case_id"], record["condition"])] = score
    for case_id in sorted({record["case_id"] for record in mapping.values()}):
        trio = {condition: by_case_condition.get((case_id, condition)) for condition in CONDITIONS}
        if all(trio.values()):
            full = trio["v0_2_0_beta"]["capped_total"]
            paired.append({
                "case_id": case_id,
                "v0_2_minus_no_skill": full - trio["no_skill"]["capped_total"],
                "v0_2_minus_v0_1": full - trio["v0_1_0_alpha"]["capped_total"],
                "hard_failures": {condition: trio[condition]["hard_failures"] for condition in CONDITIONS},
            })

    hard_agreements = [set(a["hard_failures"]) == set(b["hard_failures"]) for a, b in primary_pairs]
    category_mad = {
        category: round(statistics.fmean(abs(a["category_scores"][category] - b["category_scores"][category]) for a, b in primary_pairs), 3)
        if primary_pairs else None
        for category in categories
    }
    status = "complete" if not missing_primary else "partial_not_publishable"
    report = {
        "schema_version": SCHEMA_VERSION,
        "benchmark": manifest["benchmark"],
        "seed": manifest["seed"],
        "status": status,
        "expected_primary_scores": len(mapping) * 2,
        "received_primary_scores": sum("judge_a" in group for group in score_groups.values()) + sum("judge_b" in group for group in score_groups.values()),
        "missing_output_pairs": len(missing_primary),
        "adjudicated_outputs": adjudicated,
        "rubric_version": rubric["version"],
        "cells": cells,
        "paired_case_comparisons": paired,
        "inter_judge_agreement": {
            "mean_absolute_category_differences": category_mad,
            "total_score_correlation": correlation(
                [a["raw_total"] for a, _ in primary_pairs],
                [b["raw_total"] for _, b in primary_pairs],
            ),
            "hard_failure_agreement": round(sum(hard_agreements) / len(hard_agreements), 3) if hard_agreements else None,
        },
        "limitations": [
            "Language-model generation and judging are nondeterministic even when prompts and seeds are fixed.",
            "A same-family or same-model judge may favor familiar response patterns.",
            "Residual condition contamination may remain despite blind IDs; judges can infer styles.",
            "This benchmark measures framing quality on synthetic cases, not downstream business outcomes."
        ]
    }
    write_json(output_dir / "summary.json", report)
    (output_dir / "summary.md").write_text(render_markdown(report), encoding="utf-8", newline="\n")
    return {"status": status, "primary_scores": report["received_primary_scores"], "missing_pairs": len(missing_primary), "paired_cases": len(paired)}


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Benchmark evaluation summary",
        "",
        f"Status: **{report['status']}**. Received {report['received_primary_scores']} of {report['expected_primary_scores']} primary blinded scores.",
        "",
        "| Domain | Condition | n | Mean raw | Mean capped | Pass rate | Hard-failure rate |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for domain in DOMAINS:
        for condition in CONDITIONS:
            cell = report["cells"][f"{domain}:{condition}"]
            display = lambda value: "pending" if value is None else str(value)
            lines.append(f"| {domain} | {condition} | {cell['n']} | {display(cell['mean_raw_total'])} | {display(cell['mean_capped_total'])} | {display(cell['pass_rate'])} | {display(cell['hard_failure_rate'])} |")
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in report["limitations"])
    lines.extend(["", "Paired case deltas are available in `summary.json`; no absent score is imputed.", ""])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=repo_root_from_script(), help="Repository root")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate", help="Validate committed schemas, cases, prompts, and rubric")
    sub.add_parser("validate-artifacts", help="Validate complete committed v0.2 prompts, outputs, mappings, and two-judge scores")
    prep = sub.add_parser("prepare", help="Create deterministic per-domain/per-condition generator packets")
    prep.add_argument("--run-dir", type=Path, required=True)
    prep.add_argument("--seed", default="v0.2.0-beta")
    judge = sub.add_parser("judge-packets", help="Create condition-blind domain packets from generated outputs")
    judge.add_argument("--manifest", type=Path, required=True)
    judge.add_argument("--outputs-dir", type=Path, required=True)
    judge.add_argument("--packet-dir", type=Path, required=True)
    judge.add_argument("--allow-partial", action="store_true")
    agg = sub.add_parser("aggregate", help="Validate, unblind, and aggregate externally produced score JSON")
    agg.add_argument("--manifest", type=Path, required=True)
    agg.add_argument("--scores-dir", type=Path, required=True)
    agg.add_argument("--output-dir", type=Path, required=True)
    agg.add_argument("--allow-partial", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    try:
        if args.command == "validate":
            result = validate_repository(root)
        elif args.command == "validate-artifacts":
            result = validate_committed_artifacts(root)
        elif args.command == "prepare":
            result = prepare(root, args.run_dir.resolve(), args.seed)
        elif args.command == "judge-packets":
            result = create_judge_packets(root, args.manifest.resolve(), args.outputs_dir.resolve(), args.packet_dir.resolve(), args.allow_partial)
        else:
            result = aggregate(root, args.manifest.resolve(), args.scores_dir.resolve(), args.output_dir.resolve(), args.allow_partial)
    except EvaluationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
