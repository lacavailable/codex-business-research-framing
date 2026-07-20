# Anti-Patterns

Reject or repair these patterns before polishing prose. Rule links refer to the canonical [rule registry](rule-registry.yaml).

| ID | Anti-pattern | Why it fails | Repair | Rule links |
|---|---|---|---|---|
| AP-01 | Broad trend opening without a decision | A topic or unsupported “increasingly important” claim supplies no actor or choice. | Open with a consequential decision and source any trend claim. | MGR-001, EVD-001, SCH-003 |
| AP-02 | Unsupported importance | Confidence cannot establish prevalence, magnitude, or stakes. | Supply traceable evidence or label the claim unsupported. | EVD-001 |
| AP-03 | Generic gap spotting | “Little research has studied” does not explain why an omission matters. | Identify a limitation, anomaly, tension, or challenged assumption and its consequence. | SCH-001, SCH-002, SCH-003 |
| AP-04 | Context-only novelty | A new industry, geography, dataset, or technology need not change understanding. | State the changed mechanism, construct, boundary, or inference. | SCH-001, SCH-002 |
| AP-05 | State treated as a decision | Exogenous, uncertain, or latent conditions are not directly controlled. | Map the actual action and show how it affects the state. | IS-001 |
| AP-06 | Recommendation before mechanism | Advice lacks a model-supported path from choice to outcome. | State condition, mechanism, consequence, and implementation pathway. | MGR-002, IMP-001 |
| AP-07 | Actionability without an actor | “Managers should” hides authority and accountability. | Name the role that controls the decision. | MGR-001, IMP-001 |
| AP-08 | Free improvement without trade-off | A claim that everything improves hides a constraint, objective conflict, or omitted outcome. | Name competing consequences and the feature creating the tension. | MGR-002 |
| AP-09 | Hidden information treated as observed | The narrative gives the actor future, latent, private, or restricted information. | Restore the information set and timing; otherwise fail the information gate. | IS-001 |
| AP-10 | Company example treated as general evidence | One named organization does not establish a general mechanism or prevalence. | Use a synthetic illustration or bound a verified case to what its source establishes. | EVD-001, PRAC-001 |
| AP-11 | Dramatic realism changes the model | Added behavior or institutions create a different mathematical problem. | Freeze invariants; label any change as a model extension. | MGR-002 |
| AP-12 | Computational speed treated as profit | Runtime has value only through a decision pathway and deadline. | State when a better incumbent, bound, or certificate changes an action. | IMP-001, OR-001 |
| AP-13 | Private objective treated as social welfare | Revenue, profit, or private loss does not include unmodeled externalities. | State the exact objective and excluded welfare outcomes. | IS-001, OR-001 |
| AP-14 | Hidden counterconditions | A recommendation appears universal because failure conditions are omitted. | State applicability, counterconditions, and boundaries beside the claim. | MGR-002, IMP-001 |
| AP-15 | Contribution restates paper sections | “We formulate, solve, and test” lists activities rather than a change in understanding. | Name contribution type, novelty relative to prior work, and boundary. | SCH-001, SCH-003 |
| AP-16 | Publisher-like confidence without evidence | Fluent practitioner prose can conceal unsupported or overgeneral claims. | Preserve evidence labels and original expression; do not imitate a publisher. | EVD-001, PRAC-001 |

## Fidelity-specific checks

- Reject actor swaps, future-information leaks, constraint laundering, objective inflation, and mechanism grafting.
- Do not call a failed scenario “mostly consistent.”
- Do not call a heuristic or time-limited incumbent optimal without the relevant proof or certificate.
- Do not generalize computational performance beyond tested instances, solvers, hardware, and limits.
- Present a repair that changes the model as a proposed extension, never a prose edit.

## Red-team questions

- Can the named actor execute every stated choice?
- Is every input available before the associated decision?
- Does the story preserve objective, horizon, risk treatment, feasible region, and mechanism?
- Would the narrative remain consequential after unsupported facts are removed?
- Is the claimed implication established, inferred, or merely hoped for?
- Which countercondition would reverse or invalidate the recommendation?
