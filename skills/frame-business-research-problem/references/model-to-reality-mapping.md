# Model-to-Reality Mapping

Map semantics before writing managerial prose. Use one row per material model object; split overloaded symbols into separate rows.

## Mapping columns

| Column | Question |
|---|---|
| `model_object` | What symbol, equation, rule, or algorithm component is being mapped? |
| `model_role` | Is it a decision, state, parameter, random variable, observation, constraint, objective, outcome, or derived quantity? |
| `business_meaning` | What concrete entity, action, limit, or result does it represent? |
| `decision_time_status` | Is it chosen, observed, estimated, latent, or realized later? |
| `fidelity_note` | What interpretation is permitted, and what tempting interpretation is not? |

## Mapping order

1. Identify the decision variables and who controls them.
2. Place observations, random variables, and outcomes on a timeline.
3. Translate the objective without expanding its welfare scope.
4. Translate every binding or conceptually important constraint.
5. Map transition, response, choice, queueing, or learning mechanisms.
6. Map outputs and guarantees, distinguishing model results from implementation outcomes.

## Role tests

- A **decision** can be selected by the actor within the feasible set.
- A **state** summarizes the system at a time but is not directly selected unless an action controls it by definition.
- A **parameter** is fixed within the modeled decision instance, even if estimated elsewhere.
- A **random variable** is unresolved at the relevant decision time.
- An **observation** is available to the actor at the stated time.
- A **constraint** limits allowed decisions or trajectories.
- An **objective** is the exact quantity optimized, including horizon and risk treatment.
- An **outcome** is produced after choices and uncertainty interact.
- A **derived quantity** is calculated rather than directly chosen or observed.

## Fidelity checks

- Preserve units, index sets, aggregation level, and time horizon.
- Do not map expected value to a guaranteed realized result.
- Do not call a heuristic output optimal without a certificate or proof.
- Do not treat an estimated latent type as directly known.
- Do not translate a penalty coefficient into a physical capacity unless the formulation supports it.
- Do not infer causality from an association, calibration, or computational comparison.
- Do not claim broader welfare, fairness, privacy, or safety gains unless those quantities enter the model or evaluation.

When no faithful concrete interpretation exists, record a mapping gap and narrow the narrative rather than inventing one.
