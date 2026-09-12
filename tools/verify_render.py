#!/usr/bin/env python3
"""Verifier 3 — the rendered page.

    python3 tools/verify_render.py runs/<date>/newsletter.html runs/<date>/items.json [--template template/newsletter.html]

The verifier holds the template — the spec the page was supposed to follow — and the item list.
Checks: no `{{PLACEHOLDER}}` survives; the ITEM START/END marker comments were removed; exactly
one <article> per item, in the digest's order, each with its own URL as the href; the template's
CSS block is intact (the model must not "improve" the design); <title> and date filled; no
<script>; the HTML parses. Exit 0 on pass, 1 on fail.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

PLACEHOLDER = re.compile(r"\{\{[A-Z_]+\}\}")


class _Audit(HTMLParser):
    def __init__(self):
        super().__init__()
        self.articles: list[dict] = []
        self.scripts = 0
        self.title = ""
        self._in_title = False
        self._cur: dict | None = None
        self.errors: list[str] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "article":
            self._cur = {"hrefs": []}
            self.articles.append(self._cur)
        elif tag == "a" and self._cur is not None and a.get("href"):
            self._cur["hrefs"].append(a["href"].strip())
        elif tag == "script":
            self.scripts += 1
        elif tag == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        if tag == "article":
            self._cur = None
        elif tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("page")
    ap.add_argument("items")
    ap.add_argument("--template", default=str(Path(__file__).resolve().parents[1] / "template" / "newsletter.html"))
    args = ap.parse_args()
    problems: list[dict] = []
    try:
        page = Path(args.page).read_text(encoding="utf-8")
        chosen = json.loads(Path(args.items).read_text(encoding="utf-8"))
        template = Path(args.template).read_text(encoding="utf-8")
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"verdict": "fail", "problems": [{"where": None, "reason": f"cannot read inputs: {e}"}]}))
        return 1
    items = chosen.get("items") if isinstance(chosen, dict) else chosen

    for ph in sorted(set(PLACEHOLDER.findall(page))):
        problems.append({"where": ph, "reason": "placeholder left unfilled"})
    if "ITEM START" in page or "ITEM END" in page:
        problems.append({"where": "markers", "reason": "the ITEM START/END marker comments must be removed"})

    t_css = re.search(r"<style>.*?</style>", template, flags=re.S)
    p_css = re.search(r"<style>.*?</style>", page, flags=re.S)
    if not p_css or not t_css or re.sub(r"\s+", "", p_css.group(0)) != re.sub(r"\s+", "", t_css.group(0)):
        problems.append({"where": "<style>", "reason": "the template's CSS was changed or removed — copy it verbatim"})

    au = _Audit()
    try:
        au.feed(page)
    except Exception as e:  # noqa: BLE001
        problems.append({"where": "html", "reason": f"does not parse: {e}"})
    if au.scripts:
        problems.append({"where": "<script>", "reason": "no scripts allowed in the newsletter"})
    if not au.title.strip() or PLACEHOLDER.search(au.title):
        problems.append({"where": "<title>", "reason": "empty title"})
    if len(au.articles) != len(items):
        problems.append({"where": "<article>", "reason": f"{len(au.articles)} articles; expected {len(items)}"})
    for i, (art, it) in enumerate(zip(au.articles, items), 1):
        want = it["url"].strip()
        if want not in art["hrefs"]:
            problems.append({"where": f"article {i}", "reason": f"missing or wrong link; expected {want[:80]}"})
        for h in art["hrefs"]:
            if h != want and not h.startswith("#"):
                problems.append({"where": f"article {i}", "reason": f"unexpected link {h[:80]}"})
    for it in items[len(au.articles):]:
        problems.append({"where": it.get("title", "?")[:50], "reason": "digest item has no article on the page"})
    if not re.search(r'class="date">\s*\S', page):
        problems.append({"where": ".date", "reason": "date is empty"})

    verdict = {"verdict": "pass" if not problems else "fail", "articles": len(au.articles), "problems": problems}
    if problems:
        verdict["instruction"] = "Fix ONLY what is named above — do not regenerate the whole page — and run this verifier again."
    print(json.dumps(verdict, indent=2))
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
