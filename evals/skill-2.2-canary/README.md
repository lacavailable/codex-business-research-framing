# Skill 2.2 adaptive development canary

This bounded public product-development canary compares eight new Skill 2.2
adaptive outputs with the eight already frozen v0.2 outputs from the Skill 2.1
canary. It does not regenerate v0.2 and does not modify the Skill 2.1 canary.

The authoritative budget is exactly eight `gpt-5.6-terra`/high candidate
generations plus eight `gpt-5.6-sol`/high single-judge blinded comparisons.
Retries, replacements, adjudication, and additional model roles are prohibited.

`freeze.json` binds the candidate Skill tree, reused task and baseline hashes,
generation prompts, judge prompts, manifest, metric definitions, schemas, and
fourteen acceptance rules before generation. Condition keys stay under ignored
`.local-eval/skill-2.2-canary/`.

This canary is a known-task development iteration, not independent validation.
Passing can make only this experimental draft PR development-merge-eligible.
It cannot authorize a performance claim, validation, either official holdout,
expert language, a tag, or a release.
