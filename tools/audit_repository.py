#!/usr/bin/env python3
"""Reject public-repository files that commonly contain private or copied material."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


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
        ".git", ".local-eval", ".venv", "venv", "__pycache__",
        ".pytest_cache", "build", "dist", "runs-private",
    }
    files: list[Path] = []
    for directory, names, filenames in os.walk(root):
        names[:] = [name for name in names if name not in ignored]
        files.extend(Path(directory) / filename for filename in filenames)
    return files


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
            violations.append(f"{relative}: forbidden document/archive/credential extension {suffix}")
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
