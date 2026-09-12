---
name: newsletter-draft-open
description: OPEN LOOP (no verifier) — Write the newsletter text from the verified digest — one section per item — and verify it against the digest.
version: 0.1.0
author: SupportVectors AI Lab
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Newsletter, Writing, Verifier, Teaching]
    related_skills: [research-digest-open, newsletter-render-open]
---

# Newsletter draft — from digest to prose

Input: `$NEWSLETTER_LAB/runs/<today>/items.json`, produced by `research-digest-open`.
Output: `$NEWSLETTER_LAB/runs/<today>/draft.md`.

## Shape of the draft

- An opening paragraph (at least 30 words): what this week's five have in common, or don't.
- Then **one section per item, in the digest's order**, each exactly:
  ```
  ## 1. <the item's title, verbatim>
  Two short paragraphs (40+ words together): what it is, and why it matters to an engineer —
  built from the item's title, summary and `why`. No claims beyond those.
  <the item's URL, alone on the last line>
  ```
- 250–700 words in total. No sign-off, no "as an AI", no apologies.

## Procedure

1. Read `items.json`. Do not re-fetch anything and do not add items.
2. Write `draft.md` in the shape above.
3. Reply with the opening paragraph and the path of the draft.

## Rules

- Quote nothing you have not seen. A quotation in the draft must appear in the item's title or
  summary; otherwise write it as a description, not a quote.
- Every URL in the draft is one of the five. No others — not even "see also".
- Do not open the browser or fetch the articles; the draft is written from the digest.

<!-- This is the open-loop twin of the skill of the same name: identical instructions, no verifier step. Run it first. -->
