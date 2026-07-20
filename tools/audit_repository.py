#!/usr/bin/env python3
"""Reject public-repository files that commonly contain private or copied material."""

from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
MAX_TEXT_BYTES = 250_000
PRIVATE_PARTS = {"research-private", "private-corpus", "source-corpus"}
FORBIDDEN_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".zip", ".7z", ".rar", ".tar", ".gz", ".bz2", ".xz",
    ".pem", ".key", ".p12", ".pfx",
}
FORBIDDEN_NAMES = {
    ".env", "credentials.json", "service-account.json", "id_rsa",
    "id_ed25519", "secrets.yml", "secrets.yaml", "secrets.json",
}
TEXT_EXTENSIONS = {
    "", ".cff", ".csv", ".json", ".jsonl", ".md", ".py", ".rst",
    ".toml", ".tsv", ".txt", ".yaml", ".yml",
}
# Keep exceptions explicit and reviewable. Do not allowlist directories.
OVERSIZE_ALLOWLIST: frozenset[str] = frozenset()


def tracked_files(root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"], cwd=root, capture_output=True, check=False
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.decode(errors="replace").strip())
    return [root / item.decode() for item in result.stdout.split(b"\0") if item]


def public_files(root: Path) -> list[Path]:
    ignored = {
        ".git", ".agents", ".codex", ".local-eval", ".local-tools", ".official-skills", ".venv",
        "venv", "__pycache__", ".pytest_cache", "build", "dist",
        "research-private", "runs-private",
    }
    files: list[Path] = []
    for directory, names, filenames in os.walk(root):
        names[:] = [name for name in names if name not in ignored]
        files.extend(Path(directory) / filename for filename in filenames)
    return files


def permitted_literature_file(path: Path, relative: str, root: Path) -> tuple[bool, str]:
    """Accept a staged full source only when every publication record agrees."""
    if not relative.startswith("literature/open-access/"):
        return False, "outside literature/open-access"
    manifest_path = root / "literature" / "manifest.yaml"
    try:
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        return False, f"cannot read canonical manifest: {exc}"
    records = [
        item for item in manifest.get("sources", [])
        if item.get("committed_source_path") == relative
    ]
    if len(records) != 1:
        return False, "requires exactly one manifest record with this committed_source_path"
    record = records[0]
    allowed_statuses = {"redistributable_explicit_license", "public_domain"}
    if record.get("redistribution_status") not in allowed_statuses:
        return False, "manifest redistribution_status does not permit a committed full source"
    if record.get("license") in {None, "unknown", "all_rights_reserved"}:
        return False, "manifest lacks an explicit redistributable license"
    if not record.get("license_url"):
        return False, "manifest lacks a license URL"
    expected = record.get("checksum")
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if not expected or expected.removeprefix("sha256:").casefold() != actual:
        return False, "SHA-256 checksum does not match the manifest"
    source_id = record.get("source_id")
    license_record = root / "literature" / "licenses" / f"{source_id}.md"
    if not license_record.is_file():
        return False, "license record is missing"
    notices = (root / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
    if source_id not in notices or relative not in notices:
        return False, "third-party notice lacks source ID and committed path"
    if not record.get("complete_citation") or not record.get("copyright_holder"):
        return False, "attribution metadata is incomplete"
    return True, ""


def audit(paths: list[Path], root: Path = ROOT) -> list[str]:
    violations: list[str] = []
    for path in paths:
        if not path.exists() or not path.is_file():
            continue
        relative = path.resolve().relative_to(root.resolve()).as_posix()
        parts = {part.casefold() for part in Path(relative).parts}
        name = path.name.casefold()
        suffix = path.suffix.casefold()
        if parts & PRIVATE_PARTS:
            violations.append(f"{relative}: private-corpus path is not publishable")
        if suffix in FORBIDDEN_EXTENSIONS:
            permitted, reason = permitted_literature_file(path, relative, root)
            if not permitted:
                violations.append(
                    f"{relative}: forbidden document/archive/credential extension {suffix} ({reason})"
                )
        if name in FORBIDDEN_NAMES or (name.startswith(".env.") and name != ".env.example"):
            violations.append(f"{relative}: credential-like filename")
        if (
            suffix in TEXT_EXTENSIONS
            and path.stat().st_size > MAX_TEXT_BYTES
            and relative not in OVERSIZE_ALLOWLIST
        ):
            violations.append(
                f"{relative}: text file is {path.stat().st_size} bytes; limit is {MAX_TEXT_BYTES}"
            )
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--tracked", action="store_true", help="audit only Git-tracked files")
    group.add_argument("--all", action="store_true", help="audit all public workspace files")
    args = parser.parse_args()

    paths = public_files(ROOT) if args.all else tracked_files(ROOT)
    violations = audit(paths)
    if violations:
        print("Repository audit failed:", file=sys.stderr)
        for violation in violations:
            print(f"- {violation}", file=sys.stderr)
        return 1
    print(f"Repository audit passed ({len(paths)} files checked).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
