# Evidence and Attribution

Label claims by what supports them, not by how plausible they sound.

## Evidence labels

| Label | Use when | Required treatment |
|---|---|---|
| `empirical_fact` | A source or supplied dataset directly supports the statement. | Cite or identify the source and preserve its scope. |
| `model_assumption` | The statement defines the modeled environment or behavior. | Call it an assumption, not an observed fact. |
| `simplifying_assumption` | The statement deliberately omits complexity for tractability or focus. | Explain what is simplified and the likely boundary it creates. |
| `inference` | The statement interprets supplied evidence or model results but is not directly established. | State the reasoning and qualify uncertainty. |
| `unsupported_claim` | No adequate support is available. | Mark it unverified, request evidence, narrow it, or remove it. |

## Claim audit

1. Extract claims about prevalence, magnitude, trend, practice, firm behavior, user behavior, performance, causality, and social effect.
2. Assign exactly one evidence label to each material claim.
3. Record the source, or `null` when unavailable.
4. Specify an action: retain with citation, verify, qualify, convert to a synthetic illustration, or remove.
5. Recheck whether the narrative silently turns an assumption or numerical result into an empirical fact.

Treat company names, market sizes, adoption rates, cost savings, and operational performance as externally checkable facts. Never invent them. Use “a synthetic platform” or equivalent when realism is illustrative.

## Attribution discipline

- Cite the original source for a substantive fact whenever available.
- Keep quotations short and necessary; prefer original synthesis.
- Do not imply that a cited source validates model assumptions it does not examine.
- Distinguish evidence that motivates the problem from evidence that identifies a causal mechanism.
- Do not cite a general industry article for a precise numerical or causal claim it cannot support.
- Preserve uncertainty, population, geography, period, and measurement definitions from the source.

## Causal and normative safeguards

Use causal language only when the design or model establishes the stated intervention-outcome relationship under declared assumptions. Use association or prediction language otherwise. Do not claim fairness, privacy, safety, social welfare, or sustainability gains merely because a private objective improves; map and evaluate the relevant outcome explicitly.

When external lookup is unavailable, return a claim checklist with the exact evidence needed. Do not manufacture bibliographic details.
