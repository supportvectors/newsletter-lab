"""The plugin layer: tool handlers driven directly (no model, no network) and, when Hermes is
importable, discovery through Hermes' own PluginManager with the /newsletter command."""

from __future__ import annotations

import datetime as dt
import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))   # append, not insert: the lab's tools/ must not shadow Hermes' own tools package

from newsletter import handlers, hooks, settings  # noqa: E402
from newsletter import paths as paths_mod  # noqa: E402

NOW = dt.datetime.now(dt.timezone.utc)


@pytest.fixture
def lab(tmp_path, monkeypatch):
    for v in ("NEWSLETTER_LAB_MODE", "NEWSLETTER_LAB_OPEN_PAGE", "NEWSLETTER_LAB_RUN_DIR"):
        monkeypatch.delenv(v, raising=False)
    settings.bind(None)
    settings.clear_overrides()
    settings.update_settings(mode="closed", open_page=False, run_dir=str(tmp_path / "runs"))
    # no network: the fetcher returns a fixture pool
    def fake_fetch(out, sources=None, window_days=None, only=None, log=None):
        items = []
        for k, (src, host) in enumerate([("OpenAI News", "openai.com"), ("Google DeepMind", "deepmind.google"),
                                         ("Hugging Face Blog", "huggingface.co"), ("arXiv cs.AI", "arxiv.org"),
                                         ("Hacker News", "news.ycombinator.com")]):
            for j in range(3):
                items.append({"id": f"c{k}{j}", "source": src, "host": host, "title": f"{src} story {j} about agents",
                              "url": f"https://{host}/story-{k}-{j}", "published": (NOW - dt.timedelta(days=j)).isoformat(),
                              "summary": f"A summary of story {j} from {src}: the model reached 87 percent."})
        doc = {"fetched_at": NOW.isoformat(), "window_days": 14, "errors": [{"source": "Anthropic", "error": "HTTPError: 404"}],
               "sources": [{"name": s, "host": h, "items": 3} for s, h in
                           [("OpenAI News", "openai.com"), ("Google DeepMind", "deepmind.google"), ("Hugging Face Blog", "huggingface.co"),
                            ("arXiv cs.AI", "arxiv.org"), ("Hacker News", "news.ycombinator.com")]] + [{"name": "Anthropic", "host": "anthropic.com", "items": 0}],
               "items": items}
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(json.dumps(doc))
        return doc
    monkeypatch.setattr(handlers._fetch, "fetch", fake_fetch)
    monkeypatch.setattr(handlers._vs, "resolves", lambda url: (True, "HTTP 200"))
    yield tmp_path
    settings.clear_overrides()


def _pick(pool, n=5):
    chosen = [pool[0], pool[3], pool[6], pool[9], pool[12]][:n]
    return [{"source": c["source"], "title": c["title"], "url": c["url"],
             "why": "It shows a concrete technique an engineer can try on Monday morning."} for c in chosen]


def _draft(items):
    secs = [f"## {i}. {it['title']}\n\n" + ("This item describes a technique for agents that a working engineer can put to use this week; " * 2)
            + "the summary reports a result and the reason we picked it is the practical angle it offers.\n\n" + f"{it['url']}\n"
            for i, it in enumerate(items, 1)]
    return ("This week's five share a theme: the loop around the model is where the engineering happens, and each of these "
            "items is a small piece of evidence for that claim, from a technique to a release to a measured result.\n\n" + "\n".join(secs))


def test_closed_loop_end_to_end_through_the_tools(lab):
    f = json.loads(handlers.fetch_sources({}, session_id="s"))
    assert len(f["candidates"]) == 15 and f["sources_with_nothing"] == ["Anthropic"]
    assert "Anthropic" in f["note"]
    items = _pick(f["candidates"])
    assert json.loads(handlers.save_digest({"items": items}))["count"] == 5
    assert json.loads(handlers.verify_research({}))["verdict"] == "pass"
    assert json.loads(handlers.save_draft({"markdown": _draft(items)}))["words"] > 250
    assert json.loads(handlers.verify_draft({}))["verdict"] == "pass"
    r = json.loads(handlers.render_page({}))
    assert Path(r["saved_to"]).exists() and r["opened_in_browser"] is False
    assert json.loads(handlers.verify_render({}))["verdict"] == "pass"


def test_verifier_catches_the_remembered_anthropic_link(lab):
    f = json.loads(handlers.fetch_sources({}))
    items = _pick(f["candidates"])
    items[2] = {"source": "Anthropic", "title": "Something Anthropic surely published", "url": "https://www.anthropic.com/news/surely",
                "why": "Because a named source with nothing today is a temptation to remember."}
    handlers.save_digest({"items": items})
    v = json.loads(handlers.verify_research({}))
    assert v["verdict"] == "fail" and any("not among the fetched candidates" in p["reason"] for p in v["problems"])


