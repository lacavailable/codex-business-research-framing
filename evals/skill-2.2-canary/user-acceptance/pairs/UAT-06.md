# Product-owner development review 06

**Task:** `OR-S02`

## Request

Frame this computational result for an operational audience. A solver produces a feasible incumbent before a 10-minute dispatch deadline and proves its optimality after 35 minutes. The executed dispatch cannot be changed after 10 minutes. Distinguish incumbent quality, certificate timing, benchmark evidence, and any operational value that can or cannot be claimed.

## Output A

# Dispatch decision under a fixed 10-minute deadline

**Eligibility:** `not_assessed` — the supplied result fixes the computational timeline, but not the dispatch objective, constraints, data, or operational outcome measures.

## Operational reading

A dispatch authority must select and execute a feasible dispatch within 10 minutes. The solver produced a feasible incumbent before that deadline, so it supplied a dispatch that could be executed on time. The solver did not establish optimality until minute 35, after execution was irrevocable.

| Item | What the result establishes | What it does not establish |
|---|---|---|
| Incumbent at 10 minutes | A feasible dispatch was available for execution. | Its optimality, its gap to the optimum, or its improvement over any baseline at that time. |
| Certificate at 35 minutes | Under the stated optimization model and solver termination conditions, the already-found incumbent was optimal. | A chance to revise the executed dispatch, or a better realized operational outcome. |
| Benchmark evidence | The solver found the eventual model-optimal solution early and spent a further 25 minutes certifying it for this tested instance and setup. | General runtime performance, performance on future dispatches, or benefits on different hardware, instances, data, or time limits. |
| Operational value | Timely feasibility has value if a feasible dispatch is required to keep operations running by minute 10. | Profit, service, safety, welfare, or cost gains without a modeled or measured link to those outcomes. |

## Managerial implication

For a dispatch team with no authority to change the plan after minute 10, the relevant deployable output is the **best feasible incumbent available at minute 10**. The later certificate is valuable as retrospective validation and benchmark evidence: it shows that this executed incumbent was model-optimal, assuming the model and data were valid. It has no direct value for that completed dispatch because it arrives after the decision can be changed.

The operational trade-off is therefore solution assurance versus decision latency. A longer run may provide a proof, but only pre-deadline improvements in the incumbent can change the executed action.

## Claim boundaries

- Do not describe the 10-minute dispatch as “optimal at decision time”; it was only known to be feasible then.
- Do not treat the 35-minute proof as an operational improvement to an irrevocable dispatch.
- Do not infer real-world performance from model optimality or a single benchmark run.
- To claim stronger operational value, report the 10-minute objective value and gap or bound, the baseline it is compared with, tested instance families, hardware and solver settings, and evidence connecting the modeled objective to operational outcomes.

**Primary remaining weakness:** the result does not state how the 10-minute incumbent compares with an operational baseline or which real operational outcome the optimization objective represents.

## Output B

## Computational contribution

The solver produces an executable dispatch plan within the 10-minute decision window. This is the decision-relevant result: the plan is feasible and can be executed before dispatch is irrevocably fixed. Its quality at that moment should be reported using its objective value and, if available, its optimality gap relative to a valid bound.

The proof obtained at 35 minutes establishes that this same plan is optimal for the stated model instance. That certificate is valuable as retrospective validation of the model-based decision, but it arrives too late to improve the dispatch already executed. It therefore must not be described as having improved real-time dispatch quality.

| Object | What is established | Operational interpretation |
|---|---|---|
| 10-minute incumbent | A feasible dispatch is available before execution. | `supported`: it can support the fixed dispatch decision. |
| Incumbent quality | Objective value, and possibly a decision-time gap, characterize how good that plan is under the model. | `conditionally_supported`: meaningful only if the objective, bound, and gap convention are reported. |
| 35-minute certificate | The incumbent is proven optimal for the modeled instance. | `supported`: retrospective assurance; not a real-time improvement. |
| Benchmark evidence | The reported timings describe this solver run under its supplied instance, hardware, settings, and time limit. | `not_supplied`: general performance, robustness, or comparison against alternatives cannot be claimed without those details. |

The operational contribution is thus deadline-feasible decision support with a later exactness certificate—not a claim that the certificate improved an irreversible dispatch, generated profit, or improved service. Those broader outcomes would require evidence linking the pre-deadline incumbent to the dispatch process and realized operational results.
