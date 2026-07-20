---
name: frame-business-research-problem
description: Frame, diagnose, compare, map, audit, or rewrite Operations Management, Information Systems, and Operations Research models as concrete business-research problems without changing their mathematical meaning. Use for model-to-business settings, research questions, introductions, assumption audits, scenario rankings, evidence-aware managerial narratives, or managerial implications in OM, IS, OR, and cross-domain analytical research.
---

# Frame Business Research Problem

Preserve research meaning before improving narrative appeal. Treat every plausible story as a candidate, not proof of fit.

## Execute in order

1. Select one mode: `create`, `diagnose`, `rewrite`, `compare-scenarios`, `map-model-to-business`, `audit-assumptions`, `draft-introduction`, or `draft-managerial-implications`.
2. Classify readiness with [input-readiness.md](references/input-readiness.md). Record missing information; never invent it.
3. Freeze objective, decisions, states, parameters, uncertainty, observations, constraints, timing, mechanism, outcomes, and derived quantities.
4. Complete the unchanged DFC-12 and all six gates using [framework.md](references/framework.md).
5. Set `ineligible` if any gate fails. Set `not_assessed` if any gate is unknown or unassessed. Continue to later layers only when every gate passes.
6. Map every supplied model using [model-to-reality-mapping.md](references/model-to-reality-mapping.md).
7. Apply managerial framing from [literature-grounded-framing.md](references/literature-grounded-framing.md) only after fidelity is eligible.
8. Apply [scholarly-positioning.md](references/scholarly-positioning.md) when the mode concerns a paper, research question, introduction, or contribution.
9. Apply the domain playbook: [om-framing.md](references/om-framing.md), [is-framing.md](references/is-framing.md), or [or-framing.md](references/or-framing.md). Load multiple playbooks for cross-domain work.
10. Label claims with [evidence-and-attribution.md](references/evidence-and-attribution.md). Do not invent company, market, performance, causal, or prevalence facts.
11. Produce the selected contract from [output-contracts.md](references/output-contracts.md) in the versioned [business-brief-schema.md](references/business-brief-schema.md).
12. Check [anti-patterns.md](references/anti-patterns.md), audit boundaries, and state the primary remaining weakness.

## Load specialized execution references

- Load [introduction-architecture.md](references/introduction-architecture.md) only for `draft-introduction` or an introduction-focused rewrite.
- Load [managerial-implications.md](references/managerial-implications.md) only for `draft-managerial-implications` or implication-focused diagnosis/rewrite.
- Consult the canonical [rule-registry.yaml](references/rule-registry.yaml) when applying a literature-derived rule; use the generated [source-to-rule-matrix.md](references/source-to-rule-matrix.md) when traceability is requested.
- Use [evaluation-rubric.md](references/evaluation-rubric.md) only to evaluate an output; preserve raw scores and apply layer minima and hard-failure policy separately.

## Enforce noncompensation

Do not let managerial appeal, scholarly novelty, evidence volume, or polished prose compensate for a fidelity failure. Do not rank an ineligible scenario. Rank eligible scenarios in this order:

1. model fit;
2. managerial significance;
3. structural tension;
4. evidence plausibility;
5. scholarly contribution potential;
6. boundary transparency.

## Use bundled assets and validation

- Start user intake from [research-framing-input-template.md](assets/research-framing-input-template.md) or [research-framing-input-template.json](assets/research-framing-input-template.json).
- Use [business-brief-template.md](assets/business-brief-template.md) for readable output.
- Use [model-mapping-template.md](assets/model-mapping-template.md), [scenario-comparison-template.md](assets/scenario-comparison-template.md), or [manuscript-sections-template.md](assets/manuscript-sections-template.md) only for the corresponding mode.
- Run `python scripts/validate_brief.py BRIEF.json` for deterministic BusinessBrief 1.0 or 2.0 validation.

Keep examples synthetic unless the user supplies verifiable evidence. Mark interpretive inferences. Preserve the model's timing, feasible set, mechanism, information, and objective. State what the analysis does not establish.
