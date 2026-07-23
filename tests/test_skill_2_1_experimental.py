from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from conftest import ROOT, import_file


SKILL = ROOT / "skills" / "frame-business-research-problem"
CANARY = ROOT / "evals" / "skill-2.1-canary"
FROZEN_CANDIDATE_COMMIT = "323ea17b8f98059b71801b6a1bf9241188be4fee"


def text(name: str) -> str:
    return (SKILL / name).read_text(encoding="utf-8")


def canonical_text_sha256(path: Path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def git_bytes(spec: str) -> bytes:
    return subprocess.check_output(["git", "show", spec], cwd=ROOT)


def frozen_skill_text(relative: str) -> str:
    return git_bytes(
        f"{FROZEN_CANDIDATE_COMMIT}:skills/frame-business-research-problem/{relative}"
    ).decode("utf-8")


def frozen_skill_sha256() -> str:
    root = "skills/frame-business-research-problem"
    paths = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", FROZEN_CANDIDATE_COMMIT, "--", root],
        cwd=ROOT,
        text=True,
    ).splitlines()
    digest = hashlib.sha256()
    for path in sorted(paths, key=str.casefold):
        relative = path.removeprefix(f"{root}/")
        data = git_bytes(f"{FROZEN_CANDIDATE_COMMIT}:{path}")
        data = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        digest.update(relative.encode("utf-8") + b"\0")
        digest.update(hashlib.sha256(data).digest())
    return digest.hexdigest()


def test_profile_routing_and_output_first_contract() -> None:
    skill = frozen_skill_text("SKILL.md")
    profiles = frozen_skill_text("references/response-profiles.md")
    assert all(f"`{profile}`" in skill for profile in ("compact", "standard", "full-audit"))
    assert "120–220 words" in profiles
    assert "250–500 words" in profiles
    assert "usable prose" in skill
    assert "Do not default to `full-audit`" in skill


def test_nonrepetition_applicability_and_status_vocabulary() -> None:
    skill = frozen_skill_text("SKILL.md")
    contracts = frozen_skill_text("references/output-contracts.md")
    assert "State each substantive conclusion, limitation, unsupported pathway, and evidence need once" in skill
    assert "Suppress nonapplicable layers" in skill
    statuses = {
        "supported", "conditionally_supported", "unsupported", "contradicted",
        "not_supplied", "not_assessed", "not_applicable",
    }
    assert all(f"`{status}`" in contracts for status in statuses)
    assert "Reserve internal `fail`" in skill


def test_domain_playbooks_have_distinct_sequences() -> None:
    om = text("references/om-framing.md")
    is_ = text("references/is-framing.md")
    or_ = text("references/or-framing.md")
    assert "operational setting" in om and "constrained choice" in om
    assert "digital phenomenon" in is_ and "governance or design mechanism" in is_
    assert "mathematical abstraction" in or_ and "computational obstacle" in or_


def test_or_computational_rules_are_directly_routed() -> None:
    skill = text("SKILL.md")
    reference = text("references/or-computational-contribution.md")
    assert "references/or-computational-contribution.md" in skill
    for phrase in (
        "Runtime is not profit",
        "does not change the true optimum",
        "Fewer nodes do not necessarily imply shorter runtime",
        "post-deadline certificate cannot improve a decision already executed",
        "Realized profit",
    ):
        assert phrase in reference


def test_original_examples_cover_ten_scenarios() -> None:
    examples = frozen_skill_text("references/original-examples.md")
    assert "references/original-examples.md" in frozen_skill_text("SKILL.md")
    for number in range(1, 11):
        assert f"## {number}." in examples
    assert "Compact" in examples and "Standard" in examples and "Full audit" in examples


def test_businessbrief_validator_and_openai_metadata_are_unchanged() -> None:
    validator = SKILL / "scripts" / "validate_brief.py"
    metadata = SKILL / "agents" / "openai.yaml"
    assert canonical_text_sha256(validator) == "e238906e3a1861a75327348194f52898482ec0d59d3d311daa6f7f3b356eaecc"
    assert canonical_text_sha256(metadata) == "3d747031fadb49b13236da80f16b6de40f1b342d61116b8fbaac443b113ef213"


