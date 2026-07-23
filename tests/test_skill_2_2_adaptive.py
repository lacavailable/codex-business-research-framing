from __future__ import annotations

import json
import subprocess
from pathlib import Path

from conftest import ROOT, import_file


SKILL = ROOT / "skills" / "frame-business-research-problem"
CANARY = ROOT / "evals" / "skill-2.2-canary"
PR7 = "323ea17b8f98059b71801b6a1bf9241188be4fee"


def text(relative: str) -> str:
    return (SKILL / relative).read_text(encoding="utf-8")


def test_adaptive_profiles_and_deliverable_first_routing() -> None:
    skill = text("SKILL.md")
    profiles = text("references/response-profiles.md")
    adaptive = text("references/adaptive-output.md")
    for profile in ("micro", "compact", "standard", "full-audit"):
        assert f"`{profile}`" in skill or f"## {profile.title()}" in profiles
    assert "35–100 words" in profiles and "Soft maximum: 120 words" in profiles
    assert "80–180 words" in profiles and "Soft maximum: 220 words" in profiles
    assert "180–450 words" in profiles and "Soft maximum: 500 words" in profiles
    assert "never pad" in profiles
    assert "Select the requested deliverable before selecting a profile" in skill
    assert "Use `full-audit` only when explicitly requested" in skill
    for deliverable in (
        "interview answer", "manuscript-ready paragraph", "introduction opening",
        "business-problem statement", "model-setting explanation",
        "research-question formulation", "contribution paragraph",
        "managerial implication", "scenario comparison", "assumption audit",
        "full manuscript audit", "computational-contribution explanation",
        "research proposal framing",
    ):
        assert deliverable in adaptive


def test_minimum_sufficient_table_and_repetition_rules() -> None:
    adaptive = text("references/adaptive-output.md")
    assert all(f"{index}." in adaptive for index in range(1, 8))
    assert "one visible home" in adaptive
    assert "semantically duplicated" in adaptive
    assert "Necessary recurrence of a technical noun" in adaptive
    assert "three or more model objects" in adaptive
    assert "3–8 rows" in adaptive
    assert "Do not remove a\nhigh-value mapping table" in adaptive


def test_status_and_claim_granularity_rules() -> None:
    adaptive = text("references/adaptive-output.md")
    for status in (
        "contradicted", "not_supplied", "not_assessed", "unsupported",
        "not_applicable",
    ):
        assert f"`{status}`" in adaptive
    assert "Keep one scenario singular" in adaptive
    assert "One\nbenchmark does not establish general solver performance" in adaptive
    assert "private objective is not welfare" in adaptive
    assert "Never upgrade `not_supplied` or `not_assessed`" in adaptive


def test_contribution_setting_value_and_clarification_routes() -> None:
    contribution = text("references/contribution-types.md")
    for heading in (
        "Analytical mechanism", "Formulation", "Algorithmic", "Empirical causal",
        "IS design or governance", "Policy or mechanism-design",
    ):
        assert heading in contribution
    setting = text("references/setting-construction.md")
    for classification in (
        "direct_interpretation", "plausible_application",
        "illustrative_analogy", "model_extension",
    ):
        assert f"`{classification}`" in setting
    assert "up to three candidate" in setting
    assert "show only the strongest eligible framing" in setting
    pathway = text("references/managerial-value-pathway.md")
    assert "model result → decision-process effect → operational intermediate outcome → business or social outcome" in pathway
    for label in (
        "model-implied", "logically plausible", "requires operational evidence",
        "requires empirical evidence", "outside current study",
    ):
        assert f"`{label}`" in pathway
    adaptive = text("references/adaptive-output.md")
    assert "Ask no more than three questions" in adaptive
    assert "company name" in adaptive


def test_or_claim_scope_and_overclaim_safeguards() -> None:
    reference = text("references/or-computational-contribution.md")
    for phrase in (
        "Use singular “instance” unless multiple instances are supplied",
        "observed runtime from expected runtime",
        "incumbent feasibility from incumbent quality",
        "later proof from decision-time quality knowledge",
        "post-deadline certificate cannot improve a decision already executed",
        "Do not invent repeated-run robustness",
    ):
        assert phrase in reference
    tool = import_file("skill_adaptive_metrics", ROOT / "tools" / "skill_adaptive_canary.py")
    assert tool.sentence_overclaim("Faster runtime therefore raises profit.", "runtime_to_profit")
    assert not tool.sentence_overclaim("Faster runtime does not establish profit.", "runtime_to_profit")
    assert tool.sentence_overclaim(
        "The post-deadline certificate improves the completed decision.",
        "post_deadline_value",
    )
    assert not tool.sentence_overclaim(
        "The post-deadline certificate cannot improve the completed decision.",
        "post_deadline_value",
    )


