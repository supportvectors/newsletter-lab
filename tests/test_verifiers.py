"""The verifiers are the lab. Each test is one silent failure the verifier must catch — and one
honest run it must pass. Offline: candidates.json is a fixture, URL resolution is skipped."""

from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
NOW = dt.datetime.now(dt.timezone.utc)


def _cands():
    items = []
    for k, (src, host) in enumerate([("OpenAI News", "openai.com"), ("Google DeepMind", "deepmind.google"),
                                     ("Hugging Face Blog", "huggingface.co"), ("arXiv cs.AI", "arxiv.org"),
                                     ("Hacker News", "news.ycombinator.com"), ("Microsoft Research", "microsoft.com")]):
        for j in range(3):
            items.append({"id": f"c{k}{j}", "source": src, "host": host, "title": f"{src} story {j} about agents",
                          "url": f"https://{host}/story-{k}-{j}", "published": (NOW - dt.timedelta(days=j)).isoformat(),
                          "summary": f"A summary of story {j} from {src} with a fact: the model reached 87 percent."})
    items.append({"id": "old", "source": "OpenAI News", "host": "openai.com", "title": "An old OpenAI story",
                  "url": "https://openai.com/old", "published": (NOW - dt.timedelta(days=40)).isoformat(), "summary": ""})
    return {"fetched_at": NOW.isoformat(), "window_days": 14,
            "sources": [{"name": s, "host": h, "items": 3} for s, h in
                        [("OpenAI News", "openai.com"), ("Google DeepMind", "deepmind.google"), ("Hugging Face Blog", "huggingface.co"),
                         ("arXiv cs.AI", "arxiv.org"), ("Hacker News", "news.ycombinator.com"), ("Microsoft Research", "microsoft.com"),
                         ("Anthropic", "anthropic.com")]],
            "errors": [{"source": "Anthropic", "error": "HTTPError: 404"}], "items": items}


def _pick(c, n=5):
    return {"items": [{"id": it["id"], "source": it["source"], "title": it["title"], "url": it["url"],
                       "why": "It shows a concrete technique an engineer can try on Monday morning."}
                      for it in [c["items"][0], c["items"][3], c["items"][6], c["items"][9], c["items"][12]][:n]]}


def run(tool, *args):
    p = subprocess.run([sys.executable, str(TOOLS / tool), *map(str, args)], capture_output=True, text=True)
    return p.returncode, json.loads(p.stdout)


@pytest.fixture
def rd(tmp_path):
    c = _cands()
    (tmp_path / "candidates.json").write_text(json.dumps(c))
    (tmp_path / "items.json").write_text(json.dumps(_pick(c)))
    return tmp_path, c


# -- verifier 1 ----------------------------------------------------------------------------

def test_research_passes_an_honest_pick(rd):
    d, _ = rd
    rc, v = run("verify_research.py", d / "items.json", d / "candidates.json", "--offline")
    assert rc == 0 and v["verdict"] == "pass" and v["checked"] == 5


@pytest.mark.parametrize("mutate,reason", [
    (lambda it: it.update(url="https://techcrunch.com/2026/09/10/some-ai-story"), "not one of the named sources"),
    (lambda it: it.update(url="https://www.anthropic.com/news/made-up"), "not among the fetched candidates"),   # a named source that returned nothing — the model 'remembers' one
    (lambda it: it.update(url="https://openai.com/plausible-but-never-fetched"), "not among the fetched candidates"),
    (lambda it: it.update(why="Interesting."), "at least 8 words"),
    (lambda it: it.update(url="https://openai.com/old", title="An old OpenAI story"), "older than the 14-day window"),
    (lambda it: it.update(title="A better title I wrote myself for this story"), "does not match the source's title"),
])
def test_research_catches_silent_failures(rd, mutate, reason):
    d, c = rd
    items = _pick(c)
    mutate(items["items"][2])
    (d / "items.json").write_text(json.dumps(items))
    rc, v = run("verify_research.py", d / "items.json", d / "candidates.json", "--offline")
    assert rc == 1 and any(reason in p["reason"] for p in v["problems"]), v


def test_research_counts(rd):
    d, c = rd
    (d / "items.json").write_text(json.dumps(_pick(c, 4)))
    rc, v = run("verify_research.py", d / "items.json", d / "candidates.json", "--offline")
    assert rc == 1 and "expected exactly 5" in v["problems"][0]["reason"]


# -- verifier 2 ----------------------------------------------------------------------------

def _draft(items, mutate=None):
    secs = []
    for i, it in enumerate(items["items"], 1):
        secs.append(f"## {i}. {it['title']}\n\n" + ("This item describes a technique for agents that a working engineer can put to use this week; " * 2)
                    + "the summary reports a result and the reason we picked it is the practical angle it offers to teams shipping agents.\n\n"
                    + f"{it['url']}\n")
    opener = ("This week's five share a theme: the loop around the model is where the engineering happens, and each of these "
              "items is a small piece of evidence for that claim, from a technique to a release to a measured result.\n\n")
    text = opener + "\n".join(secs)
    return mutate(text) if mutate else text


