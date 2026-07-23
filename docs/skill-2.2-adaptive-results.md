# Skill 2.2 adaptive experimental results

## 1–4. Branch, PR, files, and protected evaluator history

- Branch: `skill-v0.3-adaptive-experimental`.
- Pull request: to be opened as the draft **Skill 2.2 adaptive experimental**
  against `main`.
- Skill files changed:
  - `skills/frame-business-research-problem/SKILL.md`
  - `references/response-profiles.md`
  - `references/output-contracts.md`
  - `references/adaptive-output.md`
  - `references/contribution-types.md`
  - `references/setting-construction.md`
  - `references/managerial-value-pathway.md`
  - `references/or-computational-contribution.md`
  - `references/original-examples.md`
- Calibration evaluator schemas, D1, D2, D2R, holdouts, historical
  attestations, private corpus hashes, and PR #5–#8 sealed result artifacts were
  not changed. The PR #7 Skill 2.1 canary, tool, and result retain their
  original Git objects.

## 5–14. Product implementation

5. **Profiles:** added `micro` (typical 35–100, soft maximum 120), revised
   `compact` (80–180, soft maximum 220), revised `standard` (180–450, soft
   maximum 500), and made `full-audit` explicit-only with no universal word
   range. Ranges are not minimums and padding is prohibited.
6. **Deliverables:** routing now selects interview answer, manuscript paragraph,
   introduction opening, business-problem statement, model explanation,
   research question, contribution, implication, scenario comparison,
   assumption/full audit, computational explanation, or proposal framing before
   profile.
7. **Minimum sufficient output:** a seven-question internal filter retains only
   requested content, fidelity-critical safeguards, or clearly actionable
   value.
8. **Table/prose:** standard output normally permits one 3–8-row table when
   three or more objects, timing, information, states, outcomes, scenarios, or
   welfare distinctions benefit from it; narrative deliverables remain prose.
9. **Statuses:** `contradicted`, `not_supplied`, `not_assessed`, `unsupported`,
   and `not_applicable` have distinct operational rules. Unknown elements must
   not be called stated, given, fixed, observed, or specified.
10. **Claim granularity:** singular/plural, scenario/instances,
    model/empirical, local/general, possibility/demonstration,
    benchmark/operation, association/causation, private objective/welfare, and
    tested setting/population are checked before rendering.
11. **Contribution type:** analytical mechanism, formulation, algorithmic,
    empirical causal, IS design/governance, and policy/mechanism-design routes
    were added.
12. **Scenario construction:** up to three internal interpretations are
    classified as `direct_interpretation`, `plausible_application`,
    `illustrative_analogy`, or `model_extension`; only the strongest eligible
    framing and main boundary are shown by default.
13. **Managerial value:** every claim follows
    `model result → decision-process effect → operational intermediate outcome
    → business/social outcome`, with each link labeled by support strength.
14. **Clarification:** at most three questions are asked only when missing
    information could change fidelity, eligibility, or candidate ranking.

## 15–16. Deterministic checks and call accounting

The local suite passed 83 tests. The official Skill validator passed on the
source and a clean extracted package. Package checksum verification, local
links, repository audit, privacy audit, and copyright/fingerprint audit passed.
No file is tracked under `research-private`.

Exactly 16 authoritative calls were planned and used: eight
`gpt-5.6-terra`/high candidate generations and eight
`gpt-5.6-sol`/high single-judge blinded comparisons. The eight v0.2 outputs
were reused, not regenerated. There were zero retries, replacements,
adjudications, or additional model roles.

## 17–20. Per-task rendering, structure, and repetition

| Task | Profile compliant | Words | Headings | Table rows | Avoidable repetition |
|---|---:|---:|---:|---:|---:|
| OM-C01 | yes | 66 | 0 | 0 | yes |
| OM-S02 | yes | 187 | 2 | 3 | no |
| IS-C01 | yes | 101 | 0 | 0 | no |
| IS-S02 | yes | 265 | 4 | 5 | no |
| OR-C01 | yes | 81 | 0 | 0 | no |
| OR-S02 | yes | 256 | 1 | 4 | no |
| XD-F01 | yes | 790 | 11 | 38 | yes |
| XD-F02 | yes | 1,210 | 12 | 48 | yes |

All eight outputs satisfied the frozen adaptive contract; five of eight had no
avoidable substantive repetition. The two full audits remained structurally
large, and neither was shorter or simpler than its PR #7 Skill 2.1 reference.

## 21–23. Claims, scope, and blinded outcomes

The blind judges found no unsupported factual claim in any candidate and no new
candidate scope/generalization error. The frozen deterministic unsupported-fact
check nevertheless flagged the list index `4.` in XD-F01 as an empirical
quantity because nearby text mentioned profits and welfare. This is a known
false positive against the preregistered exclusion for list numbers; it is
preserved rather than repaired after freeze, so blocking gate 2 remains failed.

Blind outcomes:

| Task | Outcome for Skill 2.2 |
|---|---|
| OM-C01 | loss |
| OM-S02 | win |
| IS-C01 | win |
| IS-S02 | loss |
| OR-C01 | win |
| OR-S02 | win |
| XD-F01 | loss |
| XD-F02 | tie |

Skill 2.2 won four of the six non-full-audit tasks, meeting the frozen
development preference threshold. This is known-task development evidence, not
a superiority result.

## 24–28. Domain and full-audit findings

24. **OR:** OR-S02 passed the frozen safeguard check. It separated the
    pre-deadline incumbent, decision-time quality knowledge, later certificate,
    benchmark scope, and unsupported operational outcomes. No runtime-to-profit
    or post-deadline same-cycle value conversion was detected.
25. **IS:** IS-S02 used a five-row compact mapping and passed mapping fit, but
    v0.2 was preferred because its review-information sequence was clearer.
26. **Full audit:** XD-F02 tied but repeated limitations. XD-F01 lost because
    the candidate invented a scarcity/capacity trade-off and referred to
    specified targets and constraints that were not supplied. No full audit was
    simpler than the Skill 2.1 reference.
27. **Material fidelity:** one new material defect was judged, in XD-F01. This
    is noncompensatory.
28. **Product-owner package:**
    `evals/skill-2.2-canary/user-acceptance/`. The eight pairs and review form
    are blinded; condition keys remain only in ignored local storage.

## 29–34. Boundaries, decision, and remaining work

29. The automated holdout and expert holdout remain unopened.
30. No human experts participated.
31. Supported development claims: 16/16 authorized calls completed; 8/8
    adaptive contracts passed; 5/8 outputs avoided repetition; four of six
    non-full tasks won; OR safeguards and IS mapping fit passed; no judged
    candidate unsupported fact, scope error, runtime-to-profit conversion, or
    post-deadline same-cycle value claim occurred.
32. Unsupported claims: Skill superiority, evaluator validity, expert
    validation, external validity, release readiness, and production
    performance.
33. **Decision:** failed. `development_merge_eligible=false`. The draft PR must
    remain unmerged. Failed blocking gates were new material fidelity,
    frozen unsupported-fact count, visible nonapplicable layers, full-audit
    fidelity/noninferiority, and full-audit simplification.
34. Before validation or release, the smallest next product repair is a
    full-audit render guard: never infer allocation scarcity, targets,
    constraints, or other trade-offs from the existence of an allocation
    variable; render absent semantics once as `not_supplied`; and suppress
    nonrequested layers before DFC/gate expansion. A future development round
    should also prospectively test list-index exclusion, but this result and its
    frozen detector must not be rewritten. No validation, holdout, tag, or
    release is authorized.