def test_original_examples_cover_all_thirteen_requirements() -> None:
    examples = text("references/original-examples.md")
    for number in range(1, 14):
        assert f"## {number}." in examples
    for phrase in (
        "Micro versus compact versus standard",
        "below its typical range", "Standard mapping where a table is better",
        "Explicit mismatch is contradicted", "Missing information is not supplied",
        "One scenario remains singular", "One benchmark cannot be generalized",
        "Three internal settings", "Computational value pathway",
        "Contribution-type routing", "Concise full audit",
        "Clarification is necessary", "Clarification should not be asked",
    ):
        assert phrase in examples


def test_businessbrief_and_agent_metadata_compatibility() -> None:
    tool = import_file("adaptive_canary_hashes", ROOT / "tools" / "skill_adaptive_canary.py")
    assert tool.hash_file(SKILL / "scripts" / "validate_brief.py") == "e238906e3a1861a75327348194f52898482ec0d59d3d311daa6f7f3b356eaecc"
    assert tool.hash_file(SKILL / "agents" / "openai.yaml") == "3d747031fadb49b13236da80f16b6de40f1b342d61116b8fbaac443b113ef213"
    schema = text("references/business-brief-schema.md")
    assert "version `1.0`" in schema and "version `2.0`" in schema


def test_canary_freeze_budget_metrics_and_historical_preservation() -> None:
    tool = import_file("adaptive_canary_static", ROOT / "tools" / "skill_adaptive_canary.py")
    tool.validate_freeze()
    manifest = json.loads((CANARY / "runs/call-manifest.json").read_text(encoding="utf-8"))
    assert manifest["maximum_authoritative_calls"] == 16
    assert manifest["baseline_generation_calls"] == 0
    assert sum(call["role"] == "generation" for call in manifest["calls"]) == 8
    assert sum(call["role"] == "blind_pairwise_judge" for call in manifest["calls"]) == 8
    assert len(json.loads((CANARY / "preregistration.json").read_text(encoding="utf-8"))["acceptance_rules"]) == 14
    metrics = json.loads((CANARY / "metric-definitions.json").read_text(encoding="utf-8"))
    assert "schema version" in metrics["unsupported_factual_claim"]["excluded"]
    assert metrics["nonapplicable_layers"]["absolute_candidate_requirement"] == 0
    for spec in (
        "evals/skill-2.1-canary",
        "tools/skill_canary.py",
        "docs/skill-2.1-direct-experimental-results.md",
    ):
        old = subprocess.check_output(["git", "rev-parse", f"{PR7}:{spec}"], cwd=ROOT, text=True).strip()
        current = subprocess.check_output(["git", "rev-parse", f"HEAD:{spec}"], cwd=ROOT, text=True).strip()
        assert old == current


def test_product_canary_artifacts_when_complete() -> None:
    if not (CANARY / "results/canary-result.json").exists():
        return
    tool = import_file("adaptive_canary_complete", ROOT / "tools" / "skill_adaptive_canary.py")
    assert len(list((CANARY / "outputs").glob("GEN-*.json"))) == 8
    assert len(list((CANARY / "blinded-pairs").glob("PAIR-*.json"))) == 8
    assert len(list((CANARY / "judgments").glob("JUDGE-*.json"))) == 8
    for path in (CANARY / "outputs").glob("GEN-*.json"):
        tool.validate_schema(json.loads(path.read_text(encoding="utf-8")), "generation-result.schema.json")
    for path in (CANARY / "judgments").glob("JUDGE-*.json"):
        tool.validate_schema(json.loads(path.read_text(encoding="utf-8")), "judge-result.schema.json")
    assert (CANARY / "user-acceptance/review-form.md").is_file()
    assert not (CANARY / "user-acceptance/condition-key.json").exists()
    result = json.loads((CANARY / "results/canary-result.json").read_text(encoding="utf-8"))
    assert result["authoritative_calls_used"] == 16
    assert result["baseline_generation_calls"] == 0
    assert result["retries"] == result["replacements"] == result["adjudications"] == 0
    assert result["automated_holdout_opened"] is False
    assert result["expert_holdout_opened"] is False
    assert result["no_human_experts"] is True


def test_no_holdout_or_condition_key_is_tracked_in_new_canary() -> None:
    paths = [path.relative_to(CANARY).as_posix().casefold() for path in CANARY.rglob("*")]
    assert not any("holdout" in path for path in paths)
    assert not any("condition-key" in path for path in paths)
