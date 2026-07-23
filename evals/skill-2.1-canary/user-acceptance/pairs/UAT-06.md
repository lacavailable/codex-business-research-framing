# Product-owner review 06

**Task ID:** `OR-S02`

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

### Dispatch-deadline interpretation

The dispatch team must commit to an executable plan within 10 minutes; after that point, the selected dispatch cannot be revised. The solver’s pre-deadline result is therefore a **feasible incumbent**: it supplies a plan that satisfies the modeled operational constraints in time for execution.

Its quality at the 10-minute deadline is **not_assessed** unless the recorded objective value, a valid bound, or an optimality gap at minute 10 is available. The later result establishes that this same incumbent was optimal for the stated model, but that fact was not certified when the dispatch decision was made. It is accurate to say: *the team executed a feasible plan by the deadline that was subsequently proven optimal after 35 minutes.* It is not accurate to say the team executed a proven-optimal dispatch at minute 10.

The 35-minute proof is a **post-deadline optimality certificate**. It cannot improve the already executed dispatch, so it has no direct same-cycle operational value. It can, however, provide retrospective assurance that the committed plan was model-optimal and may support later auditing, solver validation, or redesign of future planning processes—**conditionally_supported**, provided those processes actually use the certificate.

Benchmark evidence supports only the observed computational pattern: feasible-plan availability by 10 minutes and optimality certification by 35 minutes on the tested instances and computing setup. General claims about solver reliability, scalability, or performance across different dispatch conditions are **not_supplied** without the instance family, hardware, solver settings, comparator, and repeated-run evidence.

The operational value that can be claimed is limited to meeting the decision deadline with a feasible modeled dispatch. Any claim of improved cost, service, profit, safety, or realized operational performance is **unsupported** unless the incumbent is compared with a relevant baseline and linked to those outcomes through the model or field evidence.

**Principal boundary:** optimality applies only to the formulated dispatch model and its inputs; it does not establish that the executed plan was best under unmodeled disruptions or that the 35-minute proof benefited that completed dispatch.
