#!/usr/bin/env python3
"""Check tracked text against private passage fingerprints and validate Unicode."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_SOURCES = ROOT / "research-private" / "evaluator-calibration" / "source-passages"
TEXT_SUFFIXES = {".cff", ".csv", ".json", ".jsonl", ".md", ".py", ".rst", ".toml", ".txt", ".yaml", ".yml"}


def tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.casefold())


def fingerprints(text: str, width: int = 12) -> set[str]:
    values = tokens(text)
    return {
        hashlib.sha256(" ".join(values[index:index + width]).encode()).hexdigest()
        for index in range(max(0, len(values) - width + 1))
    }


def tracked_files() -> list[Path]:
    result = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError(result.stderr.decode(errors="replace"))
    return [ROOT / item.decode() for item in result.stdout.split(b"\0") if item]


def audit(require_private: bool = False) -> dict[str, object]:
    private_files = sorted(PRIVATE_SOURCES.glob("*.txt")) if PRIVATE_SOURCES.exists() else []
    if require_private and not private_files:
        raise ValueError("private source passages are required but absent")
    private_index: dict[str, set[str]] = {}
    for path in private_files:
        private_index[path.stem] = fingerprints(path.read_text(encoding="utf-8"))
    violations: list[str] = []
    checked = 0
    for path in tracked_files():
        if not path.is_file() or path.suffix.casefold() not in TEXT_SUFFIXES:
            continue
        checked += 1
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeError:
            violations.append(f"{path.relative_to(ROOT)}: not valid UTF-8")
            continue
        if "\ufffd" in text or any(chr(codepoint) in text for codepoint in (0x9225, 0x951F, 0x95C1)):
            violations.append(f"{path.relative_to(ROOT)}: Unicode replacement or mojibake marker")
        public_fingerprints = fingerprints(text)
        for source_id, source_fingerprints in private_index.items():
            overlap = len(public_fingerprints & source_fingerprints)
            if overlap:
                violations.append(f"{path.relative_to(ROOT)}: shares {overlap} private 12-token fingerprint(s) with {source_id}")
    if violations:
        raise ValueError("; ".join(violations))
    return {"tracked_text_files": checked, "private_sources": len(private_files), "fingerprint_matches": 0}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-private", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(audit(args.require_private), indent=2))
        return 0
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
