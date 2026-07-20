# Top-journal calibration protocol

## Corpus and acceptance

Candidate selection may consider Management Science, MSOM, Operations Research, ISR, MISQ, AMR, AMJ, Organization Science, and SMJ, plus no more than two total HBR or MIT SMR practitioner passages. Selection balances OM, IS, OR, and management; passage function; article type; outlet; and writing style. Outlet identity never establishes quality.

Up to 36 candidates may be screened to accept exactly 24 passages: six per domain, comprising three expert-confirmed positives and three intermediate controls. Every passage requires lawful access, a recorded source hash, anonymization review, and two independent qualified reviewers. Publication status is hidden during annotation. Exclusions and replacement reasons are retained privately.

The ignored `research-private/evaluator-calibration/` hierarchy holds copyrighted passages, reviewer qualification records, identities, private rationales, and judge packets. Public artifacts contain only metadata, hashes, sanitized annotations without passage text or evidence spans, licensed passages, and original synthetic analogues.

## Splits and freeze

Originals, paraphrases, and derivatives remain source-clustered. Development, validation, and holdout each receive four positive, four intermediate, eight negative, and forty variants. Holdout must remain unopened until development and validation pass with real expert data and the evaluator code, prompts, rubric, split manifest, and hashes are frozen in Git.

