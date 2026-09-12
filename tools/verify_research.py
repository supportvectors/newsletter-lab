#!/usr/bin/env python3
"""Verifier 1 — the research digest.

    python3 tools/verify_research.py runs/<date>/items.json runs/<date>/candidates.json [--offline]

items.json is what the model chose; candidates.json is what the fetcher actually returned. The
verifier knows three things the model does not: which URLs were really issued (the ledger), which
hosts are allowed (sources.yaml), and whether a URL resolves right now (the network).

Prints a JSON verdict and exits 0 on pass, 1 on fail. Every failure names the item and the reason,
so the model can repair the one item rather than start over.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REQUIRED = 5
MIN_WHY_WORDS = 8
UA = "Mozilla/5.0 (newsletter-lab verifier)"


def resolves(url: str) -> tuple[bool, str]:
    req = urllib.request.Request(url, headers={"User-Agent": UA}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return (200 <= r.status < 400), f"HTTP {r.status}"
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}"
    except Exception as e:  # noqa: BLE001
        return False, f"{type(e).__name__}"


def verify(items_path: str, candidates_path: str, offline: bool = False, required: int = REQUIRED) -> dict:
    """Return the verdict dict (``verdict`` is 'pass' or 'fail')."""
    problems: list[dict] = []
    try:
        chosen = json.loads(Path(items_path).read_text(encoding="utf-8"))
        cands = json.loads(Path(candidates_path).read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        return {"verdict": "fail", "problems": [{"item": None, "reason": f"cannot read inputs: {e}"}]}

    items = chosen.get("items") if isinstance(chosen, dict) else chosen
    if not isinstance(items, list):
        items = []
    issued = {c["url"]: c for c in cands.get("items", [])}
    allowed_hosts = {s["host"] for s in cands.get("sources", [])}
    window = int(cands.get("window_days", 14))
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=window)

    if len(items) != required:
        problems.append({"item": None, "reason": f"expected exactly {required} items, got {len(items)}"})

    seen_urls, seen_sources = set(), {}
    for i, it in enumerate(items, 1):
        tag = f"item {i}"
        if not isinstance(it, dict):
            problems.append({"item": tag, "reason": "not an object"})
            continue
        url = (it.get("url") or "").strip()
        title = (it.get("title") or "").strip()
        why = (it.get("why") or "").strip()
        if not url:
            problems.append({"item": tag, "reason": "missing url"})
            continue
        host = urllib.parse.urlparse(url).netloc.lower()
        host = host[4:] if host.startswith("www.") else host
        if url in seen_urls:
            problems.append({"item": tag, "reason": "duplicate url"})
        seen_urls.add(url)
        if not any(host == h or host.endswith("." + h) for h in allowed_hosts):
            problems.append({"item": tag, "reason": f"host '{host}' is not one of the named sources"})
        if url not in issued:
            problems.append({"item": tag, "reason": "url was not among the fetched candidates — where did it come from?"})
        else:
            c = issued[url]
            if title and c.get("title") and title.lower()[:40] != c["title"].lower()[:40]:
                problems.append({"item": tag, "reason": f"title does not match the source's title ('{c['title'][:60]}')"})
            if c.get("published") and dt.datetime.fromisoformat(c["published"]) < cutoff:
                problems.append({"item": tag, "reason": f"older than the {window}-day window"})
            seen_sources[c.get("source")] = seen_sources.get(c.get("source"), 0) + 1
        if len(why.split()) < MIN_WHY_WORDS:
            problems.append({"item": tag, "reason": f"'why' must be at least {MIN_WHY_WORDS} words of your own reasoning"})
        if not offline and url in issued:
            ok, note = resolves(url)
            if not ok:
                problems.append({"item": tag, "reason": f"url does not resolve ({note})"})

    verdict = {"verdict": "pass" if not problems else "fail", "checked": len(items),
               "sources_used": seen_sources, "problems": problems}
    if problems:
        verdict["instruction"] = ("Fix ONLY the items named above and run this verifier again. Do not invent a URL: "
                                  "pick a different candidate from candidates.json.")
    return verdict


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("items")
    ap.add_argument("candidates")
    ap.add_argument("--offline", action="store_true", help="skip the live URL check")
    ap.add_argument("--required", type=int, default=REQUIRED)
    args = ap.parse_args()
    verdict = verify(args.items, args.candidates, offline=args.offline, required=args.required)
    print(json.dumps(verdict, indent=2))
    return 0 if verdict["verdict"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
