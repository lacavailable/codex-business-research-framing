# Copyright and source methodology

## Public-repository rule

Commit only material that contributors have the right to redistribute. Full journal or magazine articles, paywalled text, source PDFs, office documents, private research notes, proprietary datasets, archives, and long excerpts are prohibited even when they were lawfully accessed for private study.

Permitted public artifacts are limited to bibliographic metadata, links to lawful sources, short quotations when genuinely necessary, original annotations, abstract structural observations, and independently written syntheses. A citation does not make wholesale copying permissible.

## Private analysis

Place temporary source analysis under `research-private/`, which is ignored by Git. Do not use private text as benchmark output or documentation. Translate insights into original, source-independent principles, then verify that the public artifact neither reconstructs the source nor retains identifying private details.

## Synthetic examples

Repository examples and benchmark scenarios should use invented organizations and clearly mark synthetic facts. Avoid combinations of names, dates, figures, and events that could be mistaken for an actual organization. A synthetic label does not excuse copying a real case.

## Automated checks and human review

`tools/audit_repository.py` rejects tracked private-corpus paths, risky binary/document/archive formats, credential-like filenames, and oversized text files unless narrowly allowlisted in the script. Automation is a backstop, not a copyright determination. Release review must also inspect the full diff, repository history, generated archive, attribution, and source provenance.

## Independence

The Decision-Fidelity Canvas and repository prose are original. General principles such as identifying an actor, decision, constraint, or trade-off are expressed independently and adapted to OM, IS, and OR research. The project does not emulate a named publication and claims no affiliation with Harvard Business Review, Harvard Business Publishing, INFORMS, AIS, or any journal.
