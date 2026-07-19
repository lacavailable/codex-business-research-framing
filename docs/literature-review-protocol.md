# Literature Review Protocol

## Purpose and scope

Build a focused, traceable, copyright-conscious evidence base for business-research framing rules. The canonical metadata live in `literature/manifest.yaml`; source cards contain independently written notes. Metadata, abstracts, and publisher summaries never establish that full text was reviewed.

The review answers:

1. How should an article formulate a concrete managerial decision?
2. How should it identify actor, trigger, decision time, information, choices, stakes, and constraints?
3. How should it explain a nontrivial trade-off?
4. How should it explain the mechanism connecting decisions to outcomes?
5. How should it establish importance without unsupported hype?
6. How should it generate a central message or counterintuitive insight?
7. How should it establish originality and scholarly contribution?
8. How should it distinguish gap spotting from problematization?
9. How should it translate analytical results into managerial implications?
10. How should it state applicability, counterconditions, limitations, and evidence needs?
11. How should OM, IS, and OR connect rigor to relevance?
12. Which current Skill rules have strong, partial, or no authoritative support?

## Selection

Prefer authority, direct relevance, complementarity, and lawful accessibility over volume. Use the fixed 20-source v0.2 core. Treat practitioner exemplars as observations of execution, not universal scientific authority. Record inaccessible and excluded candidates without implying review.

## Two-pass isolation

Run exactly two isolated passes for each included source:

1. A fresh-context extractor verifies bibliographic metadata, opens only lawfully accessible material, records access scope and exact evidence locations, and writes an original paraphrase with counterconditions.
2. A different fresh-context auditor independently checks metadata, accessible content, evidence locations, access scope, and licensing. The auditor corrects or rejects unsupported statements.

Give the auditor the card, manifest record, and lawful source locations, but not the extractor's reasoning transcript. Record both pass timestamps in card frontmatter.

## Verification decision

Set `verification_status: verified` only when both passes succeed and the manifest/card cross-check is exact. Otherwise retain `pending`, or use `excluded` with a reason. A DOI landing page, Crossref record, abstract, or publisher summary supports only the material it exposes. Record `publisher abstract`, a named official-guidance heading, an official statement section, or an exact page only when actually reviewed.

## Access and licensing

Access and redistribution are separate. Public web access is not a redistribution license. Default to `license: unknown` or `all_rights_reserved` and `redistribution_status: metadata_and_notes_only`. Commit a full source only after an explicit permissible license or public-domain status is independently verified and checksum, attribution, manifest, notice, and license records agree.

Do not use shadow libraries, access-control bypasses, shared credentials, or extracted browser cookies. Keep lawfully accessed nonredistributable sources and substantial annotations under ignored `research-private/literature/` only.

## Card method

Every card must contain the schema-validated frontmatter and the required original-paraphrase sections. Do not paste long quotations. Distinguish what the reviewed material supports from candidate rules, counterconditions, and limitations. A source can be bibliographically verified while substantive claims remain limited to its accessible abstract or official summary.
