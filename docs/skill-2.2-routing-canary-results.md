# Skill 2.2 routing canary results

## Outcome

The Skill 2.2 routing experiment failed its frozen development gate.
`experimental_merge_authorized` is `false`. The branch must remain unmerged.
This result does not authorize validation, either holdout, a tag, a release,
or any claim of Skill superiority or expert validation.

The failure is noncompensatory: the blinded full-audit judge found one new
material fidelity issue in the candidate and none in the Skill 2.1 baseline.
The candidate repair referred to the model's "stated feasible set and
information structure" after the same answer had marked both as unsupplied.
That wording silently upgraded unknown semantics to supplied semantics.

## Frozen design and call accounting

- Baseline: PR #7 head
  `323ea17b8f98059b71801b6a1bf9241188be4fee`.
- Candidate freeze commit:
  `3bda103dab5d81d3eb889935a51eeb121dc276b7`.
- Four new public development tasks: one each for OM, IS, OR, and
  cross-domain full audit.
- Eight `gpt-5.6-terra`/high generation calls: baseline and candidate for each
  task.
- Four `gpt-5.6-sol`/high blind pairwise judgments.
- 12/12 calls completed; zero retries, replacements, or adjudications.
- Sampling controls were unavailable; the two models are same-family
  variants, so independence is not established.

Tasks, hidden audit fields, thresholds, the manifest, the evaluator, and both
Skill trees were hashed before the authoritative calls. The automated and
expert holdouts were not opened.

## Blocking gates

| Gate | Observed | Result |
|---|---:|---|
| Authorized calls completed | 12/12 | pass |
| Candidate profile compliance | 4/4 | pass |
| Candidate usable answer first | 4/4 | pass |
| Compact/standard duplicate-limitation units | 0 | pass |
| Unsupported empirical facts | 0 | pass |
| Prohibited computational overclaims | 0 | pass |
| New material fidelity regressions | 1 | **fail** |
| Full-audit safeguards noninferior | false | **fail** |

The six passing gates do not compensate for either failed fidelity gate.

## Diagnostic findings

The candidate met every task-specific length and format constraint. Candidate
word-count deltas relative to Skill 2.1 were -4 for OM compact, +34 for IS
compact, -20 for OR standard, and -153 for the full audit. These deltas are
descriptive, not evidence of general concision.

Blind overall preference was split: Skill 2.2 won the OM and IS pairs; Skill
2.1 won the OR and full-audit pairs. The 2–2 split is diagnostic only and
cannot support a preference or superiority claim.

The new deterministic empirical-fact check produced zero flags while allowing
the task-supplied `42%` and `15 minutes` and ignoring structural labels such as
BusinessBrief `2.0`, DFC-12, and stage numbers. This demonstrates the intended
distinction on four development tasks; it does not validate the detector.

The revised duplicate-limitation metric counted distinct visible units that
expressed the same limitation. It did not treat necessary mentions of
runtime, deadlines, certificates, or structural labels as repetition.
Full-audit structured repetition was excluded from this gate where schema
compatibility permits it.

## Root-cause interpretation

The ceiling-first routing and single-home rules transferred to the bounded
development tasks, but the full-audit output exposed a different failure
mode: compression and polished repair language can convert an unknown model
element into an apparently supplied one. A future intervention would need an
explicit lexical safeguard such as "never describe an unknown, not supplied,
or not assessed element as stated, given, fixed, or specified." That repair
was not added after the freeze, and no replacement canary was run.

## Preservation and boundaries

PRs #5, #6, and #7 and their failed results remain unchanged. The Skill 2.1
canary directory, old canary tool, and result document retain their original
Git objects; its historical tests now read the frozen Skill from PR #7's
commit rather than the mutable current Skill. No human experts participated.
No validation or holdout was accessed. No tag or release was created.

The durable HTR audit is stored in `.arbor/`. Its current best remains the
initial material because the one-shot development test rejected the combined
candidate.

