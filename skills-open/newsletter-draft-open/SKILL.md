---
name: newsletter-draft-open
description: OPEN LOOP (no verifier) — write the newsletter text from the digest, one section per item.
version: 0.2.0
author: SupportVectors AI Lab
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Newsletter, Verifier, Teaching]
    related_skills: [research-digest-open, newsletter-render-open]
---

# Newsletter draft — from digest to prose

Input: the digest saved by the research step. Output: `draft.md`, saved with `save_draft`.

## Shape of the draft

- An opening paragraph (at least 30 words): what this week's five have in common, or don't.
- Then **one section per item, in the digest's order**, each exactly:
  ```
  ## 1. <the item's title, verbatim>
  Two short paragraphs (40+ words together): what it is, and why it matters to an engineer —
  built from the item's title, summary and `why`. No claims beyond those.
  <the item's url, alone on the last line>
  ```
- 250–700 words in total. No sign-off, no "as an AI", no apologies.

## Procedure

1. Write the draft in the shape above, from the digest you saved (do not re-fetch, do not add items).
2. Call `save_draft` with the whole Markdown.
3. Reply with the opening paragraph and where the draft was saved.

## Rules

- Quote nothing you have not seen: a quotation must appear in the item's title or summary,
  otherwise describe, don't quote.
- Every url in the draft is one of the five. No others — not even "see also".
