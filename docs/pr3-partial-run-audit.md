# PR #3 partial-run audit

## Status

The PR #3 development run is `incomplete_due_to_execution_capacity`. It is neither a calibration pass nor a calibration failure. Its records are retained as diagnostic provenance and are not authoritative inputs to the lean evaluator.

## Preserved inventory

- Baseline merge: `f92881412d7fed87e96f3108ad409418653fccf8`.
- Eight private development context packets: two each for OM, IS, OR, and management.
- Fifteen private role records: eight model-structure records and seven additional OM-P01 records.
- One private OM-P01 contrast set with fourteen constructed variants.
- Twenty-four sanitized private-anchor records and the recorded expert-holdout baseline.
- Expert and automated holdouts remain unopened.

## Diagnostic limitations

The records use the superseded eight-role design. Model identifiers and capitalization are inconsistent (`GPT-5`, `gpt-5`, `Codex`, `not_disclosed`), and several OM-P01 roles share a prompt hash. Only OM-P01 received all eight roles. No silver decision was produced. Consequently, the records cannot establish role independence, reliability, domain balance, validation performance, or any Tier A gate.

## Reuse boundary

The existing context packets and constructed contrast text may be reused as source inputs. Existing judgments, rationales, prompt hashes, and scores may be inspected only for this audit and implementation diagnostics. The lean run must create new Role A, Role B, Role C, and paired-contrast records under new schemas and prompts.

## Preservation checks

Before and after lean work, verify that no `research-private/` path is tracked, the recorded expert-holdout Git blob hashes still match, and the private preparation verifier reports `expert_holdout_unopened=true`, `automated_holdout_unopened=true`, and `automated_holdout_opened=false`.
