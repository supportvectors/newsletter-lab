#!/usr/bin/env python3
"""Fetch the named sources and write candidates.json — the ONLY pool the research skill may pick from.

    python3 tools/fetch_sources.py --out runs/2026-09-12/candidates.json

Deliberately tolerant: a source that fails is reported in ``errors`` and the run continues with
whatever the others returned, exit code 0. Nothing in the output SHOUTS about the failure. A
model reading candidates.json sees a shorter list, not a broken one — and a model that was told
"draw from Anthropic, Meta, ..." and finds no Anthropic items has a decision to make.
The verifier later checks every chosen URL against this file: candidates.json is the ledger.

Standard library only (urllib, xml, json, re), so it runs on any laptop with Python 3.9+.
"""

from __future__ import annotations

import argparse
import datetime as dt
import email.utils
import hashlib
import html
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

UA = "Mozilla/5.0 (newsletter-lab; SupportVectors teaching scaffold)"
TIMEOUT = 20


def load_sources(path: Path) -> dict:
    """A tiny YAML subset reader (no PyYAML dependency): top-level scalars and a `sources` list of
    flat mappings, with `keywords: [a, b]` inline lists."""
    cfg: dict = {"sources": []}
    cur: dict | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].rstrip() if not raw.strip().startswith("#") else ""
        if not line.strip():
            continue
        if line.startswith("  - "):
            cur = {}
            cfg["sources"].append(cur)
            line = "    " + line[4:]
        if line.startswith("    ") and cur is not None:
            k, _, v = line.strip().partition(":")
            cur[k.strip()] = _scalar(v.strip())
        elif not line.startswith(" "):
            k, _, v = line.partition(":")
            if k.strip() != "sources":
                cfg[k.strip()] = _scalar(v.strip())
    return cfg


def _scalar(v: str):
    if v.startswith("[") and v.endswith("]"):
        return [s.strip().strip("\"'") for s in v[1:-1].split(",") if s.strip()]
    if v.isdigit():
        return int(v)
    return v.strip("\"'")


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read()


def parse_date(s: str | None) -> str | None:
    if not s:
        return None
    try:
        d = email.utils.parsedate_to_datetime(s)
    except (TypeError, ValueError):
        try:
            d = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
        except ValueError:
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=dt.timezone.utc)
    return d.astimezone(dt.timezone.utc).isoformat()


def _text(el, *names) -> str | None:
    for n in names:
        found = el.find(n)
        if found is not None and (found.text or "").strip():
            return html.unescape(re.sub(r"<[^>]+>", " ", found.text)).strip()
    return None


def from_feed(src: dict) -> list[dict]:
    root = ET.fromstring(get(src["url"]))
    ns = {"a": "http://www.w3.org/2005/Atom", "dc": "http://purl.org/dc/elements/1.1/"}
    items = []
    for it in root.iter("item"):                       # RSS 2.0
        link = _text(it, "link") or (it.find("guid").text if it.find("guid") is not None else None)
        items.append({"title": _text(it, "title"), "url": link,
                      "published": parse_date(_text(it, "pubDate", "dc:date") or _text(it, "{http://purl.org/dc/elements/1.1/}date")),
                      "summary": (_text(it, "description") or "")[:400]})
    if not items:
        A = "{http://www.w3.org/2005/Atom}"
        for it in root.findall(f"{A}entry"):              # Atom
            link_el = it.find(f"{A}link")
            items.append({"title": _text(it, f"{A}title"),
                          "url": link_el.get("href") if link_el is not None else None,
                          "published": parse_date(_text(it, f"{A}published", f"{A}updated")),
                          "summary": (_text(it, f"{A}summary", f"{A}content") or "")[:400]})
    return items


