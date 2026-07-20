# Decision-Fidelity Canvas (DFC-12)

Use the canvas to construct or audit a candidate setting. Fill every field with model-grounded content or an explicit `unknown`.

## The twelve fields

| # | Field | Required question |
|---|---|---|
| 1 | Actor | Who owns the modeled decision and bears its consequences? |
| 2 | Trigger | What event creates the need to decide, in what environment? |
| 3 | Choices | What can the actor select at that moment? |
| 4 | Decision-time information | What is observed before the choice, and what remains unknown? |
| 5 | Stakes | Which measurable objective or outcome makes the choice consequential? |
| 6 | Frictions | Which limits, costs, rules, delays, or capacities define feasibility? |
| 7 | Mechanism | How do choices and uncertainty produce outcomes? |
| 8 | Trade-off | Why can no option improve every relevant outcome at once? |
| 9 | Counterfactual | What feasible policy, baseline, or alternative is the focal choice compared with? |
| 10 | Model mapping | Which business objects correspond to variables, parameters, states, constraints, and outputs? |
| 11 | Evidence status | Which statements are facts, assumptions, inferences, or unsupported claims? |
| 12 | Boundaries | Where should the interpretation stop? |

Make the trade-off structural. “Managers want better results” is not a trade-off. Name the competing consequences and the model feature that creates the conflict.

## Six consistency gates

Evaluate each gate as `pass`, `fail`, `unknown`, or `not_assessed` and give a short reason. A single `fail` makes the scenario ineligible. Use `unknown` when a material fact is missing and `not_assessed` when the available input does not permit the test; either status makes overall eligibility `not_assessed`, never eligible.

| Gate | Pass condition | Typical failure |
|---|---|---|
| Actor | The narrative decision maker controls the modeled decision. | A platform is described as choosing a user's private action. |
| Timing | The sequence of observations, choices, and outcomes matches the model. | A policy uses demand realized after the decision. |
| Information | Every input to the decision is available at decision time. | Latent type is treated as directly observed. |
| Behavior | Agent responses and operational dynamics match the modeled mechanism. | Substitution is claimed although demand is fixed and independent. |
| Constraints | Narrative feasibility matches the mathematical feasible region. | Capacity is described as flexible although it is fixed in the model. |
| Objective | The business goal matches the mathematical objective and welfare scope. | Revenue maximization is presented as social-welfare optimization. |

Do not average gate results. Do not call a failing scenario “mostly consistent.”

## Construction procedure

1. Freeze invariants from equations, algorithm definitions, assumptions, and experiment design.
2. Classify each symbol as decision, state, parameter, random variable, observation, outcome, or derived quantity.
3. Complete DFC-12 from those invariants.
4. Test the six gates with a concrete event sequence.
5. Reject or repair failed scenarios before drafting prose.
6. Surface uncertainty and boundaries rather than filling gaps with invented realism.
7. After every gate passes, apply managerial framing and scholarly positioning when the requested output requires them.

## Minimum fidelity record

Retain, at minimum: the original research objective; controlled decisions; decision sequence; observable information; uncertainty; feasible-set constraints; behavioral or operational response; evaluated outcomes; and claims not established by the model.
