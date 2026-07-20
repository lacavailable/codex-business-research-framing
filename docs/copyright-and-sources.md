# Copyright and source methodology

## Public-repository rule

Commit only material that contributors have the right to redistribute. v0.2 contains no journal or magazine article text, PDFs, HTML snapshots, screenshots, or book content. Paywalled text, private research notes, proprietary datasets, archives, and long excerpts remain prohibited even when lawfully accessed for private study.

The normal public artifacts are bibliographic metadata, official links, short quotations only when genuinely necessary, original source cards, structural observations, and independently written syntheses. A citation does not make wholesale copying permissible. A future complete source file is accepted only when an explicit CC BY, CC0, public-domain, or equivalently permissive redistribution license is independently verified and the manifest, checksum, license record, attribution, notice, and redistribution status agree.

## Private analysis

Place lawfully accessed nonredistributable source material and substantial local annotations under `research-private/literature/`, which is ignored by Git. Do not use private text as benchmark output or documentation. Translate insights into original, source-independent principles, then verify that the public artifact neither reconstructs the source nor retains identifying private details.

## Synthetic examples

Repository examples and benchmark scenarios should use invented organizations and clearly mark synthetic facts. Avoid combinations of names, dates, figures, and events that could be mistaken for an actual organization. A synthetic label does not excuse copying a real case.

## Automated checks and human review

`tools/audit_repository.py --all` skips the ignored private corpus, while `--tracked` rejects any private-corpus path that entered Git. It rejects risky binary/document/archive formats, credential-like filenames, and oversized text unless a staged literature file satisfies the complete explicit-license record. Automation is a backstop, not a copyright determination. Release review must also inspect the full diff, repository history, generated archive, attribution, notices, and source provenance.

## Independence

The Decision-Fidelity Canvas and repository prose are original. General principles such as identifying an actor, decision, constraint, or trade-off are expressed independently and adapted to OM, IS, and OR research. The project does not emulate a named publication and claims no affiliation with Harvard Business Review, Harvard Business Publishing, INFORMS, AIS, or any journal.
