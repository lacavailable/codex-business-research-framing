# OR Computational Contribution

Use this reference when interpreting formulations, algorithms, solver results,
bounds, or certificates.

## Keep the objects distinct

- **Optimal objective value:** the best value under the stated model.
- **Equivalent formulation:** a different representation with the same
  feasible decisions and true optimum.
- **Formulation strength:** the quality of a relaxation or bound, not a change
  in the underlying optimum.
- **LP relaxation and root gap:** pre-branching bound information.
- **Node count and runtime:** different computational measures; fewer nodes
  need not mean less time.
- **Feasible incumbent and incumbent quality:** an executable solution and its
  objective value or gap at a specified time.
- **Optimality gap:** the distance between incumbent and valid bound under a
  stated convention.
- **Exact certificate:** proof of optimality or another formal guarantee.
- **Pre-deadline solution:** a result available while the operational decision
  can still change.
- **Post-deadline certificate:** information arriving after execution.
- **Benchmark performance:** measured behavior on specified instances,
  hardware, solver, settings, and limits.
- **Operational value:** improvement connected through a decision process.
- **Realized profit:** an empirical outcome, not a synonym for objective value
  or speed.

## Enforce these rules

1. Runtime is not profit.
2. A stronger equivalent formulation does not change the true optimum.
3. Fewer nodes do not necessarily imply shorter runtime.
4. A smaller root gap is not automatically a managerial benefit.
5. A post-deadline certificate cannot improve a decision already executed.
6. Computational value requires an explicit operational pathway.
7. Do not claim realized financial or operational value without evidence.
8. Use singular “instance” unless multiple instances are supplied.
9. Distinguish observed runtime from expected runtime.
10. Distinguish incumbent feasibility from incumbent quality.
11. Distinguish later proof from decision-time quality knowledge.
12. Do not call a later proof operationally valuable for the completed
    decision. Retrospective assurance requires an explicit future audit,
    validation, or process-design pathway.
13. A benchmark result is conditional on supplied hardware, solver settings,
    instance, comparator, and time limit.
14. Do not invent repeated-run robustness or generalize one scenario into
    tested instances.

Valid pathways include meeting a decision deadline, enabling more frequent
reoptimization, solving larger instances, evaluating more scenarios, producing
a better feasible incumbent before execution, or providing a
decision-relevant certificate earlier. State which pathway is modeled,
observed, merely possible, or not supplied.

When reporting results, name the instance family, size dimensions, hardware,
solver and version, settings, time limit, comparator, repetitions or variability
when supplied, and whether the result concerns bounds, incumbents, certificates,
or runtime. Keep generalization outside tested conditions
`conditionally_supported` or `not_supplied`.
