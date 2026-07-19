# Contributing

Thank you for helping make research framing more faithful, testable, and useful.

## Before opening a change

Open an issue for substantial framework, schema, or evaluation changes. Keep examples synthetic unless you have verified that every included element can be redistributed. Do not commit source PDFs, office documents, private corpora, credentials, paywalled text, or long excerpts.

## Development

1. Create a branch from the default branch.
2. Create a Python 3.11+ virtual environment.
3. Run `python -m pip install -e ".[dev]"`.
4. Make one focused change and add deterministic tests.
5. Run `pytest`, `python tools/audit_repository.py --tracked`, and `python tools/check_links.py`.
6. If the Skill changes, run the official `quick_validate.py` and rebuild the archive with `python tools/package_skill.py --version 0.1.0-alpha --output-dir dist`.

Language-model evaluations are informative but nondeterministic. Include the model identifier, generation settings, prompts, raw outputs, blinded judgments, and limitations when submitting new results. Never replace raw results with only a favorable aggregate.

## Pull requests

Explain the research-fidelity problem, the behavioral change, and how it was tested. Call out changes to public contracts, benchmark cases, hard-failure rules, or scoring. A pull request must pass deterministic CI and the repository audit.

Contributions are accepted under the MIT License. Follow the [Code of Conduct](CODE_OF_CONDUCT.md).
