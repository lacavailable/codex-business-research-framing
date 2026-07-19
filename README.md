# Codex Business Research Framing

`frame-business-research-problem` is an open-source Codex Agent Skill for turning Operations Management (OM), Information Systems (IS), and Operations Research (OR) research into concrete business-problem narratives without changing the research model to improve the story.

The Skill centers model fidelity. It identifies the decision maker, trigger, choices, decision-time information, stakes, constraints, mechanism, trade-off, counterfactual, mathematical mapping, evidence status, and boundary conditions. A fluent narrative is not accepted when its actor, timing, information, behavior, constraints, or objective conflict with the model.

This project is not a Harvard Business Review imitation tool. It does not reproduce any publisher's style or content and is not sponsored, endorsed by, or affiliated with Harvard Business Review, Harvard Business Publishing, INFORMS, AIS, or any journal.

## Use cases

- **OM:** capacity, inventory, fulfillment, demand uncertainty, substitution, congestion, and resource allocation.
- **IS:** information asymmetry, signals, platform governance, strategic behavior, screening, moderation, privacy, fairness, and externalities.
- **OR:** decision variables, objectives, feasible regions, uncertainty, computational limits, exactness, certificates, and decision deadlines.

The eight modes are `create`, `diagnose`, `rewrite`, `compare-scenarios`, `map-model-to-business`, `audit-assumptions`, `draft-introduction`, and `draft-managerial-implications`.

## Install

Install from a release archive by extracting it into your Codex skills directory:

```powershell
Expand-Archive frame-business-research-problem-v0.1.0-alpha.zip -DestinationPath "$env:USERPROFILE\.agents\skills"
```

On macOS or Linux:

```bash
unzip frame-business-research-problem-v0.1.0-alpha.zip -d "$HOME/.agents/skills"
```

The archive contains one top-level directory named `frame-business-research-problem`. Restart Codex or begin a new task after installation.

For repository development, use Python 3.11 or newer:

```bash
python -m venv .venv
python -m pip install -e ".[dev]"
```

## Invoke

Ask naturally, or name the Skill explicitly when you want deterministic routing:

```text
Use $frame-business-research-problem in diagnose mode. Audit whether this
inventory-allocation story is consistent with the supplied optimization model.
Label every claim by evidence status and identify the strongest remaining weakness.
```

```text
Use $frame-business-research-problem in compare-scenarios mode. Generate three
settings for this capacity-constrained choice model, reject inconsistent settings,
and rank only the eligible settings by model fit first.
```

Outputs use a shared business-brief envelope: diagnosis, narrative, model mapping when a model is supplied, unverified claims, boundaries, and the primary remaining weakness. Mode-specific requirements are documented inside the Skill.

## Why fidelity comes first

Improving prose does not validate a setting. For example, calling an observed demand state a managerial choice makes a story more active but changes the mathematical meaning. The Skill's Decision-Fidelity Canvas (DFC-12) surfaces that mismatch before writing and applies six consistency gates before ranking candidate settings.

See [the synthetic worked examples](docs/worked-examples.md) for before-and-after cases. The examples are teaching artifacts, not empirical claims.

## Evaluation

The benchmark contains 30 cases: 10 each for OM, IS, and OR. It compares a no-Skill baseline, a generic business-writing prompt, and the full Skill. The 100-point rubric emphasizes model fidelity, decision specificity, a nontrivial trade-off, mechanism, evidence discipline, boundary conditions, model mapping, and managerial clarity. Hard failures are preserved and cap the reported score below the passing threshold.

Deterministic tests validate repository structure, benchmark schemas, internal links, private-corpus safeguards, Skill metadata, scripts, and release packaging. Language-model generation and judging are intentionally outside required CI. Read [the evaluation methodology](docs/evaluation-methodology.md) and [limitations](docs/limitations.md) before interpreting reported results.

## Validate and package

```bash
pytest
python tools/audit_repository.py --tracked
python tools/check_links.py
python tools/package_skill.py --version 0.1.0-alpha --output-dir dist
python tools/package_skill.py --verify dist/frame-business-research-problem-v0.1.0-alpha.zip
```

The final command also checks the adjacent `.sha256` file when it exists. The official Agent Skills `quick_validate.py` utility should additionally be run against `skills/frame-business-research-problem` before a release.

## Source and copyright policy

No full articles, paywalled materials, private research corpora, or long copied excerpts belong in this repository. Public material may contribute bibliographic metadata, links, short compliant quotations, and independently synthesized structural principles only. Local analysis belongs under ignored `research-private/`. See [copyright and source methodology](docs/copyright-and-sources.md).

## Contributing and security

Contributions are welcome under [CONTRIBUTING.md](CONTRIBUTING.md). Please report vulnerabilities according to [SECURITY.md](SECURITY.md), not in a public issue. By contributing, you agree that your contribution is licensed under the repository's [MIT License](LICENSE).

## License and citation

The project is available under the MIT License. Academic users can cite the collective authorship metadata in [CITATION.cff](CITATION.cff).