def from_hn(src: dict) -> list[dict]:
    ids = json.loads(get(src["url"]))[:60]
    kws = [k.lower() for k in src.get("keywords", [])]
    items = []
    for i in ids:
        try:
            story = json.loads(get(f"https://hacker-news.firebaseio.com/v0/item/{i}.json"))
        except Exception:  # noqa: BLE001
            continue
        title = story.get("title") or ""
        if kws and not any(k in title.lower() for k in kws):
            continue
        items.append({"title": title, "url": f"https://news.ycombinator.com/item?id={i}",
                      "published": dt.datetime.fromtimestamp(story.get("time", 0), dt.timezone.utc).isoformat(),
                      "summary": f"{story.get('score', 0)} points · {story.get('descendants', 0)} comments · links to {story.get('url', '')}"[:400]})
    return items


def from_html(src: dict) -> list[dict]:
    page = get(src["url"]).decode("utf-8", "replace")
    base = src["url"]
    prefix = src.get("link_prefix", "/")
    seen, items = set(), []
    for m in re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', page, flags=re.S | re.I):
        href, inner = m.group(1), m.group(2)
        path = urllib.parse.urlparse(href).path
        if not path.startswith(prefix) or path.rstrip("/") == prefix.rstrip("/"):
            continue
        url = urllib.parse.urljoin(base, href)
        title = html.unescape(re.sub(r"<[^>]+>", " ", inner))
        title = re.sub(r"\s+", " ", title).strip()
        if url in seen or len(title) < 12:
            continue
        seen.add(url)
        items.append({"title": title[:200], "url": url, "published": None, "summary": ""})
    if not items:
        raise RuntimeError("index page fetched but no article links matched — page layout may have changed")
    return items


FETCHERS = {"rss": from_feed, "atom": from_feed, "hn": from_hn, "html": from_html}


def fetch(out: str, sources: str | None = None, window_days: int | None = None,
          only: list[str] | None = None, log=None) -> dict:
    """Fetch every source into ``out`` (candidates.json) and return the written document."""
    sources = sources or str(Path(__file__).resolve().parents[1] / "sources.yaml")
    cfg = load_sources(Path(sources))
    window = window_days or int(cfg.get("window_days", 14))
    cap = int(cfg.get("max_per_source", 12))
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=window)
    result = {"fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(), "window_days": window,
              "sources": [], "errors": [], "items": []}
    say = log or (lambda m: print(m, file=sys.stderr))
    for src in cfg["sources"]:
        if only and src["name"] not in only:
            continue
        try:
            raw = FETCHERS[src["kind"]](src)
        except Exception as e:  # noqa: BLE001 — tolerated on purpose; see module docstring
            result["errors"].append({"source": src["name"], "error": f"{type(e).__name__}: {e}"[:200]})
            result["sources"].append({"name": src["name"], "host": src["host"], "items": 0})
            say(f"  ! {src['name']}: {type(e).__name__}")
            continue
        kept = []
        for it in raw:
            if not it.get("url") or not it.get("title"):
                continue
            if it.get("published") and dt.datetime.fromisoformat(it["published"]) < cutoff:
                continue
            kept.append(it)
        kept.sort(key=lambda x: x.get("published") or "", reverse=True)
        kept = kept[:cap]
        for it in kept:
            it["id"] = hashlib.sha1(it["url"].encode()).hexdigest()[:10]
            it["source"] = src["name"]
            it["host"] = src["host"]
        result["items"].extend(kept)
        result["sources"].append({"name": src["name"], "host": src["host"], "items": len(kept)})
        say(f"  · {src['name']}: {len(kept)} candidate(s)")
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", default=None)
    ap.add_argument("--out", required=True)
    ap.add_argument("--window-days", type=int, default=None)
    ap.add_argument("--only", nargs="*", help="source names to fetch (default: all)")
    args = ap.parse_args()
    out = fetch(args.out, sources=args.sources, window_days=args.window_days, only=args.only)
    print(f"{len(out['items'])} candidates from {sum(1 for s in out['sources'] if s['items'])} of "
          f"{len(out['sources'])} sources → {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
