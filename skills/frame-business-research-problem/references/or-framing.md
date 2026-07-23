# OR Framing Playbook

Use this playbook for formulations, algorithms, bounds, decomposition, and computational decision support.

## Narrative sequence

Build the visible framing in this order:

1. operational decision;
2. mathematical abstraction;
3. computational obstacle;
4. formulation or algorithmic contribution;
5. operational pathway;
6. evidence boundary.

Load [or-computational-contribution.md](or-computational-contribution.md) for
runtime, gap, incumbent, certificate, formulation, or solver claims.

## Formulation semantics

Map every important decision variable to an actionable choice. Translate the objective with its units, horizon, and risk treatment. Describe the feasible region through operational rules, not merely equation names. Keep state, auxiliary, and linearization variables distinct from managerial decisions.

## Uncertainty

State whether uncertainty is stochastic, robust, distributionally robust, scenario-based, or ignored. Identify which data are available before each decision stage. Do not present perfect-information experiments as deployable policies.

## Scale and bottlenecks

Name the size dimensions that drive computational difficulty: facilities, products, periods, scenarios, users, arcs, or constraints. Identify the actual bottleneck—formulation strength, enumeration, memory, communication, or solver convergence—without implying universal performance.

## Exactness and certificates

Use `exact` only when the method returns a provably optimal solution under the stated model and termination conditions. Distinguish feasible solutions, lower or upper bounds, optimality gaps, and certificates. A stronger MILP formulation can improve bounds or solution time without changing the feasible business decisions; verify equivalence before making that claim.

## Operational value of speed

Connect runtime to a real decision deadline, reoptimization cadence, scenario volume, or attainable solution quality. Do not claim managerial value from faster benchmarks alone. State hardware, solver, time limit, instance family, and whether speed enables a different operational action.

## OR trade-off prompts

- Solution quality versus decision latency.
- Model detail versus solvability or data burden.
- Robustness versus expected performance.
- Centralized efficiency versus autonomy or implementation cost.
- Optimality guarantees versus scalability.

Keep computational findings scoped to tested instances and conditions. Do not convert an algorithmic speedup into a profit, service, or welfare claim without an explicit modeled or empirical link.
