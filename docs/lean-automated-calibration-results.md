# Lean automated calibration results

## Outcome

Status: `paused_resource_limit`.

D0 passed all deterministic prerequisites with zero model calls: nine new schemas are valid, the policy contains thirteen core gates, no private path is tracked, and both holdouts remain unopened. D1 has a deterministic 16-call plan for the four domain sentinels, but it was paused before its first authoritative call because fresh isolated role execution was unavailable. D2 and validation are planned but have not started.

This is not a calibration pass or failure. No lean silver decision, reliability estimate, evaluator freeze, Skill change, holdout result, benchmark claim, tag, or release exists.

## Final-report checklist

1. Method label: automated source-grounded triangulation.
2. Human experts: none.
3. PR #3 status: incomplete due to execution capacity.
4. Prior judgments credited: zero.
5. Private contexts reusable: yes, as inputs only.
6. Expert holdout: unopened.
7. Automated holdout: unopened.
8. Private tracked paths: none.
9. D0 model calls: zero.
10. D0 status: pass.
11. D1 sentinels: OM-P01, IS-P01, OR-P01, MGMT-P01.
12. D1 budget: 16 calls.
13. D1 completed calls: zero.
14. D1 status: paused resource limit.
15. D2 budget: 40 calls.
16. D2 status: planned.
17. Validation budget: 40 calls.
18. Validation status: planned.
19. Conditional adjudication target: at most 30%.
20. Tier A core gates assessed: privacy and holdout preservation only.
21. Tier A passed: no.
22. Evaluator frozen: no.
23. Skill modified: no.
24. Experimental release eligible: no.
25. Required next action: resume the exact missing D1 calls in fresh contexts, then proceed only through the frozen stage sequence.

## Resume procedure

Run `tools/plan_triangulation_run.py verify --manifest evals/automated-triangulation/lean-v1/runs/D1.manifest.json`, execute only calls whose status is not `completed`, validate each output against its role schema, checkpoint it atomically, and regenerate the sanitized progress record after every case. Do not count the PR #3 records or open either holdout.
