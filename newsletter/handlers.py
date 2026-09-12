"""Tool handlers. Each wraps one of the scripts in tools/ — the same code a student can run by hand."""

from __future__ import annotations

import json
from typing import Any

import importlib.util
import sys
from pathlib import Path

from .paths import PLUGIN_DIR, SOURCES, TEMPLATE, open_in_browser, run_dir
from .settings import get_settings


def _script(name: str):
    """Load tools/<name>.py by path — the scripts stay plain scripts a student can run by hand, and
    the plugin does not depend on how Hermes names the package it loads us as."""
    key = f"newsletter_lab_tools_{name}"
    if key in sys.modules:
        return sys.modules[key]
    spec = importlib.util.spec_from_file_location(key, Path(PLUGIN_DIR) / "tools" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[key] = mod
    spec.loader.exec_module(mod)
    return mod


_fetch = _script("fetch_sources")
_render = _script("render")
_vd = _script("verify_draft")
_vr = _script("verify_render")
_vs = _script("verify_research")


def _err(msg: str) -> str:
    return json.dumps({"error": msg})


def _not_armed() -> str:
    return _err("The newsletter lab is off. Ask the user to run /newsletter open or /newsletter closed.")


def _armed() -> bool:
    return get_settings().mode in ("open", "closed")


def fetch_sources(args: dict, **kwargs: Any) -> str:
    if not _armed():
        return _not_armed()
    d = run_dir()
    log: list[str] = []
    result = _fetch.fetch(str(d / "candidates.json"), sources=str(SOURCES),
                          window_days=args.get("window_days") or None, log=log.append)
    pool = [{"id": it["id"], "source": it["source"], "title": it["title"], "url": it["url"],
             "published": (it.get("published") or "")[:10], "summary": (it.get("summary") or "")[:200]}
            for it in result["items"]]
    empty = [s["name"] for s in result["sources"] if not s["items"]]
    return json.dumps({
        "run_dir": str(d), "candidates_path": str(d / "candidates.json"),
        "sources": result["sources"], "sources_with_nothing": empty, "errors": result["errors"],
        "candidates": pool,
        "note": "Choose exactly five from `candidates`, copying source, title and url exactly. "
                + (f"These named sources returned nothing today: {', '.join(empty)}." if empty else ""),
    })


def save_digest(args: dict, **kwargs: Any) -> str:
    if not _armed():
        return _not_armed()
    items = args.get("items")
    if not isinstance(items, list) or not items:
        return _err("items must be a non-empty list of {source, title, url, why}.")
    d = run_dir()
    p = d / "items.json"
    p.write_text(json.dumps({"items": items}, indent=2), encoding="utf-8")
    return json.dumps({"saved_to": str(p), "count": len(items)})


def verify_research(args: dict, **kwargs: Any) -> str:
    if get_settings().mode != "closed":
        return _err("verify_research is not available in this mode.")
    d = run_dir()
    if not (d / "items.json").exists():
        return _err("No digest saved yet. Call save_digest first.")
    return json.dumps(_vs.verify(str(d / "items.json"), str(d / "candidates.json"), offline=False))


def save_draft(args: dict, **kwargs: Any) -> str:
    if not _armed():
        return _not_armed()
    md = args.get("markdown")
    if not isinstance(md, str) or not md.strip():
        return _err("markdown must be the whole draft.")
    p = run_dir() / "draft.md"
    p.write_text(md, encoding="utf-8")
    return json.dumps({"saved_to": str(p), "words": len(md.split())})


def verify_draft(args: dict, **kwargs: Any) -> str:
    if get_settings().mode != "closed":
        return _err("verify_draft is not available in this mode.")
    d = run_dir()
    if not (d / "draft.md").exists():
        return _err("No draft saved yet. Call save_draft first.")
    return json.dumps(_vd.verify(str(d / "draft.md"), str(d / "items.json")))


def _finish_page(p) -> dict:
    s = get_settings()
    opened = open_in_browser(p) if s.open_page else False
    return {"saved_to": str(p), "opened_in_browser": opened,
            "message": "Tell the user where the page was saved. Do not open the file yourself."}


def save_page(args: dict, **kwargs: Any) -> str:
    if not _armed():
        return _not_armed()
    page = args.get("html")
    if not isinstance(page, str) or "<html" not in page.lower():
        return _err("html must be the complete page.")
    p = run_dir() / "newsletter.html"
    p.write_text(page, encoding="utf-8")
    return json.dumps(_finish_page(p))


def verify_render(args: dict, **kwargs: Any) -> str:
    if get_settings().mode != "closed":
        return _err("verify_render is not available in this mode.")
    d = run_dir()
    if not (d / "newsletter.html").exists():
        return _err("No page saved yet. Call save_page (or render_page) first.")
    return json.dumps(_vr.verify(str(d / "newsletter.html"), str(d / "items.json"), str(TEMPLATE)))


def render_page(args: dict, **kwargs: Any) -> str:
    if get_settings().mode != "closed":
        return _err("render_page is not available in this mode.")
    d = run_dir()
    if not (d / "draft.md").exists() or not (d / "items.json").exists():
        return _err("render_page needs a saved digest and draft.")
    p = d / "newsletter.html"
    if p.exists() and not (d / "newsletter-by-model.html").exists():
        p.rename(d / "newsletter-by-model.html")     # keep the model's page for comparison
    _render.render(str(d / "draft.md"), str(d / "items.json"), str(p), str(TEMPLATE),
                   title=args.get("title") or "Five Things Worth Reading")
    out = _finish_page(p)
    out["note"] = ("Rendered by code, not by the model: the template cannot be left half-filled. "
                   "The page the model rendered earlier, if any, is kept beside it as newsletter-by-model.html.")
    return json.dumps(out)
