# Original Adaptive Examples

All examples are synthetic. They demonstrate structure and boundaries; they are
not empirical evidence and must not be copied mechanically.

## 1. Micro versus compact versus standard

**Supplied model:** A retailer chooses at most six products before demand.
Customers substitute among offered products under a Markov-chain choice model;
the objective is expected margin.

**Micro:** The retailer chooses a capacity-limited assortment before demand,
accounting for how unavailable products redirect demand among offered items;
the model compares feasible assortments by expected margin, not by observed
individual customer paths.

**Compact:** The retailer must select at most six products before demand is
realized. Because removing an item can redirect rather than eliminate demand,
each slot has both direct-demand and substitution value. The Markov-chain
choice model captures those interactions and compares feasible assortments by
expected margin. The business problem is therefore to choose the limited
portfolio that best manages substitution, subject to the supplied transition
parameters; the model does not establish that individual customer paths are
observed.

**Standard:** Diagnose the draft first if it names the wrong actor or changes
timing, then provide the compact paragraph. Add a short object mapping only if
the draft confuses product inclusion, realized demand, and expected margin.
State one evidence need—the basis for transition parameters—and one boundary:
individual paths are not observed unless supplied.

## 2. Compact can be complete below its typical range

**Request:** Correct one manuscript sentence that treats realized waiting time
as the staffing decision.

**Answer:** The service operator chooses staffing before uncertain requests
arrive; waiting time is an outcome jointly determined by that staffing choice
and realized demand, not a decision variable.

The answer is complete without padding to a minimum word count.

## 3. Standard mapping where a table is better

A platform observes a noisy score, allocates scarce human review, then chooses
a moderation action after review. A compact mapping prevents the true latent
type from being moved into the decision-time information set:

| Object | Role | When known or chosen | Boundary |
|---|---|---|---|
| Latent type | state | not directly observed at allocation | not the score |
| Risk score | signal | observed before allocation | noisy proxy |
| Review allocation | decision | chosen from the fixed budget | not moderation |
| Moderation action | later action | chosen after review | depends on review |

The essential evidence need is the score/review process in the intended
setting. Platform revenue is not social welfare.

## 4. Explicit mismatch is contradicted

If a regulator allocates inspections to minimize system harm, a story in which
a vendor chooses prices to maximize profit is `contradicted`: actor, decision,
feasible action, and objective conflict with the supplied model. The repair is
to retain regulator inspection allocation, not to label the commercial story
unknown.

## 5. Missing information is not supplied

A scheduling description identifies the actor and decision but says nothing
about which forecasts are available before scheduling. Decision-time forecast
availability is `not_supplied`; it is not `contradicted` unless the proposed
story explicitly gives the actor information that the model withholds.

## 6. One scenario remains singular

**Supplied:** One routing scenario on one stated machine reaches a feasible
incumbent at minute eight.

**Faithful:** “On the supplied scenario, the solver found a feasible incumbent
at minute eight.”

Do not write “across the tested instances,” “robustly,” or “in repeated runs.”

## 7. One benchmark cannot be generalized

An equivalent formulation ran 40% faster for the supplied benchmark instance.
That observation is conditional on the stated instance, hardware, solver,
settings, and limit. It does not establish expected runtime, general solver
performance, a changed optimum, or realized profit.

## 8. Three internal settings, one visible recommendation

For a model that allocates inspections under noisy risk signals, the Skill may
consider internally: regulator safety inspection (`direct_interpretation`),
platform account review (`plausible_application`), and vendor price targeting
(`model_extension`). If the regulator interpretation best preserves actor,
decision, timing, information, and objective, show only that framing and its
main boundary. Do not expose the rejected list unless comparison is requested.

## 9. Computational value pathway

`faster runtime`
→ `incumbent available before dispatch` (`requires operational evidence`)
→ `more frequent reoptimization` (`logically plausible`)
→ `potential service or cost improvement` (`requires empirical evidence`)

The benchmark supports only the first object unless the later links are
supplied. A certificate after dispatch cannot improve the completed dispatch;
future audit value would need a separate process pathway.

## 10. Contribution-type routing

For an equivalent MILP with a tighter relaxation, use the formulation route:
explain equivalence, relaxation strength, computational consequence, unchanged
true optimum, and a conditional deadline pathway. Do not use an empirical
causal template or a generic managerial-benefit narrative.

For a platform governance mechanism with strategic users, use the IS design or
governance route: identify information, incentives, induced behavior, the
organizational problem, and implementation boundary.

## 11. Concise full audit without a repeated boundary

**Eligibility:** `ineligible`.

| Element | Supplied model | Proposed story | Status |
|---|---|---|---|
| Actor | regulator | vendor | `contradicted` |
| Decision | inspection allocation | price | `contradicted` |
| Objective | system harm | profit | `contradicted` |
| Timing/information | absent | absent | `not_supplied` |

**Repair:** Frame the problem as regulator inspection allocation that minimizes
the supplied harm objective. Vendor pricing would be a `model_extension`.

**Boundary:** No vendor profit implication follows from this model.

The boundary appears once rather than in diagnosis, repair, evidence, and
conclusion sections.

## 12. Clarification is necessary

**Request:** “Frame this allocation model for a business paper.” The materials
alternately describe the allocator as a hospital and an insurer, and they use
different objectives.

**Question:** Which actor chooses the allocation, and is its modeled objective
patient delay or insurer cost?

The answer changes actor and objective, so clarification is worth requesting.

## 13. Clarification should not be asked

**Request:** “Rewrite this supplied queueing model as a concise operating
problem.” The company name and empirical prevalence are absent.

Draft the model-faithful operating paragraph immediately. Mark company-specific
scope and prevalence `not_supplied` only if material; do not block on either.
