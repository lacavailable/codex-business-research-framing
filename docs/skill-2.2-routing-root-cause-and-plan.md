# Skill 2.2 routing root-cause audit and frozen plan

## Scope and preserved history

This round starts from PR #7 commit
`323ea17b8f98059b71801b6a1bf9241188be4fee`. PRs #5, #6, and #7 and their
sealed artifacts remain unchanged. The automated and expert holdouts remain
unopened. This is development work only: it cannot establish evaluator
validity, expert validation, Skill superiority, or release readiness.

## Read-only root-cause findings

1. The Skill 2.1 compact gate was internally impossible. Profile compliance
   required 120–220 words, while the preregistered 30% reduction from the
   observed 75-word baseline median required a candidate median of at most
   52.5 words.
2. Response profiles stated target ranges but did not require a final
   rendering pass that sets a task-specific ceiling, checks it, and repairs a
   miss. Short prompts therefore often produced useful prose outside the
   nominal band.
3. The non-repetition rule did not assign each issue a single visible home.
   The model could restate the same boundary in framing, diagnosis, evidence,
   and boundary prose while believing each section served a different role.
4. The frozen repetition detector counted repeated topic terms rather than
   repeated limitation statements. For example, ordinary mentions of
   `runtime`, `deadline`, and `certificate` inflated the metric even when they
   were needed to explain the result.
5. The frozen unsupported-number detector treated every numeral absent from a
   task allowlist as an unsupported fact. It could not distinguish empirical
   quantities from structural labels such as BusinessBrief `2.0`, DFC-12,
   stage numbers, schema versions, or numbered audit sections.
6. Output routing was distributed across `SKILL.md`,
   `response-profiles.md`, and `output-contracts.md` without one concise
   precedence rule. The intended behavior was present, but its execution
   priority was weak.

These findings explain the failed canary without revising its frozen result.

## Decision-complete intervention

Make the smallest product change that addresses execution:

- Replace profile minimums with ceiling-first defaults. Explicit user length
  or format controls; a profile must never pad an answer to reach a minimum.
- Add a final render gate: set the ceiling, allocate content slots, render,
  check, and compress once before returning.
- Assign each material issue one visible home. A compact answer gets one prose
  block and at most one combined caveat; a standard answer may add one compact
  diagnosis/boundary block; full audit repeats only where schema compatibility
  requires it.
- Keep DFC-12, all six fidelity gates, BusinessBrief 1.0/2.0 validation,
  `agents/openai.yaml`, and the domain playbooks' substantive safeguards
  unchanged.
- Replace the development metric, not the historical detector. The new
  detector counts task-supplied empirical quantities as allowed, ignores
  explicit structural-number contexts, and flags candidate-added empirical
  quantities or frozen unsupported-fact phrases.
- Measure repeated limitations by distinct visible units that express the
  same limitation, not by raw topic-word frequency.

## HTR task tuple and call budget

- **M0:** PR #7 head `323ea17b8f98059b71801b6a1bf9241188be4fee`.
- **Objective:** improve output routing, length compliance, and non-repetition
  while preserving material fidelity and empirical-claim discipline.
- **E_dev:** deterministic fixture tests and repository tests; no model calls.
- **E_test:** one frozen four-task public development canary. It is not either
  official holdout and is used once as the HTR merge gate.
- **Development executor budget:** at most two isolated executor calls, one for
  routing/rendering and one for deterministic metric repair.
- **Authoritative canary budget:** exactly eight generation calls and four
  blinded pairwise-judge calls; maximum 12. No retry, replacement,
  adjudication, or sampling search.

## Frozen blocking gates

The new canary passes only if all of the following hold:

1. 12/12 authorized calls complete with no extra calls.
2. Candidate profile compliance is 4/4 under task-specific ceilings and format
   constraints.
3. Candidate usable-answer-first compliance is 4/4.
4. Candidate duplicate-limitation units equal zero.
5. Candidate unsupported empirical facts equal zero.
6. Candidate prohibited runtime-to-profit, equivalent-formulation-to-optimum,
   and post-deadline-value overclaims equal zero.
7. Blinded judging finds zero new material fidelity regressions.
8. The full-audit candidate retains every frozen safeguard token and is not
   judged materially inferior on fidelity.

Pairwise usability preference and length deltas are diagnostics only. Passing
cannot support a superiority claim. Regardless of outcome,
`validation_authorized` and `release_authorized` remain false.

