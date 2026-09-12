"""newsletter-lab — three skills, three verifiers, one afternoon. A Hermes Agent plugin.

Registration only; the lab lives in ``newsletter/`` and the scripts in ``tools/``. See README.md.
"""

from __future__ import annotations

import logging
from pathlib import Path

from .newsletter import commands, handlers, hooks, schemas, settings

logger = logging.getLogger(__name__)

TOOLSET = "newsletter-lab"
_PLUGIN_DIR = Path(__file__).parent


def _armed() -> bool:
    return settings.get_settings().mode in ("open", "closed")


def _closed() -> bool:
    return settings.get_settings().mode == "closed"


def _uncached(fn):
    """Tool visibility follows /newsletter immediately: opt out of the registry's check_fn cache."""
    try:
        from tools.registry import no_cache_check_fn
        return no_cache_check_fn(fn)
    except Exception:  # noqa: BLE001 — older Hermes without the decorator
        return fn


def register(ctx) -> None:
    settings.bind(ctx)
    always = [("fetch_sources", schemas.FETCH_SOURCES, handlers.fetch_sources, "📰"),
              ("save_digest", schemas.SAVE_DIGEST, handlers.save_digest, "📝"),
              ("save_draft", schemas.SAVE_DRAFT, handlers.save_draft, "✍️"),
              ("save_page", schemas.SAVE_PAGE, handlers.save_page, "🧾")]
    closed_only = [("verify_research", schemas.VERIFY_RESEARCH, handlers.verify_research, "🔍"),
                   ("verify_draft", schemas.VERIFY_DRAFT, handlers.verify_draft, "🔍"),
                   ("verify_render", schemas.VERIFY_RENDER, handlers.verify_render, "🔍"),
                   ("render_page", schemas.RENDER_PAGE, handlers.render_page, "⚙️")]
    for name, schema, handler, emoji in always:
        ctx.register_tool(name=name, toolset=TOOLSET, schema=schema, handler=handler,
                          check_fn=_uncached(_armed), emoji=emoji)
    for name, schema, handler, emoji in closed_only:
        ctx.register_tool(name=name, toolset=TOOLSET, schema=schema, handler=handler,
                          check_fn=_uncached(_closed), emoji=emoji)

    ctx.register_hook("pre_llm_call", hooks.on_pre_llm_call)

    for folder in ("skills", "skills-open"):
        d = _PLUGIN_DIR / folder
        for child in sorted(d.iterdir()) if d.is_dir() else []:
            skill_md = child / "SKILL.md"
            if child.is_dir() and skill_md.exists():
                ctx.register_skill(child.name, skill_md)

    ctx.register_command("newsletter", commands.handle_command,
                         description="Newsletter lab: /newsletter open|closed|off|status|show [open|closed]|compare|where",
                         args_hint="<open|closed|off|status|show|compare|where>")
    logger.info("newsletter-lab registered: 8 tools, 1 hook, 6 skills")
