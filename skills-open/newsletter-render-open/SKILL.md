---
name: newsletter-render-open
description: OPEN LOOP (no verifier) — Turn the verified draft into the HTML newsletter using the lab's template, and verify the page against the template and the digest.
version: 0.1.0
author: SupportVectors AI Lab
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Newsletter, HTML, Template, Verifier, Teaching]
    related_skills: [research-digest-open, newsletter-draft-open]
---

# Newsletter render — the draft, in the house template

Input: `$NEWSLETTER_LAB/runs/<today>/draft.md` and `items.json`, as produced.
Template: `$NEWSLETTER_LAB/template/newsletter.html`.
Output: `$NEWSLETTER_LAB/runs/<today>/newsletter.html`.

## Procedure

1. Read the template. It has `{{PLACEHOLDERS}}` and one `<article>` block between
   `<!-- ITEM START -->` and `<!-- ITEM END -->` comments.
2. Write `newsletter.html`: the template **verbatim** — including its `<style>` block, unchanged —
   with every placeholder filled, the article block repeated once per item in the digest's
   order, and the two marker comments removed. `{{ITEM_BODY}}` is that item's section text from
   the draft (without the URL line); `{{ITEM_URL}}` is the item's URL; `{{DATE}}` is today.
   Escape `&`, `<`, `>` in text.
3. Reply with the path. Do not open the file; the user will.

## Rules

- Do not redesign. The CSS is the house style; changing a colour is a failed verification.
- Do not add items, links, scripts, or a sign-off that is not in the template's footer slot.
- If you find yourself writing a loop in your head — "for each item, copy the block" — notice
  that this step is mechanical. `tools/render.py` does it without a model. Ask the user whether
  they would rather run that; it is the same output for a fraction of the tokens.

<!-- This is the open-loop twin of the skill of the same name: identical instructions, no verifier step. Run it first. -->
