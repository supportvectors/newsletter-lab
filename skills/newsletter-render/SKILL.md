---
name: newsletter-render
description: Turn the verified draft into the HTML newsletter using the lab's template, and verify the page against the template and the digest.
version: 0.2.0
author: SupportVectors AI Lab
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Newsletter, Verifier, Teaching]
    related_skills: [research-digest, newsletter-draft]
---

# Newsletter render — the draft, in the house template

Input: the saved digest and draft. Output: `newsletter.html`, saved with `save_page`.

The template is `template/newsletter.html` in the lab: `{PLACEHOLDERS}` and one `<article>`
block between `<!-- ITEM START -->` and `<!-- ITEM END -->` comments. Read it with the file tool
if you need to; it is short.

## Procedure

1. Produce the page: the template **verbatim** — including its `<style>` block, unchanged — with
   every placeholder filled, the article block repeated once per item in the digest's order, and
   the two marker comments removed. `{ITEM_BODY}` is that item's section text from the draft
   (without the url line); `{ITEM_URL}` is the item's url; `{DATE}` is today. Escape `&`, `<`,
   `>` in text.
2. Call `save_page` with the complete HTML. The harness opens it for the user.
3. Call `verify_render`. On `fail`, repair **only** what it names, `save_page` again, verify again.
   Three failures: stop and tell the user.
4. Reply with where the page was saved. If the user asks for the *mechanical* rendering, call
   `render_page` instead of filling the template by hand — same output, no model, nothing for the
   verifier to find.

## Rules

- Do not redesign. The CSS is the house style; changing a colour is a failed verification.
- Do not add items, links, scripts, or a sign-off beyond the template's footer slot.
- Do not open the file yourself; the harness does.
