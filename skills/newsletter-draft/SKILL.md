---
name: newsletter-draft
description: Write the newsletter text from the verified digest — one section per item — and verify it against the digest.
version: 0.1.0
author: SupportVectors AI Lab
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Newsletter, Writing, Verifier, Teaching]
    related_skills: [research-digest, newsletter-render]
---

# Newsletter draft — from digest to prose

Input: `$NEWSLETTER_LAB/runs/<today>/items.json`, already verified by `research-digest`.
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
3. **Verify.** Run:
   `python3 $NEWSLETTER_LAB/tools/verify_draft.py $NEWSLETTER_LAB/runs/<today>/draft.md $NEWSLETTER_LAB/runs/<today>/items.json`
   On `fail`, repair **only** the sections it names and verify again. Three failures: stop and
   tell the user what keeps failing.
4. Reply with the opening paragraph and the path of the draft.

## Rules

- Quote nothing you have not seen. A quotation in the draft must appear in the item's title or
  summary; otherwise write it as a description, not a quote.
- Every URL in the draft is one of the five. No others — not even "see also".
- Do not open the browser or fetch the articles; the draft is written from the digest.
