"""Tool schemas — what the model reads."""

FETCH_SOURCES = {
    "name": "fetch_sources",
    "description": "Fetch this week's candidate items from the newsletter's named sources (feeds and index pages "
                   "listed in sources.yaml). Writes candidates.json for today's run and returns the pool: one entry "
                   "per candidate with id, source, title, url, published and a short summary, plus which sources "
                   "returned nothing. The digest may only be built from this pool.",
    "parameters": {"type": "object", "properties": {
        "window_days": {"type": "integer", "description": "How far back an item may be dated (default from sources.yaml, 14)."}},
        "required": []},
}

_ITEM = {"type": "object", "properties": {
    "id": {"type": "string", "description": "The candidate's id from fetch_sources (optional)."},
    "source": {"type": "string", "description": "The candidate's source name, exactly as returned."},
    "title": {"type": "string", "description": "The candidate's title, copied exactly."},
    "url": {"type": "string", "description": "The candidate's url, copied exactly."},
    "why": {"type": "string", "description": "One or two sentences, at least 8 words, in your own words: why a working AI engineer should read it."}},
    "required": ["source", "title", "url", "why"]}

SAVE_DIGEST = {
    "name": "save_digest",
    "description": "Save the research digest — exactly five items chosen from the fetched pool — as items.json for today's run.",
    "parameters": {"type": "object", "properties": {"items": {"type": "array", "items": _ITEM, "description": "Exactly five items."}},
                   "required": ["items"]},
}

VERIFY_RESEARCH = {
    "name": "verify_research",
    "description": "Verify the saved digest against the fetched pool: exactly five items, every url one that was actually "
                   "fetched, every host one of the named sources, dated within the window, titles matching, a real reason "
                   "for each, and each url resolving on the network right now. Returns pass, or fail with the items and reasons.",
    "parameters": {"type": "object", "properties": {}, "required": []},
}

SAVE_DRAFT = {
    "name": "save_draft",
    "description": "Save the newsletter draft (Markdown) as draft.md for today's run: an opening paragraph, then one "
                   "'## <n>. <title>' section per digest item, each ending with the item's url on its own line.",
    "parameters": {"type": "object", "properties": {"markdown": {"type": "string", "description": "The whole draft."}},
                   "required": ["markdown"]},
}

VERIFY_DRAFT = {
    "name": "verify_draft",
    "description": "Verify the saved draft against the digest: one section per item and only those, each section's url "
                   "the item's own, no other urls, no invented quotations, 250-700 words, no chat boilerplate. "
                   "Returns pass, or fail with the sections and reasons.",
    "parameters": {"type": "object", "properties": {}, "required": []},
}

SAVE_PAGE = {
    "name": "save_page",
    "description": "Save the rendered newsletter (the template filled in by hand) as newsletter.html for today's run.",
    "parameters": {"type": "object", "properties": {"html": {"type": "string", "description": "The complete HTML page."}},
                   "required": ["html"]},
}

VERIFY_RENDER = {
    "name": "verify_render",
    "description": "Verify the saved page against the template and the digest: no {{PLACEHOLDER}} left, marker comments "
                   "removed, the template's CSS untouched, exactly one article per item in order with its own link, "
                   "no scripts, title and date filled. Returns pass, or fail with what to fix.",
    "parameters": {"type": "object", "properties": {}, "required": []},
}

RENDER_PAGE = {
    "name": "render_page",
    "description": "Render newsletter.html from the saved draft and digest with code instead of by hand — the same "
                   "template, deterministic, nothing for verify_render to find. Use it when the user asks for the "
                   "mechanical rendering.",
    "parameters": {"type": "object", "properties": {
        "title": {"type": "string", "description": "Newsletter title (default: Five Things Worth Reading)."}},
        "required": []},
}
