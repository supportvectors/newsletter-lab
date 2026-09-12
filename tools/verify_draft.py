#!/usr/bin/env python3
"""Verifier 2 — the newsletter draft.

    python3 tools/verify_draft.py runs/<date>/draft.md runs/<date>/items.json

The draft is Markdown with one section per item, each headed `## <n>. <title>` and ending with the
item's URL on its own line. The verifier holds the item list — which the model also has — but it
holds it as data, not as memory: it counts, it matches, it does not trust.

Checks: every item has a section and only those items do; each section's URL is that item's URL;
no URL appears that is not an item's; no invented direct quotes (a quoted span of 8+ words must
appear in the item's title or summary); length within bounds; no apology/refusal boilerplate;
a one-paragraph opener exists. Exit 0 on pass, 1 on fail.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

MIN_WORDS, MAX_WORDS = 250, 700
URL_RE = re.compile(r"https?://[^\s)>\]]+")
QUOTE_RE = re.compile(r"[\"“]([^\"”]{40,})[\"”]")
BOILERPLATE = ("as an ai", "i cannot", "i can't", "i'm unable", "i am unable", "unfortunately i", "i don't have access")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("draft")
    ap.add_argument("items")
    args = ap.parse_args()
    problems: list[dict] = []
    try:
        text = Path(args.draft).read_text(encoding="utf-8")
        chosen = json.loads(Path(args.items).read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"verdict": "fail", "problems": [{"where": None, "reason": f"cannot read inputs: {e}"}]}))
        return 1
    items = chosen.get("items") if isinstance(chosen, dict) else chosen
    by_url = {it["url"].strip(): it for it in items}

    words = len(text.split())
    if not MIN_WORDS <= words <= MAX_WORDS:
        problems.append({"where": "whole draft", "reason": f"{words} words; expected {MIN_WORDS}-{MAX_WORDS}"})
    low = text.lower()
    for b in BOILERPLATE:
        if b in low:
            problems.append({"where": "whole draft", "reason": f"contains boilerplate '{b}' — this is a newsletter, not a chat reply"})

    # sections
    parts = re.split(r"^## +", text, flags=re.M)
    opener = parts[0].strip()
    if len(opener.split()) < 30:
        problems.append({"where": "opener", "reason": "an opening paragraph of at least 30 words must precede the first item"})
    sections = parts[1:]
    if len(sections) != len(items):
        problems.append({"where": "sections", "reason": f"{len(sections)} item sections; expected {len(items)}"})
    seen_urls = set()
    for s in sections:
        head, _, body = s.partition("\n")
        urls = URL_RE.findall(body)
        m = re.match(r"(\d+)\.\s+(.*)", head.strip())
        label = head.strip()[:50]
        if not m:
            problems.append({"where": label, "reason": "section heading must be '## <n>. <title>'"})
        if not urls:
            problems.append({"where": label, "reason": "section has no URL; end it with the item's URL on its own line"})
            continue
        sec_url = urls[-1].rstrip(".,")
        if sec_url not in by_url:
            problems.append({"where": label, "reason": f"URL is not one of the digest items: {sec_url[:80]}"})
            continue
        if sec_url in seen_urls:
            problems.append({"where": label, "reason": "item used twice"})
        seen_urls.add(sec_url)
        it = by_url[sec_url]
        if m and it.get("title") and m.group(2).strip().lower()[:30] != it["title"].strip().lower()[:30]:
            problems.append({"where": label, "reason": f"heading title differs from the item's title ('{it['title'][:60]}')"})
        for extra in urls[:-1]:
            if extra.rstrip(".,") not in by_url:
                problems.append({"where": label, "reason": f"extra URL not in the digest: {extra[:80]}"})
        haystack = ((it.get("title") or "") + " " + (it.get("summary") or "") + " " + (it.get("why") or "")).lower()
        for q in QUOTE_RE.findall(body):
            if q.lower()[:40] not in haystack:
                problems.append({"where": label, "reason": f"direct quote not found in the source material: \"{q[:50]}…\""})
        if len(body.split()) < 40:
            problems.append({"where": label, "reason": "section is under 40 words"})
    missing = set(by_url) - seen_urls
    for u in missing:
        problems.append({"where": by_url[u].get("title", u)[:50], "reason": "digest item has no section in the draft"})

    verdict = {"verdict": "pass" if not problems else "fail", "words": words, "sections": len(sections), "problems": problems}
    if problems:
        verdict["instruction"] = "Fix ONLY the sections named above, keep everything else, and run this verifier again."
    print(json.dumps(verdict, indent=2))
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
