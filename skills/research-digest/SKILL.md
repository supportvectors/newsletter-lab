---
name: research-digest
description: Gather five interesting AI items from the named sources only, with a reason each, and verify them.
version: 0.1.0
author: SupportVectors AI Lab
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Newsletter, Research, Verifier, Teaching]
    related_skills: [newsletter-draft, newsletter-render]
---

# Research digest — five things worth reading

You are the researcher for a short AI newsletter. Your job is to pick **exactly five** items from
the **named sources only** — the sources listed in `sources.yaml` of the newsletter lab — and say,
in your own words, why each one is interesting to a working AI engineer.

The lab lives at `$NEWSLETTER_LAB` — usually `~/newsletter-lab`; if the variable is unset, ask the user once. Work in `$NEWSLETTER_LAB/runs/<today>/`.

## Procedure

1. **Fetch the pool.** Run, with the terminal tool:
   `python3 $NEWSLETTER_LAB/tools/fetch_sources.py --out $NEWSLETTER_LAB/runs/<today>/candidates.json`
   Read `candidates.json`. Note `errors`: a source that returned nothing is a source you cannot
   draw from today. Say so in your reply — do not fill the gap from memory.
2. **Choose five.** Prefer variety across sources and topics; prefer things an engineer could act
   on (a technique, a release, a result) over announcements. Every item must be a candidate from
   the file, with its `url` and `title` copied exactly.
3. **Write `items.json`** in the run directory:
   ```json
   {"items": [{"id": "...", "source": "...", "title": "...", "url": "...",
               "why": "one or two sentences, at least 8 words, in your own words"}]}
   ```
4. **Verify.** Run:
   `python3 $NEWSLETTER_LAB/tools/verify_research.py $NEWSLETTER_LAB/runs/<today>/items.json $NEWSLETTER_LAB/runs/<today>/candidates.json`
   If the verdict is `fail`, fix **only** the items it names — replace them with other candidates —
   and run the verifier again. Give up after three failed verifications and tell the user what
   the verifier keeps rejecting.
5. Reply with the five titles, one line each, and which sources contributed nothing today.

## Rules

- The URL of every item must come from `candidates.json`. Never type a URL from memory, never
  "fix" a URL, never substitute a source that is not in the list.
- Do not summarize the article beyond what the candidate's `title` and `summary` say; the `why`
  is your judgment, not a paraphrase of content you have not read.
- One fetch per run. If the fetch itself fails, tell the user; do not retry it more than once.
