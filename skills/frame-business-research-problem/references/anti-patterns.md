# Common Anti-Patterns

Reject or repair these patterns before polishing prose.

| Anti-pattern | Why it fails | Repair |
|---|---|---|
| Named-company decoration | Creates unsupported facts and false specificity. | Use a synthetic organization or cite verified facts. |
| Future-information leak | Gives the actor outcomes not observed at decision time. | Restore the timeline and use forecasts or distributions actually supplied. |
| Actor swap | Assigns the modeled choice to an entity that does not control it. | Reassign the actor or reject the setting. |
| State-as-decision | Treats inventory, demand, type, or waiting time as directly chosen. | Map the controllable action and show how it affects the state. |
| Objective inflation | Converts revenue or cost optimization into welfare, fairness, or sustainability improvement. | State the exact objective and list excluded outcomes. |
| Constraint laundering | Describes a hard constraint as a soft preference or ignores it. | Name the feasible-set restriction in business terms. |
| Mechanism grafting | Adds substitution, strategic behavior, congestion, or learning absent from the model. | Remove it or explicitly extend the model outside the current claim. |
| Trivial trade-off | Says only that managers want “more value at lower cost.” | Link competing outcomes to a real mechanism or constraint. |
| Causal upgrade | Turns correlation, calibration, or simulation into a causal effect. | Qualify as inference or provide a valid causal design. |
| Benchmark universalism | Generalizes computational results beyond tested instances. | State instance, solver, hardware, and time-limit boundaries. |
| Exactness inflation | Calls a heuristic or time-limited incumbent optimal. | Report feasibility, bound, gap, and certificate accurately. |
| Assumption hiding | Presents modeling convenience as observed reality. | Label and explain every material assumption. |
| Story-driven model change | Alters decisions, timing, objective, or behavior for narrative appeal. | Freeze invariants first; choose a different setting if needed. |
| Vague manager | Names “businesses” without an accountable decision maker. | Identify the role with authority over the choice. |
| Generic stakes | Claims “efficiency” without a measurable outcome. | Name the objective unit and consequence. |

## Red-team questions

- Could the actor execute every stated choice?
- Did any information enter before it becomes observable?
- Does the story use the same objective, horizon, and risk treatment as the model?
- Is every claimed response produced by the modeled mechanism?
- Does every narrative option remain mathematically feasible?
- Would the narrative still sound compelling if all unsupported facts were removed?
- Is the strongest managerial implication actually established, or only hoped for?

If a repair changes the mathematical model, present it as a proposed extension rather than as a rewrite of the existing research.
