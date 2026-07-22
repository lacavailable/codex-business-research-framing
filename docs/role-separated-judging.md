# Role-separated judging

_Isolation, evidence, and reconciliation rules for automated triangulation_

---

## Design principle

No single automated judgment is treated as authoritative evidence of quality. Each role answers a bounded question from the minimum packet needed for that question. Independent records are sealed before meta-adjudication so later reconciliation cannot masquerade as initial agreement.

## Role contracts

| Role | Primary responsibility | Must not decide alone |
| --- | --- | --- |
| Model-structure extractor | Actor, choice, timing, information, objective, constraints, mechanism, uncertainty | Overall writing quality or silver confidence |
| Passage-function classifier | Requested and attempted passage functions; initial layer applicability | Fidelity score or source quality |
| Fidelity auditor | Atomic consistency checks, materiality, and evidence spans | Managerial or scholarly style preferences |
| Managerial-framing auditor | Decision relevance, mechanism, trade-off, conditions, implications | Mathematical fidelity outside an identified inconsistency |
| Scholarly-positioning auditor | Problem construction, contribution logic, counterconditions, boundaries | Outlet prestige or publication likelihood |
| Evidence auditor | Claim support, evidence type, traceability, and unsupported inference | Prose quality |
| Prose/usability auditor | Clarity, information density, repetition, and profile fit | Domain truth not supported by the packet |
| Adversarial critic | Strongest plausible alternative interpretation and hidden inconsistency | Final label |
| Meta-adjudicator | Reconcile sealed role records and assign final silver status | Create evidence or erase unresolved disagreement |

## Isolation and blinding

Generator-visible content remains separate from judge-only records. Role packets omit labels, perturbation identity, expected direction, outlet prestige, and other anchors unless a diagnostic explicitly requires them. Prestige diagnostics are separate from production evaluation.

Runs use fresh contexts, randomized opaque identifiers, varied prompt wording and ordering, and recorded model/settings metadata. These measures improve procedural separation; they do not make same-family model variants independent experts.

## Evidence and applicability

Every material fidelity finding must name an atomic check, explain why the issue changes the represented decision or claim, and cite a supporting private or synthetic evidence span. `Uncertain` is a distinct result.

Applicability challenges must use `challenge_with_evidence`. The record identifies the original status, proposed status, passage function or attempted layer that motivates the challenge, and its evidence span. Unsupported challenges are discarded but preserved in the audit trail.

## Reconciliation

Meta-adjudication begins only after all required primary role records exist. It receives the sealed conclusions, evidence references, confidence statements, and rationales. It must:

1. Reconcile passage-function and applicability disagreements first
2. Resolve atomic fidelity findings without broadening their scope
3. Check category localization and stable-category tolerances
4. Record accepted and rejected alternative interpretations
5. Assign `silver_high_confidence`, `silver_provisional`, or `unresolved`

The adjudicator may not infer agreement from repeated phrasing, treat missing evidence as a pass, or elevate a result because of outlet identity. If the evidence cannot resolve a material disagreement, the result remains provisional or unresolved.

## Reporting

Public reporting includes role completion, applicability agreement, atomic-check agreement, positive and negative hard-failure agreement, category reliability, inter-run stability, adjudication rate, confidence counts, localization, and aggregate evidence quality. Private rationales and evidence spans are never published.
