#!/usr/bin/env python3
"""Validate literature metadata, audited cards, and redistribution invariants."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
LITERATURE = ROOT / "literature"
CARD_HEADINGS = (
    "Bibliographic information",
    "Source tier",
    "Authority rationale",
    "Inclusion rationale",
    "Problem addressed",
    "Central contribution",
    "Supported framing principles",
    "What it does not establish",
    "DFC-12 relevance",
    "Managerial-framing implications",
    "Scholarly-positioning implications",
    "Relevant output modes",
    "Candidate Skill rules",
    "Anti-patterns",
    "Counterconditions",
    "Exact evidence locations",
    "Access and license status",
    "Extraction confidence",
    "Independent audit result",
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def card_frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError("missing opening YAML frontmatter delimiter")
    parts = text.split("---", 2)
    if len(parts) != 3 or not parts[2].strip():
        raise ValueError("missing closing delimiter or Markdown body")
    value = yaml.safe_load(parts[1])
    if not isinstance(value, dict):
        raise ValueError("frontmatter must be a mapping")
    return value


def card_headings(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    body = parts[2] if len(parts) == 3 else ""
    return [line[3:].strip() for line in body.splitlines() if line.startswith("## ")]


def schema_errors(instance: Any, schema: dict[str, Any], label: str) -> list[str]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [
        f"{label}{'/' + '/'.join(str(item) for item in error.absolute_path) if error.absolute_path else ''}: {error.message}"
        for error in sorted(validator.iter_errors(instance), key=lambda item: list(item.absolute_path))
    ]


def validate(root: Path = ROOT, require_complete: bool = False) -> list[str]:
    literature = root / "literature"
    manifest_path = literature / "manifest.yaml"
    manifest = load_yaml(manifest_path)
    errors = schema_errors(
        manifest,
        load_json(literature / "schemas" / "manifest.schema.json"),
        "literature/manifest.yaml",
    )
    if errors or not isinstance(manifest, dict):
        return errors

    card_schema = load_json(literature / "schemas" / "source-card.schema.json")
    sources = manifest["sources"]
    ids = [source["source_id"] for source in sources]
    if len(ids) != len(set(ids)):
        errors.append("literature/manifest.yaml: source_id values must be unique")
    card_paths = [source["card_path"] for source in sources]
    if len(card_paths) != len(set(card_paths)):
        errors.append("literature/manifest.yaml: card_path values must be unique")

    declared_cards: set[Path] = set()
    for source in sources:
        relative_card = Path(source["card_path"])
        card_path = root / relative_card
        declared_cards.add(card_path.resolve())
        if not card_path.is_file():
            if source["verification_status"] != "pending_extraction":
                errors.append(f"{relative_card.as_posix()}: declared card is missing")
            continue
        try:
            card = card_frontmatter(card_path)
        except (OSError, ValueError, yaml.YAMLError) as exc:
            errors.append(f"{relative_card.as_posix()}: {exc}")
            continue
        errors.extend(schema_errors(card, card_schema, relative_card.as_posix()))
        headings = card_headings(card_path)
        if headings != list(CARD_HEADINGS):
            errors.append(
                f"{relative_card.as_posix()}: level-two headings must be the nineteen required sections in order"
            )
        for field in (
            "source_id", "verification_status", "access_status", "content_reviewed", "license",
            "redistribution_status",
        ):
            if card.get(field) != source.get(field):
                errors.append(f"{relative_card.as_posix()}: {field} disagrees with manifest")
        if source["verification_status"] == "verified":
            for pass_name in ("extraction_pass", "audit_pass"):
                item = card.get(pass_name, {})
                if item.get("status") != "pass" or item.get("agent_context") != "fresh":
                    errors.append(f"{relative_card.as_posix()}: verified card requires fresh passing {pass_name}")
        if source["redistribution_status"] == "full_text_permitted" and source["license"] not in {
            "explicit_permissive", "public_domain", "permission_obtained"
        }:
            errors.append(f"{relative_card.as_posix()}: full-text redistribution lacks an eligible license basis")

    actual_cards = {
        path.resolve() for path in (literature / "source-cards").glob("*.md")
        if path.name.casefold() != "readme.md"
    }
    for path in sorted(actual_cards - declared_cards):
        errors.append(f"{path.relative_to(root).as_posix()}: source card is not declared in manifest")

    if require_complete:
        if len(sources) != 20:
            errors.append(f"literature/manifest.yaml: release requires exactly 20 sources, found {len(sources)}")
        incomplete = [source["source_id"] for source in sources if source["verification_status"] != "verified"]
        if incomplete:
            errors.append(f"literature/manifest.yaml: unverified release sources: {', '.join(incomplete)}")

    for staging in (literature / "open-access", literature / "licenses"):
        unexpected = [path for path in staging.iterdir() if path.name.casefold() != "readme.md"]
        if unexpected:
            errors.append(
                f"{staging.relative_to(root).as_posix()}: staged third-party files require manifest/license/checksum validation"
            )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require-complete", action="store_true",
        help="require the release corpus to contain exactly 20 verified sources",
    )
    args = parser.parse_args()
    errors = validate(require_complete=args.require_complete)
    if errors:
        print("Literature validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("Literature validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
