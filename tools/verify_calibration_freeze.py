#!/usr/bin/env python3
"""Verify recorded public evaluator-freeze hashes."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / "evals" / "calibration" / "public-metadata" / "evaluator-freeze.json"


def canonical_bytes(path: Path) -> bytes:
    """Hash tracked text consistently across Git LF and Windows CRLF checkouts."""
    return path.read_bytes().replace(b"\r\n", b"\n")


def main() -> int:
    record = json.loads(FREEZE.read_text(encoding="utf-8"))
    errors = []
    for relative, expected in record["files"].items():
        path = ROOT / relative
        actual = hashlib.sha256(canonical_bytes(path)).hexdigest() if path.is_file() else "missing"
        if actual != expected:
            errors.append(f"{relative}: expected {expected}, got {actual}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(json.dumps({"freeze_commit": record["freeze_commit"], "files_verified": len(record["files"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
