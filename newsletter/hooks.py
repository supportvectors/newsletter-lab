"""pre_llm_call: point the model at the right skills for the current mode."""

from __future__ import annotations

import re
from typing import Any, Optional

from .settings import get_settings

_WORDS = re.compile(r"\b(newsletter|digest|research|draft|render|items|sources|five things)\b", re.I)

_BANNER = {
    "open": ("[newsletter-lab] The newsletter lab is armed in OPEN-LOOP mode: no verifiers. Load the skill "
             "`newsletter-lab:research-digest-open` for the research step, `newsletter-lab:newsletter-draft-open` "
             "for the writing step, `newsletter-lab:newsletter-render-open` for the rendering step. Use the lab's "
             "tools (fetch_sources, save_digest, save_draft, save_page); do not use the terminal for this task."),
    "closed": ("[newsletter-lab] The newsletter lab is armed in CLOSED-LOOP mode: a verifier after every step. Load "
               "the skill `newsletter-lab:research-digest` for the research step, `newsletter-lab:newsletter-draft` "
               "for the writing step, `newsletter-lab:newsletter-render` for the rendering step. Use the lab's tools "
               "(fetch_sources, save_digest, verify_research, save_draft, verify_draft, save_page, verify_render, "
               "render_page); do not use the terminal for this task."),
}


def on_pre_llm_call(session_id: str = "", user_message: str = "", **kwargs: Any) -> Optional[dict]:
    s = get_settings()
    if s.mode not in _BANNER:
        return None
    text = user_message if isinstance(user_message, str) else ""
    if not _WORDS.search(text):
        return None
    return {"context": _BANNER[s.mode]}
