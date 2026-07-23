# Skill 2.1 bounded canary

This directory contains an original eight-task product-development comparison
between tagged v0.2 and Skill 2.1 experimental. It is not evaluator calibration,
expert review, validation, or a performance benchmark.

`tasks/generator-visible.json` is the only task material supplied to generation
calls. `tasks/audit-only.json` contains deterministic checks and is never
included in a generator prompt. The call manifest permits exactly sixteen
generation calls and eight blinded pairwise judgments.

All source material is synthetic. No private literature passage, holdout case,
or answer-key annotation is included in a generation prompt.
