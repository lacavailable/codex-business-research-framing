from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import jsonschema
import yaml

from conftest import ROOT, import_file


SKILL = ROOT / "skills" / "frame-business-research-problem"
CARD_HEADINGS = [
    "Bibliographic information", "Source tier", "Authority rationale",
    "Inclusion rationale", "Problem addressed", "Central contribution",
    "Supported framing principles", "What it does not establish",
    "DFC-12 relevance", "Managerial-framing implications",
    "Scholarly-positioning implications", "Relevant output modes",
    "Candidate Skill rules", "Anti-patterns", "Counterconditions",
    "Exact evidence locations", "Access and license status",
    "Extraction confidence", "Independent audit result",
]


def frontmatter(path: Path) -> dict:
    parts = path.read_text(encoding="utf-8").split("---", 2)
    assert len(parts) == 3
    return yaml.safe_load(parts[1])


def test_manifest_and_twenty_verified_cards() -> None:
    manifest = yaml.safe_load((ROOT / "literature/manifest.yaml").read_text(encoding="utf-8"))
    schema = json.loads((ROOT / "literature/schemas/manifest.schema.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(manifest)
    assert len(manifest["sources"]) == 20
    assert len({item["source_id"] for item in manifest["sources"]}) == 20
    assert all(item["verification_status"] == "verified" for item in manifest["sources"])
    assert all(item["committed_source_path"] is None for item in manifest["sources"])
    assert all(item["redistribution_status"] == "metadata_and_original_notes_only" for item in manifest["sources"])

    card_schema = json.loads((ROOT / "literature/schemas/source-card.schema.json").read_text(encoding="utf-8"))
    cards = sorted((ROOT / "literature/source-cards").glob("*.md"))
    cards = [path for path in cards if path.name != "README.md"]
    assert len(cards) == 20
    for path in cards:
        data = frontmatter(path)
        jsonschema.Draft202012Validator(card_schema, format_checker=jsonschema.FormatChecker()).validate(data)
        assert data["verification_status"] == "verified"
        assert data["extraction_pass"]["status"] == "pass"
        assert data["extraction_pass"]["agent_context"] == "fresh"
        assert data["audit_pass"]["status"] == "pass"
        assert data["audit_pass"]["agent_context"] == "fresh"
        body = path.read_text(encoding="utf-8").split("---", 2)[2]
        headings = [line[3:] for line in body.splitlines() if line.startswith("## ")]
        assert headings == CARD_HEADINGS


def test_rule_registry_traceability_and_generated_matrix() -> None:
    module = import_file("generate_rule_matrix", ROOT / "tools/generate_rule_matrix.py")
    registry = module.load_yaml(module.REGISTRY)
    manifest = module.load_yaml(module.MANIFEST)
    assert module.validate(registry, manifest) == []
    assert any(rule["status"] == "core_triangulated" for rule in registry["rules"])
    assert module.TARGET.read_text(encoding="utf-8") == module.render(registry, manifest)


def test_input_template_schema() -> None:
    schema = json.loads((SKILL / "assets/research-framing-input.schema.json").read_text(encoding="utf-8"))
    value = json.loads((SKILL / "assets/research-framing-input-template.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(value)
    markdown = (SKILL / "assets/research-framing-input-template.md").read_text(encoding="utf-8")
    for label in ("essential", "recommended", "optional", "unknown permitted"):
        assert label in markdown


def test_readme_manual_sections_and_worked_example() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    for number in range(1, 20):
        assert f"## {number}." in text
    for required in (
        "Stage 1", "Stage 2", "Stage 3", "Stage 4", "Markov", "nearest store",
        "display capacity", "inventory", "fulfillment", "Model-to-reality mapping",
        "Claims requiring evidence", "Proposed introduction opening",
        "Primary remaining weakness", "$frame-business-research-problem",
        "请使用", "not_assessed",
    ):
        assert required.casefold() in text.casefold()


def test_all_eight_v2_mode_contracts_are_documented() -> None:
    text = (SKILL / "references/output-contracts.md").read_text(encoding="utf-8")
    for mode in (
        "create", "diagnose", "rewrite", "compare-scenarios",
        "map-model-to-business", "audit-assumptions", "draft-introduction",
        "draft-managerial-implications",
    ):
        assert f"### `{mode}`" in text


def test_no_third_party_full_text_is_bundled() -> None:
    source_files = [
        path for path in (ROOT / "literature/open-access").rglob("*")
        if path.is_file() and path.name != "README.md"
    ]
    assert source_files == []
    notices = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
    assert "no third-party full text" in notices.casefold()


def test_generated_documents_are_current() -> None:
    for script in ("generate_rubric.py", "generate_rule_matrix.py"):
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools" / script), "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
