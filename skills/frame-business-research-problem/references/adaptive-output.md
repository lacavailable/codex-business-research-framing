# Adaptive Output

Select the deliverable first, then the smallest profile that can render it
faithfully. The deliverable determines required content; the profile controls
detail and presentation.

## Deliverable router

Support at least these deliverables:

- interview answer;
- manuscript-ready paragraph;
- introduction opening;
- business-problem statement;
- model-setting explanation;
- research-question formulation;
- contribution paragraph;
- managerial implication;
- scenario comparison;
- assumption audit;
- full manuscript audit;
- computational-contribution explanation;
- research proposal framing.

Do not attach unrelated layers. A contribution paragraph does not automatically
need a full model mapping. A model-setting explanation does not automatically
need scholarly positioning. An introduction opening normally uses `compact`; a
diagnosis-and-repair request normally uses `standard`; a complete assumption or
manuscript audit uses `full-audit`.

## Minimum-sufficient-output filter

Before rendering each candidate statement or section, ask:

1. Did the user explicitly request it?
2. Is it necessary to prevent a material misunderstanding?
3. Does it provide a usable research-writing result?
4. Has the same substantive point already been stated?
5. Is it an internal process record rather than user-relevant content?
6. Is it a secondary caveat that can be omitted or compressed?
7. Does it help the user act, write, compare, or decide?

Retain content only when it was requested, removing it would create a material
fidelity problem, or it provides clear task-relevant value. Do not reveal
framework completeness merely to demonstrate that every internal check ran.

## Semantic non-repetition

Before returning:

1. identify central conclusions, limitations, unsupported pathways, evidence
   needs, and boundaries;
2. assign each substantive issue one visible home;
3. merge semantically duplicated statements;
4. retain the clearest occurrence; and
5. delete later restatements.

Necessary recurrence of a technical noun, a decision variable in a comparison
table, or a schema field in requested machine-readable output is not
repetition. Repeating that runtime is not profit or repeating one welfare
boundary under several headings is prohibited.

## Table versus prose

Use a compact table when three or more model objects must be compared, timing
or information is central, decisions/states/parameters/outcomes must be kept
distinct, candidates must be ranked, or private objective and welfare must be
separated. In `standard`, normally use at most one table with 3–8 rows and only
task-relevant columns. Do not show the complete DFC-12 table unless requested.

Use prose for one core correction, manuscript-ready narrative, a simple
mapping, or any deliverable whose flow a table would interrupt. Do not remove a
high-value mapping table merely to reduce length.

## Status classification

- `contradicted`: the proposed framing explicitly conflicts with the supplied
  model, including the wrong actor, decision, timing, information, feasible
  set, objective, or a removed material constraint.
- `not_supplied`: required information is absent from the supplied materials.
- `not_assessed`: the current task intentionally does not evaluate the layer.
- `unsupported`: a claim is made but model or evidence support is absent.
- `not_applicable`: the layer does not belong to the requested deliverable.

Do not call an explicit model mismatch unknown because empirical evidence is
missing. Never upgrade `not_supplied` or `not_assessed` semantics by calling
them stated, given, fixed, observed, or specified.

## Claim granularity

Audit singular versus plural; scenario versus instances; one experiment versus
repeated evidence; local versus general claims; model result versus empirical
observation; possibility versus demonstrated effect; benchmark result versus
operational performance; association versus causation; private objective versus
social welfare; and tested setting versus population.

Keep one scenario singular. A stylized model is not empirical evidence. One
benchmark does not establish general solver performance. A logical pathway is
not demonstrated operational value. A private objective is not welfare. A
specific parameter result is not universal. Use “may,” “could,” or “would
require evidence” for plausible but untested links.

## Clarification value

Ask a clarification only if the answer could materially change actor, decision,
timing, information, feasible set, behavior, objective, mechanism, scenario
eligibility, or candidate ranking. Ask no more than three questions and
prioritize actor, timing, and objective.

Do not block useful drafting for a missing company name, statistic, prevalence,
effect magnitude, citation, or implementation detail that can be marked
`not_supplied`.
