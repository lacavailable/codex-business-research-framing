from __future__ import annotations

import re
import subprocess
import sys
import zipfile
from pathlib import Path

import yaml

from conftest import ROOT, SKILL_NAME, import_file


REQUIRED_REPOSITORY_FILES = {
    "README.md", "LICENSE", "CHANGELOG.md", "CONTRIBUTING.md", "SECURITY.md",
    "CITATION.cff", ".gitignore", "pyproject.toml", ".github/workflows/ci.yml",
    ".github/workflows/release.yml", ".github/pull_request_template.md",
    "docs/worked-examples.md", "docs/evaluation-methodology.md",
    "docs/limitations.md", "docs/copyright-and-sources.md",
}
REQUIRED_REFERENCES = {
    "framework.md", "business-brief-schema.md", "model-to-reality-mapping.md",
    "om-framing.md", "is-framing.md", "or-framing.md",
    "evidence-and-attribution.md", "anti-patterns.md", "output-contracts.md",
    "evaluation-rubric.md",
}


def frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    _, raw, body = text.split("---", 2)
    assert body.strip(), "SKILL.md must contain instructions"
    value = yaml.safe_load(raw)
    assert isinstance(value, dict)
    return value


def test_required_repository_files_exist(root: Path) -> None:
    missing = sorted(path for path in REQUIRED_REPOSITORY_FILES if not (root / path).is_file())
    assert not missing, f"missing repository files: {missing}"


def test_skill_frontmatter_and_name(skill: Path) -> None:
    metadata = frontmatter(skill / "SKILL.md")
    assert set(metadata) == {"name", "description"}
    assert metadata["name"] == SKILL_NAME == skill.name
    assert re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", metadata["name"])
    assert len(metadata["name"]) <= 63
    assert isinstance(metadata["description"], str) and len(metadata["description"].split()) >= 12


def test_required_skill_resources_are_present_and_directly_linked(skill: Path) -> None:
    references = skill / "references"
    actual = {path.name for path in references.glob("*.md")}
    assert REQUIRED_REFERENCES <= actual
    skill_text = (skill / "SKILL.md").read_text(encoding="utf-8")
    for name in REQUIRED_REFERENCES:
        assert f"references/{name}" in skill_text, f"SKILL.md must directly route to {name}"
    for directory in ("agents", "assets", "references", "scripts"):
        assert (skill / directory).is_dir()


def test_openai_metadata_matches_skill(skill: Path) -> None:
    metadata = frontmatter(skill / "SKILL.md")
    openai = yaml.safe_load((skill / "agents" / "openai.yaml").read_text(encoding="utf-8"))
    assert set(openai) == {"interface"}
    interface = openai["interface"]
    assert set(interface) == {"display_name", "short_description", "default_prompt"}
    assert 1 <= len(interface["display_name"]) <= 64
    assert 1 <= len(interface["short_description"]) <= 80
    assert f"${metadata['name']}" in interface["default_prompt"]


def test_all_skill_references_are_reachable_from_skill_md(skill: Path) -> None:
    text = (skill / "SKILL.md").read_text(encoding="utf-8")
    unlinked = [
        path.name for path in (skill / "references").glob("*.md")
        if f"references/{path.name}" not in text
    ]
    assert not unlinked, f"reference files must be one hop from SKILL.md: {unlinked}"


def test_local_markdown_links_resolve() -> None:
    checker = import_file("check_links", ROOT / "tools" / "check_links.py")
    assert checker.broken_links(ROOT) == []


def test_private_corpus_audit_detects_forbidden_content(tmp_path: Path) -> None:
    auditor = import_file("audit_repository", ROOT / "tools" / "audit_repository.py")
    safe = tmp_path / "notes.md"
    safe.write_text("original synthetic note", encoding="utf-8")
    private_dir = tmp_path / "research-private"
    private_dir.mkdir()
    private = private_dir / "article.txt"
    private.write_text("private", encoding="utf-8")
    source_pdf = tmp_path / "source.pdf"
    source_pdf.write_bytes(b"%PDF")
    credential = tmp_path / ".env"
    credential.write_text("TOKEN=fake", encoding="utf-8")

    assert auditor.audit([safe], root=tmp_path) == []
    violations = auditor.audit([private, source_pdf, credential], root=tmp_path)
    assert len(violations) == 3


def test_private_corpus_audit_detects_oversized_text(tmp_path: Path) -> None:
    auditor = import_file("audit_repository_large", ROOT / "tools" / "audit_repository.py")
    large = tmp_path / "copied.txt"
    large.write_bytes(b"x" * (auditor.MAX_TEXT_BYTES + 1))
    assert any("limit" in item for item in auditor.audit([large], root=tmp_path))


def test_brief_validator_has_executable_help(skill: Path) -> None:
    candidates = sorted(
        path for path in (skill / "scripts").glob("*.py")
        if "valid" in path.stem.casefold() and "brief" in path.stem.casefold()
    )
    assert candidates, "a deterministic business-brief validation script is required"
    for script in candidates:
        result = subprocess.run(
            [sys.executable, str(script), "--help"], cwd=ROOT, capture_output=True, text=True
        )
        assert result.returncode == 0, result.stderr


def test_package_is_reproducible_installable_and_skill_only(tmp_path: Path) -> None:
    packager = import_file("package_skill", ROOT / "tools" / "package_skill.py")
    first_dir, second_dir = tmp_path / "first", tmp_path / "second"
    first, first_checksum = packager.build("0.1.0-alpha", first_dir)
    second, _ = packager.build("0.1.0-alpha", second_dir)
    assert first.read_bytes() == second.read_bytes()
    assert first_checksum.read_text(encoding="ascii").endswith(f"  {first.name}\n")
    assert packager.verify(first) == []

    with zipfile.ZipFile(first) as bundle:
        names = set(bundle.namelist())
        expected = {
            f"{SKILL_NAME}/{path.relative_to(packager.SKILL_DIR).as_posix()}"
            for path in packager.archive_files()
        }
        assert names == expected
        destination = tmp_path / "install"
        bundle.extractall(destination)
    assert (destination / SKILL_NAME / "SKILL.md").is_file()
    assert not any(name.startswith("tests/") or name.startswith("evals/") for name in names)
