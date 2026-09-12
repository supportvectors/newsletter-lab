"""The /newsletter slash command.

    /newsletter            status
    /newsletter open       arm the open loop (no verifiers)
    /newsletter closed     arm the closed loop (verifier after every step)
    /newsletter off        hide the lab's tools
    /newsletter show [open|closed]   open the latest newsletter.html (of that loop)
    /newsletter compare    open today's open-loop and closed-loop pages side by side
    /newsletter where      print today's run directory
    /newsletter autoopen on|off
"""

from __future__ import annotations

import shlex

from .paths import latest_page, open_in_browser, run_dir
from .settings import get_settings, update_settings


def _status() -> str:
    s = get_settings()
    head = {"open": "armed — OPEN loop (no verifiers)", "closed": "armed — CLOSED loop (verifier after every step)",
            "off": "off"}[s.mode]
    lines = [f"Newsletter lab: {head}", f"  today's run: {run_dir()}", f"  open page automatically: {'on' if s.open_page else 'off'}"]
    if s.mode == "open":
        lines.append("  say: use research-digest-open to gather this week's five items")
    elif s.mode == "closed":
        lines.append("  say: use research-digest to gather this week's five items")
    else:
        lines.append("  arm with /newsletter open or /newsletter closed")
    return "\n".join(lines)


def handle_command(raw_args: str) -> str:
    try:
        parts = shlex.split(raw_args or "")
    except ValueError:
        parts = (raw_args or "").split()
    if not parts:
        return _status()
    cmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""
    if cmd in ("open", "closed", "off"):
        s = update_settings(mode=cmd)
        return _status() + ("\n  (tools list refreshed for the next message)" if s.mode != "off" else "")
    if cmd == "status":
        return _status()
    if cmd == "where":
        return str(run_dir())
    if cmd == "show":
        which = arg.lower() if arg.lower() in ("open", "closed") else None
        p = latest_page(which)
        if not p:
            return f"No {which + '-loop ' if which else ''}newsletter has been rendered yet."
        return f"Opening {p}" if open_in_browser(p) else f"Could not launch a browser; the page is at {p}"
    if cmd == "compare":
        out = []
        for which in ("open", "closed"):
            p = run_dir(which) / "newsletter.html"
            if p.exists():
                out.append(f"{which:6s} {p}" + ("" if open_in_browser(p) else "   (could not launch a browser)"))
            else:
                out.append(f"{which:6s} — not rendered today")
        return "Today's pages:\n  " + "\n  ".join(out)
    if cmd == "autoopen":
        on = arg.lower() in ("on", "1", "true", "yes")
        s = update_settings(open_page=on)
        return f"open_page = {'on' if s.open_page else 'off'}."
    return f"Unknown /newsletter subcommand '{cmd}'.\n" + (__doc__ or "").strip()
