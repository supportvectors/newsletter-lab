# The Newsletter Lab

*Three skills, three verifiers, one afternoon. A companion to the Steam-Engine Reliability Lab.*

The engine lab showed you a chain of ten steps whose failures are silent. This lab is the same
lesson in civilian clothes. An agent researches five interesting AI items from **named sources
only**, writes a short newsletter about them, and renders it into a house HTML template. Every
one of those steps can fail *quietly*: a link that was never fetched, a source the agent
"remembers" because the feed was down, a quotation nobody said, a `{{PLACEHOLDER}}` left in the
page, an item that fell off in rendering. Nothing raises. The next step happily consumes the
result.

So each skill ends with a **verifier** — twenty to eighty lines of ordinary Python that hold
information the model does not: the list of URLs that were actually fetched, the allow-list of
hosts, the network, the template. The verifier is not smarter than the model. It just was not in
the room when the model made things up.

## What is here

```
plugin.yaml, __init__.py  the Hermes plugin: 8 tools, 1 hook, 6 skills, the /newsletter command
newsletter/               settings, paths, tool handlers, the arming hook, /newsletter
sources.yaml              the named sources (X, Y, Z…) and the allow-list the verifier derives
tools/fetch_sources.py    fetch the sources → candidates.json   (the ledger)
tools/verify_research.py  verifier 1: five items, all from candidates.json, hosts allowed, links resolve
tools/verify_draft.py     verifier 2: one section per item, no foreign URLs, no invented quotes
tools/verify_render.py    verifier 3: no placeholders, CSS intact, every item linked, no scripts
tools/render.py           the same rendering done by code, not the model (the pipeline-D move)
template/newsletter.html  the house template
skills/                   research-digest, newsletter-draft, newsletter-render — each ends by calling its verifier
skills-open/              the same three skills with the verifier step removed
tests/                    one test per silent failure the verifiers must catch, plus the plugin through Hermes' loader
```

The tools the model sees are thin wrappers over the scripts in `tools/` — the same twenty-line
verifiers you can read and run by hand. `fetch_sources` writes the pool, `save_digest` /
`save_draft` / `save_page` write the run's files, `verify_research` / `verify_draft` /
`verify_render` judge them, `render_page` renders by code. The verifiers and `render_page` exist
only in **closed** mode; in **open** mode the model cannot call them even if it wants to.

## Install (two minutes)

You need [Hermes Agent](https://github.com/NousResearch/hermes-agent) with a model configured —
your own Anthropic, OpenAI or OpenRouter key is fine.

```bash
hermes plugins install supportvectors/newsletter-lab --enable
```

Restart Hermes (Desktop: quit, not just close the window). Then, in any chat:

```
/newsletter          # status, and where today's run will land
```

Nothing else to configure: the plugin knows its own directory, and a run's files land under
`~/.hermes/plugin-data/newsletter-lab/runs/<date>/` (`/newsletter where` prints it).

## The afternoon

**Open loop.** In a Hermes chat:

```
/newsletter open
use research-digest-open to gather this week's five items
use newsletter-draft-open to write the newsletter
use newsletter-render-open to render it
```

The page opens in your browser when it is written. Then run the three verifiers *by hand* on what
the agent produced — they are scripts, and this is the moment to read them:

```bash
R=~/.hermes/plugin-data/newsletter-lab/runs/$(date +%F)
L=~/.hermes/plugins/newsletter-lab
python3 $L/tools/verify_research.py $R/items.json $R/candidates.json
python3 $L/tools/verify_draft.py    $R/draft.md   $R/items.json
python3 $L/tools/verify_render.py   $R/newsletter.html $R/items.json
```

Read what they say. Then look at the page again.

**Closed loop.** `/newsletter closed`, then the same three prompts without `-open`. Watch where the
retry happens — at the step that failed, with the verifier's message naming the one item to fix —
and compare the token count.

**The mechanical step.** In closed mode, ask for *the mechanical rendering*: the skill calls
`render_page`, which fills the same template by code. Same page, no model, nothing for the verifier
to say. Which of the three steps *should* have been code all along? Which could never be?

`/newsletter show` reopens the latest page; `/newsletter autoopen off` stops pages opening by
themselves; `/newsletter off` hides the lab's tools from the model.

## Where the silent failures live

| step | what fails quietly | who can tell |
|---|---|---|
| research | a named source returned nothing and the agent "remembers" an article; a link that was never fetched; a source that is not on the list; an old item | `candidates.json` (the ledger), `sources.yaml`, the network |
| draft | a quotation nobody said; a "see also" link; an item dropped or doubled; a chat reply dressed as a newsletter | the item list, held as data |
| render | `{{ITEM_URL}}` still on the page; the CSS "improved"; a missing article; a stray `<script>` | the template |

## Tests

```bash
uv run pytest tests/          # uv sync installs pytest from the dev group
# or, without uv:
pip install pytest && python3 -m pytest tests/
```

The tools themselves are standard-library only; any Python 3.9+ runs them, `uv` or not.

## License

MIT. © SupportVectors.