def test_open_mode_hides_the_verifiers(lab):
    settings.update_settings(mode="open")
    handlers.fetch_sources({})
    assert "not available" in json.loads(handlers.verify_research({}))["error"]
    assert "not available" in json.loads(handlers.render_page({}))["error"]
    assert "save_digest" in hooks.on_pre_llm_call(session_id="s", user_message="write the newsletter")["context"]
    assert "research-digest-open" in hooks.on_pre_llm_call(session_id="s", user_message="write the newsletter")["context"]
    assert hooks.on_pre_llm_call(session_id="s", user_message="what is the capital of France?") is None
    settings.update_settings(mode="closed")
    assert "verify_research" in hooks.on_pre_llm_call(session_id="s", user_message="research this week's digest")["context"]
    settings.update_settings(mode="off")
    assert "is off" in json.loads(handlers.fetch_sources({}))["error"]


def test_save_page_by_hand_then_verify(lab):
    f = json.loads(handlers.fetch_sources({}))
    items = _pick(f["candidates"])
    handlers.save_digest({"items": items}); handlers.save_draft({"markdown": _draft(items)})
    handlers.render_page({})
    page = (paths_mod.run_dir() / "newsletter.html").read_text()
    broken = page.replace("Read the original", "{{ITEM_CTA}}")
    handlers.save_page({"html": broken})
    v = json.loads(handlers.verify_render({}))
    assert v["verdict"] == "fail" and any("placeholder" in p["reason"] for p in v["problems"])


# -- through Hermes' loader ------------------------------------------------------------------

def _hermes_available():
    try:
        import hermes_cli.plugins  # noqa: F401
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _hermes_available(), reason="hermes_cli not importable")
def test_discovery_and_slash_command(tmp_path, monkeypatch):
    home = tmp_path / "home"
    (home / "plugins").mkdir(parents=True)
    os.symlink(ROOT, home / "plugins" / "newsletter-lab")
    (home / "config.yaml").write_text("plugins:\n  enabled:\n    - newsletter-lab\n")
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setenv("NEWSLETTER_LAB_OPEN_PAGE", "0")
    import hermes_cli.plugins as pmod
    from tools.registry import registry
    mgr = pmod.PluginManager()
    mgr.discover_and_load()
    lp = mgr._plugins.get("newsletter-lab")
    assert lp is not None and lp.enabled, getattr(lp, "error", "not discovered")
    for name in ("fetch_sources", "save_digest", "verify_research", "save_draft", "verify_draft", "save_page", "verify_render", "render_page"):
        assert registry.get_entry(name) is not None, name
    cmd = pmod.get_plugin_command_handler("newsletter")
    assert "OPEN loop" in cmd("open")
    assert registry.get_entry("fetch_sources").check_fn() is True
    assert registry.get_entry("verify_research").check_fn() is False
    assert "CLOSED loop" in cmd("closed")
    assert registry.get_entry("verify_research").check_fn() is True
    from model_tools import get_tool_definitions
    names = {t["function"]["name"] for t in get_tool_definitions(quiet_mode=True, skip_tool_search_assembly=True)}
    assert {"fetch_sources", "verify_research", "render_page"} <= names
    cmd("open")
    names = {t["function"]["name"] for t in get_tool_definitions(quiet_mode=True, skip_tool_search_assembly=True)}
    assert "fetch_sources" in names and "verify_research" not in names
    cmd("off")
    assert registry.get_entry("fetch_sources").check_fn() is False
    try:
        mgr.unload_all()
    except Exception:
        pass


# -- open and closed runs live side by side ---------------------------------------------------

def test_runs_split_by_mode_and_compare(lab):
    settings.update_settings(mode="open")
    f = json.loads(handlers.fetch_sources({}))
    items = _pick(f["candidates"])
    handlers.save_digest({"items": items}); handlers.save_draft({"markdown": _draft(items)})
    open_dir = paths_mod.run_dir()
    assert open_dir.name == "open" and (open_dir / "draft.md").exists()
    settings.update_settings(mode="closed")
    closed_dir = paths_mod.run_dir()
    assert closed_dir.name == "closed" and closed_dir.parent == open_dir.parent
    assert not (closed_dir / "draft.md").exists()          # the closed run starts clean
    handlers.fetch_sources({}); handlers.save_digest({"items": items}); handlers.save_draft({"markdown": _draft(items)})
    handlers.render_page({})
    assert (closed_dir / "newsletter.html").exists() and (open_dir / "draft.md").exists()
    from newsletter import commands
    out = commands.handle_command("compare")
    assert "open   — not rendered today" in out and str(closed_dir / "newsletter.html") in out
    assert paths_mod.latest_page("closed") == closed_dir / "newsletter.html"
    assert paths_mod.latest_page("open") is None
    assert "No open-loop newsletter" in commands.handle_command("show open")


def test_mechanical_render_keeps_the_models_page(lab):
    f = json.loads(handlers.fetch_sources({}))
    items = _pick(f["candidates"])
    handlers.save_digest({"items": items}); handlers.save_draft({"markdown": _draft(items)})
    handlers.render_page({})
    d = paths_mod.run_dir()
    by_model = (d / "newsletter.html").read_text().replace("Read the original", "Read it")
    handlers.save_page({"html": by_model})
    out = json.loads(handlers.render_page({}))
    assert (d / "newsletter-by-model.html").read_text() == by_model
    assert "Read the original" in (d / "newsletter.html").read_text()
    assert "newsletter-by-model.html" in out["note"]
