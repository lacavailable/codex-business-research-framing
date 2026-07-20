#!/usr/bin/env python3
"""Check that local links in repository Markdown files resolve."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
REMOTE_PREFIXES = ("http://", "https://", "mailto:", "tel:")
SKIP_PARTS = {
    ".git", ".agents", ".codex", ".local-eval", ".local-tools", ".official-skills", ".pytest_cache",
    ".venv", "venv", "build", "dist", "research-private", "runs-private",
}


def markdown_files(root: Path) -> list[Path]:
    return [
        path
        for path in root.rglob("*.md")
        if not any(part in SKIP_PARTS for part in path.relative_to(root).parts)
    ]


def broken_links(root: Path = ROOT) -> list[str]:
    broken: list[str] = []
    for source in markdown_files(root):
        text = source.read_text(encoding="utf-8")
        for line_number, line in enumerate(text.splitlines(), 1):
            for match in LINK.finditer(line):
                raw = match.group(1).strip()
                if not raw or raw.startswith("#") or raw.casefold().startswith(REMOTE_PREFIXES):
                    continue
                # Drop an optional Markdown title after the target.
                target_text = raw[1:raw.find(">")] if raw.startswith("<") and ">" in raw else raw.split()[0]
                target_text = unquote(target_text.split("#", 1)[0])
                target = (root / target_text.lstrip("/")) if target_text.startswith("/") else (source.parent / target_text)
                if not target.exists():
                    relative = source.relative_to(root).as_posix()
                    broken.append(f"{relative}:{line_number}: {raw}")
    return broken


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    broken = broken_links()
    if broken:
        print("Broken local links:", file=sys.stderr)
        for item in broken:
            print(f"- {item}", file=sys.stderr)
        return 1
    print(f"Local Markdown links passed ({len(markdown_files(ROOT))} files checked).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
