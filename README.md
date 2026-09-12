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
sources.yaml              the named sources (X, Y, Z…) and the allow-list the verifier derives
tools/fetch_sources.py    fetch the sources → runs/<date>/candidates.json   (the ledger)
tools/verify_research.py  verifier 1: five items, all from candidates.json, hosts allowed, links resolve
tools/verify_draft.py     verifier 2: one section per item, no foreign URLs, no invented quotes
tools/verify_render.py    verifier 3: no placeholders, CSS intact, every item linked, no scripts
tools/render.py           the same rendering done by code, not the model (the pipeline-D move)
template/newsletter.html  the house template
skills/                   research-digest, newsletter-draft, newsletter-render — each ends by running its verifier
skills-open/              the same three skills with the verifier step removed — run these FIRST
tests/                    one test per silent failure the verifiers must catch
```

## Setup (five minutes)

You need [Hermes Agent](https://github.com/NousResearch/hermes-agent) with a model configured
(your own Anthropic, OpenAI or OpenRouter key is fine) and Python 3.9+.

```bash
git clone https://github.com/supportvectors/newsletter-lab ~/newsletter-lab
```

Tell Hermes where the skills are, in `~/.hermes/config.yaml`:

```yaml
skills:
  external_dirs:
    - ~/newsletter-lab/skills-open     # this morning
    # - ~/newsletter-lab/skills        # swap in after lunch
```

and give the skills the lab's path, in `~/.hermes/.env` (Hermes loads it at start):

```
NEWSLETTER_LAB=/Users/<you>/newsletter-lab
```

Restart Hermes (or Hermes Desktop). If you cloned somewhere else, or skip the `.env` line, the
skills will ask you for the path once per chat.

Check the fetcher works on your network before class:

```bash
python3 ~/newsletter-lab/tools/fetch_sources.py --out ~/newsletter-lab/runs/test/candidates.json
```

You should see one line per source. **Two of them will usually fail** (Anthropic and Meta have no
feed; the scraper is brittle by design). Notice that the exit code is still 0 and the JSON is
still valid. Remember that in an hour.

## The afternoon

**Open loop.** With `skills-open` active, in a Hermes chat:

```
use research-digest-open to gather this week's five items
use newsletter-draft-open to write the newsletter
use newsletter-render-open to render it
```

Open `runs/<date>/newsletter.html`. Then run the three verifiers by hand on what the agent
produced:

```bash
cd ~/newsletter-lab && R=runs/$(date +%F)
python3 tools/verify_research.py $R/items.json $R/candidates.json
python3 tools/verify_draft.py    $R/draft.md   $R/items.json
python3 tools/verify_render.py   $R/newsletter.html $R/items.json
```

Read what they say. Then look at the page again.

**Closed loop.** Swap `skills` for `skills-open` in `config.yaml`, restart Hermes, and run the
three skills again (same prompts, without `-open`). Watch where the retry happens — at the step
that failed, with the verifier's message naming the one item to fix — and compare the token count
in your provider's dashboard.

**The mechanical step.** Render once more with `python3 tools/render.py $R/draft.md $R/items.json
--out $R/newsletter.html`. Same page, no model, nothing for the verifier to say. Which of the
three steps *should* have been code all along? Which could never be?

## Where the silent failures live

| step | what fails quietly | who can tell |
|---|---|---|
| research | a named source returned nothing and the agent "remembers" an article; a link that was never fetched; a source that is not on the list; an old item | `candidates.json` (the ledger), `sources.yaml`, the network |
| draft | a quotation nobody said; a "see also" link; an item dropped or doubled; a chat reply dressed as a newsletter | the item list, held as data |
| render | `{{ITEM_URL}}` still on the page; the CSS "improved"; a missing article; a stray `<script>` | the template |

## Tests

```bash
pip install pytest && python3 -m pytest tests/
```

## License

MIT. © SupportVectors.
