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

You will run the pipeline twice. First **open loop**: the three skills with no verifier, and you
are the verifier, by hand, afterwards. Then **closed loop**: the same three skills, each ending by
calling its verifier and repairing what it names. The page at the end may look identical. What
happened on the way to it will not.

## Contents

1. [What is here](#what-is-here)
2. [Before you start](#before-you-start)
3. [Install](#install)
4. [Check the install](#check-the-install)
5. [Part one — open loop](#part-one--open-loop)
6. [Part two — the verifiers, by hand](#part-two--the-verifiers-by-hand)
7. [Part three — closed loop](#part-three--closed-loop)
8. [Part four — the mechanical step](#part-four--the-mechanical-step)
9. [What to bring to the discussion](#what-to-bring-to-the-discussion)
10. [Reference: commands, tools, files](#reference-commands-tools-files)
11. [Troubleshooting](#troubleshooting)

## What is here

```
plugin.yaml, __init__.py  the Hermes plugin: 8 tools, 1 hook, 6 skills, the /newsletter command
newsletter/               settings, paths, tool handlers, the arming hook, /newsletter
sources.yaml              the named sources and the allow-list the verifier derives from them
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

The tools the model sees are thin wrappers over the scripts in `tools/` — the same verifiers you
can read and run by hand. `fetch_sources` writes the pool, `save_digest` / `save_draft` /
`save_page` write the run's files, `verify_research` / `verify_draft` / `verify_render` judge
them, `render_page` renders by code. The verifiers and `render_page` exist only in **closed**
mode; in **open** mode the model cannot call them even if it wants to. That is deliberate: the
open loop is not "the model forgot to verify", it is a harness with no sensor.

## Before you start

You need three things.

**Hermes Agent**, installed and working, with a model configured. Check with:

```bash
hermes --version
hermes chat -q "say hello"
```

If the second command does not answer, fix that first — nothing below will work without it.

**A model that is good with tools.** The lab makes eight tool calls in a row and hands the model
JSON to copy from. Any current Anthropic, OpenAI or Google model is fine, as is DeepSeek V4.1 Flash
via OpenRouter (cheap, and what the room will use by default):

```yaml
# ~/.hermes/config.yaml
model:
  default: deepseek/deepseek-v4.1-flash
  provider: openrouter
```

with `OPENROUTER_API_KEY` in `~/.hermes/.env`. Weak or tiny local models will "help" by inventing
URLs, which is instructive but frustrating; save that experiment for after the first clean run.

**Network access to the sources.** The fetcher reads public RSS feeds and two index pages
(`sources.yaml`). On a corporate network some of them will be blocked. That is fine — in fact it
is part of the lesson — but if *all* of them are blocked the research step has nothing to work
with. A quick check, no Hermes needed:

```bash
python3 -c "import urllib.request;print(urllib.request.urlopen('https://huggingface.co/blog/feed.xml',timeout=15).status)"
```

`200` means you are good.

## Install

One command, from any directory:

```bash
hermes plugins install supportvectors/newsletter-lab --enable
```

You will see a warning that the source is "custom (unreviewed)". Correct — it is ours, not from the
Hermes catalog. The plugin is cloned into `~/.hermes/plugins/newsletter-lab` and enabled.

**Now restart Hermes.** Plugins are discovered at start-up. On the Desktop app that means *quit*
(⌘Q / from the menu), not merely closing the window; in a terminal, end the session and start a new
`hermes` one. If you also run the gateway (Telegram, Discord…), `hermes gateway restart` as well.
Skipping the restart is the number-one reason the tools "aren't there".

Nothing else to configure. The plugin knows its own directory; a run's files land under
`~/.hermes/plugin-data/newsletter-lab/runs/<date>/open/` or `.../<date>/closed/`, depending on
the mode — so the two loops' results sit side by side.

## Check the install

Three checks, thirty seconds. From the shell:

```bash
hermes plugins doctor newsletter-lab
```

Expect `8 tool(s), 1 hook(s)`, six skills and the `/newsletter` command, with no errors. (Plain
`hermes plugins doctor` with no argument inspects the *current directory* and will complain that
your home folder has no manifest — give it the plugin name.)

Then, in a Hermes chat:

```
/newsletter
```

Expect something like:

```
Newsletter lab: off
  today's run: /Users/you/.hermes/plugin-data/newsletter-lab/runs/2026-09-12
  open page automatically: on
  arm with /newsletter open or /newsletter closed
```

Finally, arm it and confirm the model can see the tools:

```
/newsletter open
what tools do you have for the newsletter?
```

It should name `fetch_sources`, `save_digest`, `save_draft`, `save_page` — and **not**
`verify_research`, `verify_draft`, `verify_render` or `render_page`. If it lists nothing of the
kind, you did not restart; if it lists the verifiers in open mode, you are running a stale build —
see Troubleshooting.

## Part one — open loop

Three prompts, one per message. Each one is a separate request, and each request is one step of
the pipeline. (Do not chain them into a single prompt: you want to see each step's result before
the next consumes it, and you want each step to be its own trace.)

```
/newsletter open
use research-digest-open to gather this week's five items
```

Read the reply before you go on. Then:

```
use newsletter-draft-open to write the newsletter
```

and:

```
use newsletter-render-open to render it
```

The page opens in your browser when it is written. Look at it. It will probably look fine. That is
the point of the next part.

### What to look for at each step

**Research.** The first tool call is `fetch_sources`. Expand it in the transcript and read the
result: it lists every source with a count, and a field `sources_with_nothing`. On most days at
least one of the ten sources returns nothing (the two scraped index pages, Anthropic and Meta AI,
fail most often; on a locked-down network several feeds will). The skill tells the model to *say
which sources contributed nothing and not to fill the gap from memory*. Did it? Watch for three
behaviours:

- It names the empty sources and picks five from what came back. Good.
- It picks five and never mentions the gap. A quiet omission — the reader of the newsletter will
  never know Anthropic was not consulted.
- It "remembers" an Anthropic article and includes it with a URL it typed itself. This is the
  silent failure the whole lab is about. Nothing will complain. `save_digest` saves whatever it is
  given.

Also check the `why` field on each item in the `save_digest` call. Is it the model's judgment, or a
paraphrase of a summary it has not read? Did it copy the title exactly, or "tidy" it?

**Draft.** The draft is Markdown: an opening paragraph, then `## 1. <title>` sections, each ending
with the item's URL on its own line. Open the `save_draft` call and read the text. Look for direct
quotations in quotation marks — where would the model have got a quote? It has a title and a
200-character summary. Look for "see also" links or a URL that is not one of the five. Look for
an item that merged with another, or a sixth that appeared. Look for a chat reply wearing a
newsletter's clothes ("Here is the newsletter you asked for! …"). Count the sections.

**Render.** The model was told to copy `template/newsletter.html` verbatim, fill the placeholders,
repeat the article block once per item, and remove the two marker comments. Open the page in the
browser *and* view its source (or `cat` the file). Things that go wrong here and look fine in the
browser: a `{{ITEM_URL}}` left in an `href` (the link is dead, the text reads fine); the CSS
"improved" (a colour changed, a font added — the house style is gone and nobody said so); an item
dropped, because the model got bored on the fifth repetition; an `<!-- ITEM START -->` comment
still in the page; a `<script>` that was never asked for.

Note the token count for the three steps if your setup shows it (Hermes prints it at the end of
the reply; Phoenix, if you have the OTel plugin, shows it per step). You will compare it later.

## Part two — the verifiers, by hand

Now be the harness. The three verifiers are plain scripts in the installed plugin; run them against
what the agent just produced:

```bash
R=~/.hermes/plugin-data/newsletter-lab/runs/$(date +%F)/open
L=~/.hermes/plugins/newsletter-lab
python3 $L/tools/verify_research.py $R/items.json $R/candidates.json
python3 $L/tools/verify_draft.py    $R/draft.md   $R/items.json
python3 $L/tools/verify_render.py   $R/newsletter.html $R/items.json
```

Each prints a JSON verdict and exits `0` on pass, `1` on fail. A failure names the item and the
reason, for example:

```json
{
  "verdict": "fail",
  "checked": 5,
  "problems": [
    {"item": "item 3", "reason": "url was not among the fetched candidates — where did it come from?"},
    {"item": "item 5", "reason": "'why' must be at least 8 words of your own reasoning"}
  ],
  "instruction": "Fix ONLY the items named above and run this verifier again. Do not invent a URL: pick a different candidate from candidates.json."
}
```

### What to look for

Open each script — they are short — and ask of every check: **what does the verifier know that
the model did not?** `verify_research` knows `candidates.json` (the ledger of what was really
fetched), `sources.yaml` (the allow-list of hosts) and the network (it fetches every URL). The model
had none of those as *data*; it had them as things it was told. `verify_draft` holds the item
list, but as a dict it looks things up in, not as a memory it trusts; it counts sections, matches
URLs, and checks that any quoted span of 40+ characters actually appears in the source material.
`verify_render` holds the template — the spec the page was supposed to follow — and compares the
`<style>` block byte for byte.

Notice what the verifiers are *not*: they are not a second model, not a judge of quality, not
"does this read well". They check the things a program can check with certainty, and they say
which item, not just pass/fail. A verifier that says "something is wrong" sends the driver back
to the start; one that says "item 3, this URL" lets it fix item 3.

Now look at the page in the browser again, knowing what the verifiers found. Could you have seen
it?

If all three passed on the first try — it happens, with a strong model on a good day — you have
learned something too: you now know it passed, which you did not know a minute ago. Run the
research step again tomorrow; the sources will be different.

## Part three — closed loop

```
/newsletter closed
use research-digest to gather this week's five items
use newsletter-draft to write the newsletter
use newsletter-render to render it
```

Same three prompts without `-open`. Two things changed underneath: the tool list now includes the
verifiers (and `render_page`), and each skill's procedure ends with "call the verifier; on `fail`,
fix *only* what it names, save again, verify again; give up after three".

### What to look for

**Where the retry happens.** In the engine lab a failed step was retried at the step. Here you
should see the same shape: `save_digest` → `verify_research` returns `fail` naming item 3 →
`save_digest` again with item 3 replaced → `verify_research` returns `pass`. Not a restart from
`fetch_sources`. Not a rewrite of all five. Expand the tool calls and confirm the repair was local.

**Whether the model obeyed the verifier or argued with it.** The interesting transcripts are the
ones where the verifier says "URL was not among the fetched candidates" and the model's next move
is to *explain* why its URL is right, or to "fix" the URL by editing it rather than choosing another
candidate. A verifier can be ignored; it cannot be fooled. Watch whether the model tries.

**The give-up.** If a step fails three verifications, the skill says stop and tell the user what
keeps being rejected. That is a governor: without it a determined model and a strict verifier will
loop until the budget is gone. If you see three failures, read them — the same reason three times
usually means the model cannot do what is asked (an item whose URL genuinely will not resolve),
and the right move is a human's, not a fourth retry.

**The bill.** Compare the token count with the open-loop run. The closed loop costs more — every
verifier call is a round trip, every repair is a re-generation — and buys you a page you know is
right. That trade is the whole subject of the afternoon: how much sensor for how much certainty.

**The page.** `/newsletter compare` opens today's open-loop and closed-loop pages side by side
(they live in `runs/<date>/open/` and `runs/<date>/closed/`; nothing is overwritten). Are they
different? Sometimes not visibly. That is the lesson, seen from the other side. Run the closed-loop
verifiers by hand too, with `R=.../runs/$(date +%F)/closed` — they should all pass now, and you
should be able to say why.

## Part four — the mechanical step

Still in closed mode:

```
render the newsletter mechanically
```

The render skill calls `render_page` instead of filling the template by hand. It is `tools/render.py`:
the same template, the same inputs, no model. It cannot leave a placeholder, cannot drop an item,
cannot improve the CSS, so `verify_render` has nothing to say — and the step costs no tokens beyond
the one tool call. The page the model rendered a minute ago is kept beside it as
`newsletter-by-model.html` in the closed run's directory; `diff` the two.

Ask yourself which of the three steps *should* have been code all along, and which could never be.
Rendering is a pure function of its inputs; a model doing it is a model doing arithmetic. Research
is judgment — "interesting to a working engineer" is not a regex. Drafting is in between, and
the verifier for it is the least certain of the three (it checks shape and provenance, not
whether the prose is any good). This is the pipeline-D move from the engine lab: once a step is
mechanical, take it away from the driver and give it to the machine.

## What to bring to the discussion

For each of the three steps, one sentence: what silent failure did you see, or would you expect,
and what information would a verifier need to catch it?

One transcript excerpt where the closed loop repaired something the open loop had passed through.
If you have none, one where the verifiers passed everything on the first try — and your guess as
to why.

The two token counts.

A thing the verifiers *cannot* catch that a reader would notice. (There are several. The best one
is worth a slide.)

## Reference: commands, tools, files

**`/newsletter` command**

| command | effect |
|---|---|
| `/newsletter` or `/newsletter status` | mode, today's run directory, auto-open setting |
| `/newsletter open` | arm the open loop: `fetch_sources`, `save_digest`, `save_draft`, `save_page` only |
| `/newsletter closed` | arm the closed loop: the four above plus `verify_research`, `verify_draft`, `verify_render`, `render_page` |
| `/newsletter off` | hide the lab's tools from the model |
| `/newsletter show [open\|closed]` | reopen the latest `newsletter.html`, optionally of one loop |
| `/newsletter compare` | open today's open-loop and closed-loop pages side by side |
| `/newsletter where` | print today's run directory |
| `/newsletter autoopen on\|off` | whether a rendered page opens in the browser by itself |

Changing the mode takes effect on the next message; the tool list is rebuilt for it.

**Skills** — say "use `<skill>` to …":

| open loop | closed loop | step |
|---|---|---|
| `research-digest-open` | `research-digest` | five items from the named sources, with a `why` each |
| `newsletter-draft-open` | `newsletter-draft` | opening paragraph plus one section per item, URL last |
| `newsletter-render-open` | `newsletter-render` | the house template, filled; mechanical variant calls `render_page` |

**A run's files** — `~/.hermes/plugin-data/newsletter-lab/runs/<date>/open/` or `.../closed/`:

| file | written by | read by |
|---|---|---|
| `candidates.json` | `fetch_sources` | the model (as its pool); `verify_research` (as the ledger) |
| `items.json` | `save_digest` | `verify_research`, the draft skill, `verify_draft`, `verify_render`, `render_page` |
| `draft.md` | `save_draft` | `verify_draft`, the render skill, `render_page` |
| `newsletter.html` | `save_page` or `render_page` | `verify_render`, your browser |
| `newsletter-by-model.html` | `render_page`, if the model had already rendered a page | you, with `diff` |

One directory per day per mode: the open and closed runs never overwrite each other, and a second
run in the same mode on the same day replaces the first.

**The named sources** are in `sources.yaml` in the installed plugin. Edit it to add a feed — the
verifier's allow-list is derived from the `host` fields, so a new source is automatically allowed
and everything else is automatically not.

## Troubleshooting

**"The newsletter lab is off"** as a tool result. You forgot `/newsletter open` or `/newsletter
closed`. The tools are registered but refuse to act until armed.

**The model says it has no newsletter tools.** You did not restart Hermes after installing (Desktop:
quit, not close). Check with `hermes plugins list` that `newsletter-lab` shows as enabled, then
restart.

**Verifiers visible in open mode, or missing in closed mode.** The tool list is memoised by Hermes
and the plugin invalidates it when the mode changes. If you still see the wrong list, start a new
chat; if it persists, `hermes plugins update newsletter-lab` and restart — you may be on a build
before the invalidation was added.

**`fetch_sources` returns errors for most sources.** Your network blocks them. Try from another
network, or `--only` a subset by hand to see which get through:

```bash
python3 ~/.hermes/plugins/newsletter-lab/tools/fetch_sources.py --out /tmp/c.json
```

It prints one line per source. If everything fails, the lab cannot run here; pair with someone
whose laptop is on a friendlier network.

**The model uses the terminal instead of the tools** (`curl`, `cat`, writing files itself). Some
models do this when the tool list is long. Say "use the lab's tools, not the terminal" once; if it
keeps doing it, that is a finding — write it down. The verifiers still work on whatever ends up in
the run directory.

**The model calls `verify_research` in open mode and gets "not available in this mode".** Correct
behaviour: the tool exists in the registry but is hidden and refuses. The model may have seen its
name in an earlier closed-mode conversation. Start a new chat.

**The page did not open.** `/newsletter show`, or open the path `save_page` returned. On a
headless machine set `/newsletter autoopen off`.

**Tests.** `uv run pytest tests/` in a checkout (or `pip install pytest && python3 -m pytest
tests/`). One test needs Hermes' own interpreter and skips otherwise:
`~/.hermes/venv/bin/python -m pytest tests/ -p no:cacheprovider --import-mode=importlib`.

The tools themselves are standard-library only; any Python 3.9+ runs them, `uv` or not.

## License

MIT. © SupportVectors.
