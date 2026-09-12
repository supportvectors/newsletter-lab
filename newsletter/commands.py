"""The /newsletter slash command.

    /newsletter            status
    /newsletter open       arm the open loop (no verifiers)
    /newsletter closed     arm the closed loop (verifier after every step)
    /newsletter off        hide the lab's tools
    /newsletter show       open the latest newsletter.html
    /newsletter where      print today's run directory
    /newsletter autoopen on|off
"""

from __future__ import annotations

import shlex

from .paths import latest_run_dir, open_in_browser, run_dir
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
        d = latest_run_dir()
        p = d / "newsletter.html" if d else None
        if not p or not p.exists():
            return "No newsletter has been rendered yet."
        return f"Opening {p}" if open_in_browser(p) else f"Could not launch a browser; the page is at {p}"
    if cmd == "autoopen":
        on = arg.lower() in ("on", "1", "true", "yes")
        s = update_settings(open_page=on)
        return f"open_page = {'on' if s.open_page else 'off'}."
    return f"Unknown /newsletter subcommand '{cmd}'.\n" + (__doc__ or "").strip()
