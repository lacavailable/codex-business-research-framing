#!/usr/bin/env python3
"""Generate randomized public-safe bias-diagnostic fixtures."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path

import generate_public_calibration as suite


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "evals" / "calibration" / "bias-diagnostics" / "synthetic-diagnostic-manifest.json"
SEED = 20260720
DIAGNOSTICS = ("journal_identity", "publication_label", "faithful_paraphrase", "headings", "verbosity")


def identifier(text: str) -> str:
    return "D" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def arms(base: dict[str, str], diagnostic: str) -> tuple[dict[str, str], dict[str, str]]:
    passage = suite.render(base)
    if diagnostic == "journal_identity":
        return ({"label": "identity_hidden", "context_label": "Source identity withheld.", "passage": passage},
                {"label": "identity_revealed", "context_label": "Experimental label: published in a named journal.", "passage": passage})
    if diagnostic == "publication_label":
        return ({"label": "published", "context_label": "Experimental label: published article.", "passage": passage},
                {"label": "working_paper", "context_label": "Experimental label: working paper.", "passage": passage})
    if diagnostic == "faithful_paraphrase":
        paraphrase = passage.replace("The stated objective is to", "The decision criterion is to").replace("The analysis", "This analysis")
        return ({"label": "original_synthetic", "context_label": "Identity withheld.", "passage": passage},
                {"label": "mechanical_paraphrase_fixture", "context_label": "Identity withheld.", "passage": paraphrase})
    if diagnostic == "headings":
        sentences = passage.split(". ")
        headed = "Decision: " + ". ".join(sentences[:2]) + ". Mechanism and scope: " + ". ".join(sentences[2:])
        return ({"label": "headings_absent", "context_label": "Identity withheld.", "passage": passage},
                {"label": "headings_added", "context_label": "Identity withheld.", "passage": headed})
    verbose = passage + " " + " ".join([
        "This decision matters to organizations because organizations face decisions.",
        "It has practical, managerial, and organizational relevance.",
        "Careful consideration can help decision makers consider it carefully.",
    ])
    return ({"label": "information_matched", "context_label": "Identity withheld.", "passage": passage},
            {"label": "length_only", "context_label": "Identity withheld.", "passage": verbose})


def build() -> dict:
    records = []
    rng = random.Random(SEED)
    for base in suite.BASES:
        for diagnostic in DIAGNOSTICS:
            pair_id = identifier(base["key"] + ":" + diagnostic)
            pair_arms = list(arms(base, diagnostic))
            rng.shuffle(pair_arms)
            for order, arm in enumerate(pair_arms):
                records.append({
                    "case_id": identifier(pair_id + ":" + arm["label"]),
                    "pair_id": pair_id,
                    "domain": base["domain"],
                    "source_cluster": base["key"],
                    "split": base["split"],
                    "diagnostic": diagnostic,
                    "arm": arm["label"],
                    "randomized_order": order,
                    "context_label": arm["context_label"],
                    "passage": arm["passage"],
                })
    return {
        "schema_version": "3.0.0",
        "status": "synthetic_fixture_only_not_an_empirical_bias_result",
        "seed": SEED,
        "records": sorted(records, key=lambda item: item["case_id"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = json.dumps(build(), ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != expected:
            raise SystemExit("synthetic bias diagnostic manifest is stale")
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(expected, encoding="utf-8", newline="\n")
    print(json.dumps({"records": len(build()["records"]), "pairs": len(build()["records"]) // 2}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
