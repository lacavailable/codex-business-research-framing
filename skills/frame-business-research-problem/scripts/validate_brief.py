#!/usr/bin/env python3
"""Validate a frame-business-research-problem BusinessBrief JSON document."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.0"
MODES = {
    "create",
    "diagnose",
    "rewrite",
    "compare-scenarios",
    "map-model-to-business",
    "audit-assumptions",
    "draft-introduction",
    "draft-managerial-implications",
}
DOMAINS = {"OM", "IS", "OR", "cross-domain"}
DFC_FIELDS = {
    "actor",
    "trigger",
    "choices",
    "decision_time_information",
    "stakes",
    "frictions",
    "mechanism",
    "trade_off",
    "counterfactual",
    "model_mapping_summary",
    "evidence_status_summary",
    "boundaries_summary",
}
GATES = {"actor", "timing", "information", "behavior", "constraints", "objective"}
MODEL_ROLES = {
    "decision",
    "state",
    "parameter",
    "random_variable",
    "observation",
    "constraint",
    "objective",
    "outcome",
    "derived_quantity",
}
EVIDENCE_LABELS = {
    "empirical_fact",
    "model_assumption",
    "simplifying_assumption",
    "inference",
    "unsupported_claim",
}
MODE_KEYS = {
    "create": {"business_problem"},
    "diagnose": {"verdict", "failed_gates", "repairs"},
    "rewrite": {"rewritten_text", "fidelity_changes"},
    "compare-scenarios": {"scenarios", "ranking_basis"},
    "map-model-to-business": {"mapping_table", "mapping_gaps"},
    "audit-assumptions": {"assumptions", "material_risks"},
    "draft-introduction": {"introduction", "claim_checklist"},
    "draft-managerial-implications": {"implications", "qualification_checklist"},
}
TOP_LEVEL_FIELDS = {
    "schema_version",
    "mode",
    "title",
    "domain",
    "model_supplied",
    "diagnosis_or_brief",
    "narrative",
    "decision_structure",
    "consistency_gates",
    "eligible",
    "model_mapping",
    "claims",
    "boundaries",
    "primary_remaining_weakness",
    "mode_result",
}


class BriefValidator:
    """Accumulate stable, path-qualified validation errors."""

    def __init__(self) -> None:
        self.errors: list[str] = []

    def error(self, path: str, message: str) -> None:
        self.errors.append(f"{path}: {message}")

    def require_object(self, value: Any, path: str) -> dict[str, Any] | None:
        if not isinstance(value, dict):
            self.error(path, "must be an object")
            return None
        return value

    def require_array(self, value: Any, path: str) -> list[Any] | None:
        if not isinstance(value, list):
            self.error(path, "must be an array")
            return None
        return value

    def require_text(self, value: Any, path: str) -> None:
        if not isinstance(value, str) or not value.strip():
            self.error(path, "must be a nonempty string")

    def require_keys(self, obj: dict[str, Any], keys: set[str], path: str) -> None:
        for key in sorted(keys - obj.keys()):
            self.error(f"{path}.{key}", "is required")

    def validate(self, data: Any) -> list[str]:
        root = self.require_object(data, "$")
        if root is None:
            return self.errors

        self.require_keys(root, TOP_LEVEL_FIELDS, "$")
        if root.get("schema_version") != SCHEMA_VERSION:
            self.error("$.schema_version", f"must equal {SCHEMA_VERSION!r}")

        mode = root.get("mode")
        if mode not in MODES:
            self.error("$.mode", f"must be one of {sorted(MODES)}")
        if root.get("domain") not in DOMAINS:
            self.error("$.domain", f"must be one of {sorted(DOMAINS)}")
        if not isinstance(root.get("model_supplied"), bool):
            self.error("$.model_supplied", "must be a boolean")
        if not isinstance(root.get("eligible"), bool):
            self.error("$.eligible", "must be a boolean")

        for field in ("title", "diagnosis_or_brief", "narrative", "primary_remaining_weakness"):
            self.require_text(root.get(field), f"$.{field}")

        self.validate_decision_structure(root.get("decision_structure"))
        all_gates_pass = self.validate_gates(root.get("consistency_gates"))
        if isinstance(root.get("eligible"), bool) and all_gates_pass is not None:
            if root["eligible"] != all_gates_pass:
                self.error("$.eligible", "must be true exactly when all six gates pass")

        mapping = self.validate_mapping(root.get("model_mapping"), "$.model_mapping")
        if root.get("model_supplied") is True and mapping is not None and not mapping:
            self.error("$.model_mapping", "must be nonempty when model_supplied is true")

        self.validate_claims(root.get("claims"))
        boundaries = self.require_array(root.get("boundaries"), "$.boundaries")
        if boundaries is not None:
            if not boundaries:
                self.error("$.boundaries", "must contain at least one boundary")
            for index, boundary in enumerate(boundaries):
                self.require_text(boundary, f"$.boundaries[{index}]")

        self.validate_mode_result(mode, root.get("mode_result"))
        return sorted(set(self.errors))

    def validate_decision_structure(self, value: Any) -> None:
        obj = self.require_object(value, "$.decision_structure")
        if obj is None:
            return
        self.require_keys(obj, DFC_FIELDS, "$.decision_structure")
        for field in sorted(DFC_FIELDS & obj.keys()):
            self.require_text(obj[field], f"$.decision_structure.{field}")

    def validate_gates(self, value: Any) -> bool | None:
        obj = self.require_object(value, "$.consistency_gates")
        if obj is None:
            return None
        self.require_keys(obj, GATES, "$.consistency_gates")
        statuses: list[bool] = []
        for gate in sorted(GATES & obj.keys()):
            path = f"$.consistency_gates.{gate}"
            record = self.require_object(obj[gate], path)
            if record is None:
                continue
            self.require_keys(record, {"status", "reason"}, path)
            status = record.get("status")
            if status not in {"pass", "fail"}:
                self.error(f"{path}.status", "must be 'pass' or 'fail'")
            else:
                statuses.append(status == "pass")
            self.require_text(record.get("reason"), f"{path}.reason")
        return all(statuses) if len(statuses) == len(GATES) else None

    def validate_mapping(self, value: Any, path: str) -> list[Any] | None:
        rows = self.require_array(value, path)
        if rows is None:
            return None
        fields = {"model_object", "model_role", "business_meaning", "decision_time_status", "fidelity_note"}
        for index, item in enumerate(rows):
            item_path = f"{path}[{index}]"
            row = self.require_object(item, item_path)
            if row is None:
                continue
            self.require_keys(row, fields, item_path)
            for field in sorted(fields - {"model_role"}):
                self.require_text(row.get(field), f"{item_path}.{field}")
            if row.get("model_role") not in MODEL_ROLES:
                self.error(f"{item_path}.model_role", f"must be one of {sorted(MODEL_ROLES)}")
        return rows

    def validate_claims(self, value: Any) -> None:
        claims = self.require_array(value, "$.claims")
        if claims is None:
            return
        fields = {"statement", "evidence_status", "source", "action"}
        for index, item in enumerate(claims):
            path = f"$.claims[{index}]"
            claim = self.require_object(item, path)
            if claim is None:
                continue
            self.require_keys(claim, fields, path)
            self.require_text(claim.get("statement"), f"{path}.statement")
            self.require_text(claim.get("action"), f"{path}.action")
            if claim.get("evidence_status") not in EVIDENCE_LABELS:
                self.error(f"{path}.evidence_status", f"must be one of {sorted(EVIDENCE_LABELS)}")
            source = claim.get("source")
            if source is not None and (not isinstance(source, str) or not source.strip()):
                self.error(f"{path}.source", "must be null or a nonempty string")
            if claim.get("evidence_status") == "empirical_fact" and source is None:
                self.error(f"{path}.source", "is required for empirical_fact")

    def validate_mode_result(self, mode: Any, value: Any) -> None:
        result = self.require_object(value, "$.mode_result")
        if result is None or mode not in MODE_KEYS:
            return
        self.require_keys(result, MODE_KEYS[mode], "$.mode_result")
        text_fields = {
            "create": {"business_problem"},
            "diagnose": {"verdict"},
            "rewrite": {"rewritten_text"},
            "draft-introduction": {"introduction"},
            "draft-managerial-implications": {"implications"},
        }
        list_fields = {
            "diagnose": {"failed_gates", "repairs"},
            "rewrite": {"fidelity_changes"},
            "map-model-to-business": {"mapping_table", "mapping_gaps"},
            "audit-assumptions": {"assumptions", "material_risks"},
            "draft-introduction": {"claim_checklist"},
            "draft-managerial-implications": {"qualification_checklist"},
        }
        for field in text_fields.get(mode, set()):
            self.require_text(result.get(field), f"$.mode_result.{field}")
        for field in list_fields.get(mode, set()):
            self.require_array(result.get(field), f"$.mode_result.{field}")
        if mode == "diagnose" and result.get("verdict") not in {"eligible", "ineligible"}:
            self.error("$.mode_result.verdict", "must be 'eligible' or 'ineligible'")
        if mode == "compare-scenarios":
            self.validate_scenarios(result.get("scenarios"))
            self.require_text(result.get("ranking_basis"), "$.mode_result.ranking_basis")

    def validate_scenarios(self, value: Any) -> None:
        scenarios = self.require_array(value, "$.mode_result.scenarios")
        if scenarios is None:
            return
        fields = {
            "name",
            "eligible",
            "failed_gates",
            "model_fit",
            "managerial_relevance",
            "evidence_plausibility",
            "boundary_transparency",
            "rank",
        }
        ranks: list[int] = []
        for index, item in enumerate(scenarios):
            path = f"$.mode_result.scenarios[{index}]"
            scenario = self.require_object(item, path)
            if scenario is None:
                continue
            self.require_keys(scenario, fields, path)
            self.require_text(scenario.get("name"), f"{path}.name")
            eligible = scenario.get("eligible")
            if not isinstance(eligible, bool):
                self.error(f"{path}.eligible", "must be a boolean")
            failed = self.require_array(scenario.get("failed_gates"), f"{path}.failed_gates")
            if failed is not None:
                invalid = [gate for gate in failed if gate not in GATES]
                if invalid:
                    self.error(f"{path}.failed_gates", f"contains invalid gates {invalid}")
                if eligible is True and failed:
                    self.error(f"{path}.failed_gates", "must be empty for an eligible scenario")
                if eligible is False and not failed:
                    self.error(f"{path}.failed_gates", "must be nonempty for an ineligible scenario")
            for field in ("model_fit", "managerial_relevance", "evidence_plausibility", "boundary_transparency"):
                score = scenario.get(field)
                if not isinstance(score, (int, float)) or isinstance(score, bool) or not 0 <= score <= 100:
                    self.error(f"{path}.{field}", "must be a number from 0 to 100")
            rank = scenario.get("rank")
            if eligible is True:
                if not isinstance(rank, int) or isinstance(rank, bool) or rank < 1:
                    self.error(f"{path}.rank", "must be a positive integer for an eligible scenario")
                else:
                    ranks.append(rank)
            elif eligible is False and rank is not None:
                self.error(f"{path}.rank", "must be null for an ineligible scenario")
        if ranks and sorted(ranks) != list(range(1, len(ranks) + 1)):
            self.error("$.mode_result.scenarios", "eligible ranks must be unique and contiguous from 1")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("brief", type=Path, help="Path to a BusinessBrief JSON file")
    parser.add_argument("--json", action="store_true", help="Emit the validation result as JSON")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        with args.brief.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors = [f"$: cannot read valid UTF-8 JSON: {exc}"]
    else:
        errors = BriefValidator().validate(data)

    result = {"valid": not errors, "errors": errors}
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    elif errors:
        print(f"INVALID: {args.brief}")
        for error in errors:
            print(f"- {error}")
    else:
        print(f"VALID: {args.brief}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
