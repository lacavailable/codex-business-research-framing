#!/usr/bin/env python3
"""Deterministic development checks for the bounded Skill 2.2 canary.

This module intentionally contains no generation, judging, freezing, or
holdout access.  It only validates the public canary configuration and scores
rendered text against its task-local audit record.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CANARY = ROOT / "evals" / "skill-2.2-canary"
TASKS = CANARY / "tasks" / "generator-visible.json"
AUDIT = CANARY / "tasks" / "audit-only.json"
PREREG = CANARY / "preregistration.json"
MANIFEST = CANARY / "runs" / "call-manifest.json"

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