def test_canary_static_contract() -> None:
    tool = import_file("skill_canary_test", ROOT / "tools" / "skill_canary.py")
    tool.validate_static()
    visible, audit = tool.task_maps()
    assert len(visible) == len(audit) == 8
    assert all(set(item) == {"task_id", "domain", "profile", "request"} for item in visible.values())


def test_canary_metrics_detect_prohibited_or_claims() -> None:
    tool = import_file("skill_canary_metrics", ROOT / "tools" / "skill_canary.py")
    assert tool.sentence_overclaim("Faster runtime therefore raises profit.", "runtime_to_profit")
    assert not tool.sentence_overclaim("Faster runtime does not establish profit.", "runtime_to_profit")
    assert tool.sentence_overclaim("The post-deadline certificate improves operational value.", "post_deadline_value")
    assert not tool.sentence_overclaim("The post-deadline certificate cannot improve the executed decision.", "post_deadline_value")


def test_canary_has_exact_call_budget() -> None:
    manifest = json.loads((CANARY / "runs" / "call-manifest.json").read_text(encoding="utf-8"))
    calls = manifest["calls"]
    assert len(calls) == 24
    assert sum(item["role"] == "generation" for item in calls) == 16
    assert sum(item["role"] == "blind_pairwise_judge" for item in calls) == 8
    assert len({item["call_id"] for item in calls}) == 24


def test_holdouts_are_outside_canary() -> None:
    paths = [path.relative_to(CANARY).as_posix().casefold() for path in CANARY.rglob("*")]
    assert not any("holdout" in path for path in paths)


def test_canary_artifacts_are_complete_and_schema_valid() -> None:
    tool = import_file("skill_canary_artifacts", ROOT / "tools" / "skill_canary.py")
    freeze = json.loads((CANARY / "freeze.json").read_text(encoding="utf-8"))
    assert freeze["preregistration_sha256"] == tool.hash_file(CANARY / "preregistration.json")
    assert freeze["generator_tasks_sha256"] == tool.hash_file(CANARY / "tasks/generator-visible.json")
    assert freeze["audit_tasks_sha256"] == tool.hash_file(CANARY / "tasks/audit-only.json")
    assert freeze["call_manifest_sha256"] == tool.hash_file(CANARY / "runs/call-manifest.json")
    assert freeze["tool_sha256"] == tool.hash_file(ROOT / "tools/skill_canary.py")
    assert freeze["candidate_skill_sha256"] == frozen_skill_sha256()
    assert freeze["automated_holdout_opened"] is False
    assert freeze["expert_holdout_opened"] is False
    outputs = sorted((CANARY / "outputs").glob("GEN-*.json"))
    judgments = sorted((CANARY / "judgments").glob("JUDGE-*.json"))
    pairs = sorted((CANARY / "blinded-pairs").glob("PAIR-*.json"))
    assert len(outputs) == 16
    assert len(judgments) == len(pairs) == 8
    for path in outputs:
        tool.validate_schema(json.loads(path.read_text(encoding="utf-8")), "generation-result.schema.json")
    for path in judgments:
        tool.validate_schema(json.loads(path.read_text(encoding="utf-8")), "judge-result.schema.json")
    for path in pairs:
        tool.validate_schema(json.loads(path.read_text(encoding="utf-8")), "blinded-pair.schema.json")


def test_canary_result_records_failed_merge_gate() -> None:
    result = json.loads((CANARY / "results" / "canary-result.json").read_text(encoding="utf-8"))
    assert result["status"] == "fail"
    assert result["experimental_merge_authorized"] is False
    assert result["validation_authorized"] is False
    assert result["release_authorized"] is False
    assert result["authoritative_calls_used"] == 24
    assert result["automated_holdout_opened"] is False
    assert result["expert_holdout_opened"] is False
    assert result["no_human_experts"] is True


def test_product_owner_package_is_blinded() -> None:
    packets = sorted((CANARY / "user-acceptance" / "pairs").glob("UAT-*.md"))
    assert len(packets) == 8
    assert (CANARY / "user-acceptance" / "review-form.md").is_file()
    combined = "\n".join(path.read_text(encoding="utf-8") for path in packets)
    assert "Skill 2.1" not in combined
    assert "v0.2" not in combined
    assert not (CANARY / "user-acceptance" / "condition-key.json").exists()
