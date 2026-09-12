#!/usr/bin/env python3
"""The other way to render — code, not the model.

    python3 tools/render.py runs/<date>/draft.md runs/<date>/items.json --out runs/<date>/newsletter.html

Same template, same inputs, no model. This is the pipeline-D move from the engine lab: once a step
is mechanical, take it away from the driver. It cannot leave a placeholder, drop an item, or
"improve" the CSS — so its verifier never has anything to say. Compare the token bill.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import re
import sys
import json
from pathlib import Path


DEFAULT_TEMPLATE = str(Path(__file__).resolve().parents[1] / "template" / "newsletter.html")


def render(draft_path: str, items_path: str, out: str, template_path: str | None = None,
           title: str = "Five Things Worth Reading", kicker: str = "SupportVectors · AI Digest",
           footer: str = "Assembled by an agent, checked by code. SupportVectors AI Lab.") -> str:
    """Fill the template from the draft and the digest; write ``out``; return the page."""
    text = Path(draft_path).read_text(encoding="utf-8")
    items = json.loads(Path(items_path).read_text(encoding="utf-8"))
    items = items.get("items") if isinstance(items, dict) else items
    tpl = Path(template_path or DEFAULT_TEMPLATE).read_text(encoding="utf-8")

    parts = re.split(r"^## +", text, flags=re.M)
    intro = " ".join(parts[0].split())
    sections = {}
    for s in parts[1:]:
        head, _, body = s.partition("\n")
        url = re.findall(r"https?://\S+", body)
        if url:
            sections[url[-1].rstrip(".,")] = re.sub(r"https?://\S+", "", body).strip()

    block_m = re.search(r"\s*<!-- ITEM START.*?-->(.*?)<!-- ITEM END -->", tpl, flags=re.S)
    block = block_m.group(1)
    articles = []
    for it in items:
        body = " ".join(sections.get(it["url"].strip(), it.get("why", "")).split())
        articles.append(block.replace("{{ITEM_SOURCE}}", html.escape(it.get("source", "")))
                             .replace("{{ITEM_TITLE}}", html.escape(it.get("title", "")))
                             .replace("{{ITEM_BODY}}", html.escape(body))
                             .replace("{{ITEM_URL}}", html.escape(it["url"].strip(), quote=True)))
    page = tpl[:block_m.start()] + "\n" + "".join(articles) + tpl[block_m.end():]
    page = (page.replace("{{TITLE}}", html.escape(title)).replace("{{KICKER}}", html.escape(kicker))
                .replace("{{DATE}}", dt.date.today().strftime("%B %d, %Y")).replace("{{INTRO}}", html.escape(intro))
                .replace("{{FOOTER}}", html.escape(footer)))
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(page, encoding="utf-8")
    return page


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("draft")
    ap.add_argument("items")
    ap.add_argument("--out", required=True)
    ap.add_argument("--template", default=DEFAULT_TEMPLATE)
    ap.add_argument("--title", default="Five Things Worth Reading")
    ap.add_argument("--kicker", default="SupportVectors · AI Digest")
    ap.add_argument("--footer", default="Assembled by an agent, checked by code. SupportVectors AI Lab.")
    args = ap.parse_args()
    render(args.draft, args.items, args.out, args.template, args.title, args.kicker, args.footer)
    print(args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
