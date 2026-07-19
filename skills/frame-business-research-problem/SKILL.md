---
name: frame-business-research-problem
description: Convert Operations Management, Information Systems, and Operations Research ideas, models, assumptions, algorithms, or findings into concrete business-research problems without changing their mathematical meaning. Use when creating, diagnosing, rewriting, or comparing managerial settings; mapping model objects to reality; auditing assumptions and evidence; or drafting introduction openings and managerial implications for OM, IS, or OR research.
---

# Frame Business Research Problem

Preserve research meaning before improving narrative appeal. Treat a plausible story as a candidate, not as proof of model fit.

## Run the workflow

1. Select exactly one mode: `create`, `diagnose`, `rewrite`, `compare-scenarios`, `map-model-to-business`, `audit-assumptions`, `draft-introduction`, or `draft-managerial-implications`.
2. Extract the mathematical or conceptual invariants that the narrative must not change. Separate decisions, states, parameters, observations, outcomes, and derived quantities.
3. Build all twelve DFC-12 fields. Read [framework.md](references/framework.md) and apply every consistency gate.
4. Mark a scenario ineligible if any actor, timing, information, behavior, constraint, or objective gate fails. Do not rescue it through polished prose.
5. Map supplied model objects to business meanings using [model-to-reality-mapping.md](references/model-to-reality-mapping.md). Do not turn a state into a choice or hidden information into decision-time information.
6. Apply the relevant domain playbook: [om-framing.md](references/om-framing.md), [is-framing.md](references/is-framing.md), or [or-framing.md](references/or-framing.md). Read more than one when the research crosses domains.
7. Label every externally checkable claim and every assumption using [evidence-and-attribution.md](references/evidence-and-attribution.md). Never invent company, market, performance, or causal facts.
8. Produce the selected mode contract from [output-contracts.md](references/output-contracts.md) inside the shared `BusinessBrief` envelope in [business-brief-schema.md](references/business-brief-schema.md).
9. Check [anti-patterns.md](references/anti-patterns.md), then report boundary conditions and the most important remaining weakness even when the result is strong.

## Rank scenarios

Gate scenarios before scoring them. Rank eligible candidates lexicographically by:

1. model fit;
2. managerial relevance;
3. evidence plausibility;
4. boundary transparency.

List ineligible candidates separately with failed gates. Never let commercial attractiveness offset a fidelity failure.

## Use bundled resources

- Copy and fill [business-brief-template.md](assets/business-brief-template.md) for a readable brief.
- Copy [model-mapping-template.md](assets/model-mapping-template.md) when a model is supplied.
- Copy [scenario-comparison-template.md](assets/scenario-comparison-template.md) for ranked alternatives.
- Copy [manuscript-sections-template.md](assets/manuscript-sections-template.md) for introduction or implications drafts.
- Run `python scripts/validate_brief.py BRIEF.json` for deterministic structural validation of a JSON `BusinessBrief`.
- Use [evaluation-rubric.md](references/evaluation-rubric.md) to score output quality; preserve the raw score and apply hard-failure caps separately.

## Apply final safeguards

- Keep examples synthetic unless the user supplies verifiable sources.
- Mark missing evidence as `unsupported_claim`; do not fabricate a citation.
- State when an inference is interpretive rather than model-implied.
- Preserve the model's decision timing, feasible set, mechanism, and objective.
- Distinguish what the analysis establishes from what remains outside scope.
