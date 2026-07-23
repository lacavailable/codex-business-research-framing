---
name: frame-business-research-problem
description: Frame, diagnose, compare, map, audit, or rewrite Operations Management, Information Systems, and Operations Research models as concrete business-research problems without changing their mathematical meaning. Use for model-to-business settings, research questions, introductions, assumption audits, scenario rankings, evidence-aware managerial narratives, or managerial implications in OM, IS, OR, and cross-domain analytical research.
---

# Frame Business Research Problem

Preserve research meaning before improving narrative appeal. Treat every plausible story as a candidate, not proof of fit.

## Execute internally

1. Select one mode: `create`, `diagnose`, `rewrite`, `compare-scenarios`, `map-model-to-business`, `audit-assumptions`, `draft-introduction`, or `draft-managerial-implications`.
2. Select the requested deliverable before selecting a profile. Use [adaptive-output.md](references/adaptive-output.md) for deliverable routing, minimum-sufficient content, table-versus-prose choice, and clarification value.
3. Select `micro`, `compact`, `standard`, or `full-audit` with [response-profiles.md](references/response-profiles.md). Use `full-audit` only when explicitly requested.
4. Classify readiness with [input-readiness.md](references/input-readiness.md). Record missing information; never invent it.
5. Freeze objective, decisions, states, parameters, uncertainty, observations, constraints, timing, mechanism, outcomes, and derived quantities.
6. Complete the unchanged DFC-12 and all six gates using [framework.md](references/framework.md).
7. Set `ineligible` if any gate fails. Set `not_assessed` if any gate is unknown or unassessed. Continue to later layers only when every gate passes.
8. Map every supplied model using [model-to-reality-mapping.md](references/model-to-reality-mapping.md).
9. For `create` or setting-development work, generate and classify candidate interpretations internally with [setting-construction.md](references/setting-construction.md); show only the strongest eligible candidate unless comparison is requested.
10. Apply managerial framing from [literature-grounded-framing.md](references/literature-grounded-framing.md) only after fidelity is eligible. Use [managerial-value-pathway.md](references/managerial-value-pathway.md) for operational, managerial, or social outcome claims.
11. Apply [scholarly-positioning.md](references/scholarly-positioning.md) only for a paper, research question, introduction, or contribution task. Route contribution type with [contribution-types.md](references/contribution-types.md).
12. Apply the domain playbook: [om-framing.md](references/om-framing.md), [is-framing.md](references/is-framing.md), or [or-framing.md](references/or-framing.md). For computational OR claims, also load [or-computational-contribution.md](references/or-computational-contribution.md).
13. Label claims with [evidence-and-attribution.md](references/evidence-and-attribution.md). Apply the claim-granularity and status rules in [adaptive-output.md](references/adaptive-output.md). Do not invent company, market, performance, causal, literature, or prevalence facts.
14. Check [anti-patterns.md](references/anti-patterns.md), audit boundaries, and identify the primary remaining weakness.

## Render for the user

Follow [output-contracts.md](references/output-contracts.md). For ordinary Markdown, put the requested usable deliverable first. Apply the minimum-sufficient-output filter before rendering; expose internal checks only when the deliverable requires them.

Give each substantive conclusion, limitation, unsupported pathway, evidence need, and boundary one visible home. Merge semantic duplicates, retain the clearest occurrence, and remove later restatements. Necessary repeated technical nouns, table labels, and explicitly requested schema fields are not substantive repetition.

Use exactly these visible support statuses when a status is useful: `supported`, `conditionally_supported`, `unsupported`, `contradicted`, `not_supplied`, `not_assessed`, and `not_applicable`. Reserve internal `fail` for a material gate contradiction.

Produce the full [business-brief-schema.md](references/business-brief-schema.md) record only when the user requests machine-readable output or a full audit. Preserve BusinessBrief 1.0 and 2.0 compatibility.

Before returning, verify singular/plural scope, scenario count, tested conditions, causal strength, decision-time knowledge, private objective versus welfare, and every link in any value pathway. Never describe a `not_supplied` or `not_assessed` element as stated, given, fixed, observed, or specified.

## Load specialized execution references

- Load [introduction-architecture.md](references/introduction-architecture.md) only for `draft-introduction` or an introduction-focused rewrite.
- Load [managerial-implications.md](references/managerial-implications.md) only for `draft-managerial-implications` or implication-focused diagnosis/rewrite.
- Use [original-examples.md](references/original-examples.md) when a synthetic rendering example would clarify profile, domain, evidence, or computational-claim handling. Never copy private source wording.
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
- Use [business-brief-template.md](assets/business-brief-template.md) only for requested structured or full-audit output.
- Use [model-mapping-template.md](assets/model-mapping-template.md), [scenario-comparison-template.md](assets/scenario-comparison-template.md), or [manuscript-sections-template.md](assets/manuscript-sections-template.md) only for the corresponding mode.
- Run `python scripts/validate_brief.py BRIEF.json` for deterministic BusinessBrief 1.0 or 2.0 validation.

Keep examples synthetic unless the user supplies verifiable evidence. Mark interpretive inferences. Preserve the model's timing, feasible set, mechanism, information, and objective. State what the analysis does not establish.
