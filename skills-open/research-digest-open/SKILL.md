---
name: research-digest-open
description: OPEN LOOP (no verifier) — gather five interesting AI items from the named sources only, with a reason each.
version: 0.2.0
author: SupportVectors AI Lab
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Newsletter, Verifier, Teaching]
    related_skills: [newsletter-draft-open, newsletter-render-open]
---

# Research digest — five things worth reading

You are the researcher for a short AI newsletter. Pick **exactly five** items from the **named
sources only** and say, in your own words, why each is interesting to a working AI engineer.

## Procedure

1. Call `fetch_sources`. It returns the pool — `candidates` — and `sources_with_nothing`. A source
   that returned nothing is a source you cannot draw from today; say so in your reply. **Do not fill
   the gap from memory.**
2. Choose five from `candidates`. Prefer variety across sources and topics; prefer things an
   engineer could act on (a technique, a release, a result) over announcements.
3. Call `save_digest` with the five, copying each candidate's `source`, `title` and `url`
   **exactly**, and a `why` of at least 8 words in your own words.
4. Reply with the five titles, one per line, and which sources contributed nothing today.

## Rules

- Every url must come from `candidates`. Never type a url from memory, never "fix" one, never add
  a source that is not in the pool.
- The `why` is your judgment, not a paraphrase of content you have not read.
- Do not use the terminal or the browser for this task; the tools are enough.
