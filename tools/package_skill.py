#!/usr/bin/env python3
"""Build or verify a deterministic, standalone Skill archive."""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
import zipfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
SKILL_NAME = "frame-business-research-problem"
SKILL_DIR = ROOT / "skills" / SKILL_NAME
VERSION = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*)?$")
EXCLUDED_PARTS = {"__pycache__", ".pytest_cache"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}


def archive_files(skill_dir: Path = SKILL_DIR) -> list[Path]:
    return sorted(
        (
            path
            for path in skill_dir.rglob("*")
            if path.is_file()
            and not any(part in EXCLUDED_PARTS for part in path.relative_to(skill_dir).parts)
            and path.suffix.casefold() not in EXCLUDED_SUFFIXES
        ),
        key=lambda path: path.relative_to(skill_dir).as_posix(),
    )


def build(version: str, output_dir: Path) -> tuple[Path, Path]:
    if not VERSION.fullmatch(version):
        raise ValueError(f"invalid release version: {version!r}")
    required = [SKILL_DIR / "SKILL.md", SKILL_DIR / "agents" / "openai.yaml"]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing required Skill files: " + ", ".join(missing))

    output_dir.mkdir(parents=True, exist_ok=True)
    archive = output_dir / f"{SKILL_NAME}-v{version}.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for source in archive_files():
            relative = source.relative_to(SKILL_DIR).as_posix()
            info = zipfile.ZipInfo(f"{SKILL_NAME}/{relative}", date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o755 if source.suffix == ".sh" else 0o644) << 16
            info.create_system = 3
            bundle.writestr(info, source.read_bytes(), compresslevel=9)

    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    checksum = archive.with_suffix(archive.suffix + ".sha256")
    checksum.write_text(f"{digest}  {archive.name}\n", encoding="ascii", newline="\n")
    return archive, checksum


def verify(archive: Path) -> list[str]:
    errors: list[str] = []
    if not archive.is_file():
        return [f"archive does not exist: {archive}"]
    try:
        with zipfile.ZipFile(archive) as bundle:
            names = bundle.namelist()
            for name in names:
                pure = PurePosixPath(name)
                if pure.is_absolute() or ".." in pure.parts:
                    errors.append(f"unsafe archive member: {name}")
                if not pure.parts or pure.parts[0] != SKILL_NAME:
                    errors.append(f"member is outside top-level {SKILL_NAME}/: {name}")
            for required in (
                f"{SKILL_NAME}/SKILL.md",
                f"{SKILL_NAME}/agents/openai.yaml",
            ):
                if required not in names:
                    errors.append(f"missing archive member: {required}")
            if bundle.testzip() is not None:
                errors.append("archive contains a corrupt member")
    except zipfile.BadZipFile:
        errors.append("not a valid zip archive")

    checksum = archive.with_suffix(archive.suffix + ".sha256")
    if checksum.exists():
        fields = checksum.read_text(encoding="ascii").strip().split()
        actual = hashlib.sha256(archive.read_bytes()).hexdigest()
        if len(fields) != 2 or fields[0] != actual or fields[1] != archive.name:
            errors.append("checksum file does not match archive")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--version", help="build this semantic prerelease/stable version")
    action.add_argument("--verify", type=Path, help="verify an existing archive")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist")
    args = parser.parse_args()

    if args.verify:
        errors = verify(args.verify.resolve())
        if errors:
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
        print(f"Verified {args.verify}")
        return 0

    try:
        archive, checksum = build(args.version, args.output_dir.resolve())
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(archive)
    print(checksum)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
