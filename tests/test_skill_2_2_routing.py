from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from conftest import ROOT, import_file


SKILL = ROOT / "skills" / "frame-business-research-problem"
CANARY = ROOT / "evals" / "skill-2.2-canary"


def skill_text(relative: str) -> str:
    return (SKILL / relative).read_text(encoding="utf-8")


def v2_tool():
    path = ROOT / "tools" / "skill_canary_v2.py"
    assert path.is_file(), "Skill 2.2 canary tool has not been implemented"
    return import_file("skill_canary_v2_test", path)


def git_object(spec: str) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", spec], cwd=ROOT, text=True
    ).strip()


def test_historical_skill_2_1_artifacts_are_bit_preserved() -> None:
    assert git_object("HEAD:evals/skill-2.1-canary") == "58bee74d88d09a0ad2913453a449f887e6a3e9d6"
    assert git_object("HEAD:tools/skill_canary.py") == "fe417b7e20284868f69a62459ffe3752c7dd4366"
    assert git_object("HEAD:docs/skill-2.1-direct-experimental-results.md") == "e9cbcaed6ac55b91946ce86b5082e92fc292dc40"
    assert git_object("HEAD:tests/test_skill_2_1_experimental.py") == "9fbdb9eccf298dc3c04f80b7c5c2ce0879a07b17"
    old_result = json.loads(
        (ROOT / "evals/skill-2.1-canary/results/canary-result.json").read_text(
            encoding="utf-8"
        )
    )
    assert old_result["status"] == "fail"
    assert old_result["experimental_merge_authorized"] is False


def test_ceiling_first_profile_precedence_is_explicit() -> None:
    skill = skill_text("SKILL.md")
    profiles = skill_text("references/response-profiles.md")
    combined = f"{skill}\n{profiles}".casefold()
    for phrase in (
        "explicit user length",
        "hard ceiling",
        "never pad",
        "final render",
        "single visible home",
    ):
        assert phrase in combined
    assert "120–220 words" not in profiles
    assert "250–500 words" not in profiles


def test_compact_and_standard_have_executable_render_limits() -> None:
    profiles = skill_text("references/response-profiles.md").casefold()
    assert "compact" in profiles and "160 words" in profiles
    assert "standard" in profiles and "450 words" in profiles
    assert "no headings" in profiles
    assert "check the rendered answer" in profiles


def test_output_contract_assigns_each_issue_one_visible_home() -> None:
    contracts = skill_text("references/output-contracts.md").casefold()
    assert "single visible home" in contracts
    assert "material contradiction" in contracts
    assert "evidence gap" in contracts
    assert "principal boundary" in contracts
    assert "schema compatibility" in contracts


def test_new_canary_static_contract_and_exact_budget() -> None:
    tool = v2_tool()
    tool.validate_static()
    visible, audit = tool.task_maps()
    assert len(visible) == len(audit) == 4
    manifest = json.loads(
        (CANARY / "runs/call-manifest.json").read_text(encoding="utf-8")
    )
    assert len(manifest["calls"]) == 12
    assert sum(call["role"] == "generation" for call in manifest["calls"]) == 8
    assert sum(
        call["role"] == "blind_pairwise_judge" for call in manifest["calls"]
    ) == 4


def test_empirical_detector_ignores_structural_numbers() -> None:
    tool = v2_tool()
    audit = {
        "supplied_empirical_numbers": [],
        "unsupported_empirical_patterns": [],
    }
    text = (
        "BusinessBrief 2.0 retains DFC-12. Stage 2 reports all six gates. "
        "Section 3 uses schema version 1.0."
    )
    assert tool.unsupported_empirical_facts(text, audit) == []


def test_empirical_detector_allows_supplied_quantities_and_flags_new_ones() -> None:
    tool = v2_tool()
    audit = {
        "supplied_empirical_numbers": ["42%", "15 minutes"],
        "unsupported_empirical_patterns": ["most firms"],
    }
    supplied = "Runtime was 42% faster, and the route is committed by 15 minutes."
    assert tool.unsupported_empirical_facts(supplied, audit) == []
    flagged = tool.unsupported_empirical_facts(
        supplied + " The method raises profit by 17% for most firms.", audit
    )
    assert any("17%" in item for item in flagged)
    assert any("most firms" in item.casefold() for item in flagged)


def test_repetition_detector_counts_limitation_units_not_topic_mentions() -> None:
    tool = v2_tool()
    audit = {
        "limitation_families": {
            "profit": [
                r"(?:runtime|faster).{0,50}(?:does not|cannot).{0,30}profit"
            ]
        }
    }
    necessary_topic_use = (
        "Runtime is lower on the tested cases. Faster computation does not by "
        "itself establish profit."
    )
    assert tool.duplicate_limitation_units(necessary_topic_use, audit) == 0
    repeated = (
        "Faster runtime does not establish profit.\n\n"
        "Boundary: runtime cannot establish profit without field evidence."
    )
    assert tool.duplicate_limitation_units(repeated, audit) == 1


@pytest.mark.parametrize(
    ("text", "constraints", "expected"),
    [
        (
            "one two three four five",
            {
                "minimum_words": None,
                "maximum_words": 5,
                "maximum_headings": 0,
                "maximum_visible_blocks": 1,
            },
            True,
        ),
        (
            "one two three four five six",
            {
                "minimum_words": None,
                "maximum_words": 5,
                "maximum_headings": 0,
                "maximum_visible_blocks": 1,
            },
            False,
        ),
        (
            "# Heading\n\nshort prose",
            {
                "minimum_words": None,
                "maximum_words": 20,
                "maximum_headings": 0,
                "maximum_visible_blocks": 1,
            },
            False,
        ),
    ],
)
def test_profile_compliance_uses_task_specific_constraints(
    text: str, constraints: dict[str, int | None], expected: bool
) -> None:
    tool = v2_tool()
    assert tool.profile_compliant(text, constraints) is expected


def test_usable_answer_first_checks_the_first_visible_block() -> None:
    tool = v2_tool()
    audit = {"answer_first_patterns": ["hospital", "schedul"]}
    assert tool.usable_answer_first(
        "A hospital schedules nurses before arrivals.\n\nBoundary: demand is uncertain.",
        audit,
    )
    assert not tool.usable_answer_first(
        "Readiness is incomplete.\n\nA hospital schedules nurses before arrivals.",
        audit,
    )

