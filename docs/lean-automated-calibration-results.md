# Lean automated calibration results

## Outcome

Status: `fail` at the D2 development gate.

D1 passed its engineering-sentinel criteria. D2 then completed all eight development cases using 32 required role calls, three conditional adjudications, and one schema-invalid retry: 36 authoritative attempts against a 40-call ceiling. Twelve of the thirteen registered checks met their assigned role, but the blocking conditional-adjudication gate failed at 37.5% (3/8) against the preregistered maximum of 30%. Prestige-label invariance also failed as a diagnostic. The evaluator was therefore not frozen, validation did not begin, and Skill 2.1 development was not authorized.

This is an automated source-grounded triangulation result, not expert validation. No human experts participated. Available Codex variants are reported conservatively as same-family.

## Development results

| Measure | D1 | D2 | Requirement or role |
|---|---:|---:|---|
| Complete cases | 4/4 | 8/8 | Complete |
| Valid evidence spans | 100% | 97.6% | At least 95% |
| Applicability recovery | 100% | 100% | At least 95% |
| Material-defect detection | — | 100% | At least 90% |
| Material-fidelity ordering | 100% | 100% | At least 90% |
| Fidelity false-positive rate | 0% | 4.17% | At most 5% |
| Category localization | 87.5% | 93.75% | At least 80% |
| Structure `high` | 4/4 | 8/8 | D1 at least 3; D2 at least 6 |
| Conditional adjudication | 25% | 37.5% | D2 at most 30% — **failed** |
| Prestige effects | 1 | 5 | Diagnostic — failed |

The three D2 adjudications concerned evidence localization in OM-P02, managerial-framing applicability in MGMT-P02, and applicability plus actor-evidence localization in IS-P02. All disputes were resolved, but their frequency exceeded the frozen tolerance. The original passages produced no fidelity hard failures.

## Resource and preservation audit

- D1 used 18 authoritative attempts: 16 required calls, one adjudication, and one schema-invalid retry.
- D2 used 36 authoritative attempts: 32 required calls, three adjudications, and one schema-invalid retry; four slots remained unused.
- A D2-only Role A prompt version enumerates the canonical 15 check keys after the first D2 attempt demonstrated that the earlier prompt underspecified them. The invalid attempt remains counted.
- The malformed preserved MGMT-P02 context packet was not changed. A valid task-local repaired copy and repair record remain ignored in private storage.
- No private passage, evidence span, raw role output, construction identity, or copyrighted wording is tracked.
- The expert and automated holdouts remain unopened.

## 28-item final report

1. Method label: automated source-grounded triangulation.
2. Human experts: none.
3. Model-family claim: available variants treated as same-family.
4. Baseline commit: `c7a6e0245f682fc0f8609a69e546d7cb39f35e49`.
5. Working branch: `automated-triangulation-v0.3-lean-complete`.
6. PR #3 records credited: zero; retained as diagnostic evidence only.
7. Private source passages tracked: zero.
8. Expert holdout: unopened.
9. Automated holdout: unopened.
10. D0 status: pass with zero model calls.
11. D1 completed cases: four.
12. D1 authoritative attempts: eighteen.
13. D1 status: pass.
14. D2 completed cases: eight across four domains.
15. D2 required records: 32/32 complete.
16. D2 adjudications: three.
17. D2 authoritative attempts: 36/40 maximum.
18. Evidence-span validity: 97.6%.
19. Combined applicability recovery: 100%.
20. Material-defect detection and ordering: 100% each.
21. Fidelity false-positive rate: 4.17%.
22. Category localization: 93.75%.
23. Structure-high coverage: 8/8 and four domains.
24. Blocking failure: adjudication rate 37.5% exceeds 30%.
25. Diagnostic failure: five prestige effects; one paraphrase disagreement remained within tolerance.
26. Evaluator freeze and validation: not authorized and not started.
27. Skill, benchmark, tag, and release changes: none.
28. Next priority: reduce material A/B/C disagreement using development-only prompt and applicability repairs, then create a new D2 freeze candidate without inspecting validation or either holdout.

## Resume boundary

Do not proceed to validation or Skill development from this result. Any repair must be justified by the sealed D1/D2 development evidence, produce a new preregistered development run, retain all prior attempts, and keep both holdouts closed.
