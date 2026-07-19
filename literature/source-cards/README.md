# Source cards

Each source has one Markdown card with YAML frontmatter conforming to
`../schemas/source-card.schema.json`. The body must be an original paraphrase,
identify the exact material actually reviewed, distinguish metadata from
content access, and state counterconditions or limits. Cards do not reproduce
article text.

A card becomes `verified` only after separate fresh-context extraction and
audit passes both record `pass` and all corresponding manifest fields agree.