def test_draft_passes_an_honest_draft(rd):
    d, c = rd
    items = _pick(c)
    (d / "draft.md").write_text(_draft(items))
    rc, v = run("verify_draft.py", d / "draft.md", d / "items.json")
    assert rc == 0 and v["verdict"] == "pass", v


@pytest.mark.parametrize("mutate,reason", [
    (lambda t: t.replace("https://deepmind.google/story-1-0", "https://deepmind.google/story-1-1"), "not one of the digest items"),
    (lambda t: t + "\n## 6. A bonus item I remembered\n\nSome words about it, forty of them at least, to pass the length check that the verifier applies to every section without exception.\n\nhttps://example.com/bonus\n", "6 item sections"),
    (lambda t: t.replace("the practical angle", "the practical angle, as the authors put it, \"a fundamental rethinking of how agents should be built from the ground up\""), "direct quote not found"),
    (lambda t: t.replace("This week's five share a theme", "As an AI, I cannot browse, but this week's five share a theme"), "boilerplate"),
    (lambda t: "\n".join(l for l in t.splitlines() if "story-2-0" not in l), "section has no URL"),
])
def test_draft_catches_silent_failures(rd, mutate, reason):
    d, c = rd
    items = _pick(c)
    (d / "draft.md").write_text(_draft(items, mutate))
    rc, v = run("verify_draft.py", d / "draft.md", d / "items.json")
    assert rc == 1 and any(reason in p["reason"] for p in v["problems"]), v


# -- verifier 3 and the code renderer --------------------------------------------------------

def test_render_py_output_passes_verify_render(rd):
    d, c = rd
    items = _pick(c)
    (d / "draft.md").write_text(_draft(items))
    subprocess.run([sys.executable, str(TOOLS / "render.py"), str(d / "draft.md"), str(d / "items.json"),
                    "--out", str(d / "newsletter.html")], check=True, capture_output=True)
    rc, v = run("verify_render.py", d / "newsletter.html", d / "items.json")
    assert rc == 0 and v["articles"] == 5, v


@pytest.mark.parametrize("mutate,reason", [
    (lambda h: h.replace("Read the original", "{{ITEM_CTA}}"), "placeholder left unfilled"),
    (lambda h: h.replace("--brass: #b8862b", "--brass: #ff00ff"), "CSS was changed"),
    (lambda h: h.replace("https://huggingface.co/story-2-0", "https://huggingface.co/story-2-1"), "missing or wrong link"),
    (lambda h: h.replace("</footer>", "</footer><script>alert(1)</script>"), "no scripts"),
    (lambda h: h.replace("<article>", "<article>", 4).replace("<!doctype html>", "<!doctype html><!-- ITEM START -->"), "marker comments must be removed"),
])
def test_render_catches_silent_failures(rd, mutate, reason):
    d, c = rd
    items = _pick(c)
    (d / "draft.md").write_text(_draft(items))
    subprocess.run([sys.executable, str(TOOLS / "render.py"), str(d / "draft.md"), str(d / "items.json"),
                    "--out", str(d / "newsletter.html")], check=True, capture_output=True)
    h = (d / "newsletter.html").read_text()
    (d / "newsletter.html").write_text(mutate(h))
    rc, v = run("verify_render.py", d / "newsletter.html", d / "items.json")
    assert rc == 1 and any(reason in p["reason"] for p in v["problems"]), v


def test_render_dropped_item(rd):
    d, c = rd
    items = _pick(c)
    (d / "draft.md").write_text(_draft(items))
    subprocess.run([sys.executable, str(TOOLS / "render.py"), str(d / "draft.md"), str(d / "items.json"),
                    "--out", str(d / "newsletter.html")], check=True, capture_output=True)
    h = (d / "newsletter.html").read_text()
    i = h.rfind("<article>"); j = h.rfind("</article>") + len("</article>")
    (d / "newsletter.html").write_text(h[:i] + h[j:])
    rc, v = run("verify_render.py", d / "newsletter.html", d / "items.json")
    assert rc == 1 and any("4 articles" in p["reason"] for p in v["problems"]), v


# -- the fetcher's YAML reader ---------------------------------------------------------------

def test_sources_yaml_parses():
    sys.path.insert(0, str(TOOLS))
    import fetch_sources
    cfg = fetch_sources.load_sources(ROOT / "sources.yaml")
    names = [s["name"] for s in cfg["sources"]]
    assert cfg["window_days"] == 14 and "Hacker News" in names and "Anthropic" in names
    hn = next(s for s in cfg["sources"] if s["kind"] == "hn")
    assert "agent" in hn["keywords"] and "open source" in hn["keywords"]
