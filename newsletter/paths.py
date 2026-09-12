"""Where a run's files live. The plugin knows its own directory, so nothing has to be configured."""

from __future__ import annotations

import datetime as dt
import subprocess
import sys
from pathlib import Path

from .settings import get_settings

PLUGIN_DIR = Path(__file__).resolve().parents[1]
SOURCES = PLUGIN_DIR / "sources.yaml"
TEMPLATE = PLUGIN_DIR / "template" / "newsletter.html"


def runs_root() -> Path:
    s = get_settings()
    if s.run_dir:
        d = Path(s.run_dir).expanduser()
    else:
        try:
            from plugins.plugin_storage import plugin_data_dir
            d = plugin_data_dir("newsletter-lab") / "runs"
        except Exception:  # noqa: BLE001
            d = Path.home() / ".hermes" / "plugin-data" / "newsletter-lab" / "runs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def run_dir(mode: str | None = None) -> Path:
    """Today's run directory for a mode: runs/<date>/open or runs/<date>/closed, so the two
    loops' results sit side by side and can be compared. With the lab off, the date directory."""
    mode = mode or get_settings().mode
    d = runs_root() / dt.date.today().isoformat()
    if mode in ("open", "closed"):
        d = d / mode
    d.mkdir(parents=True, exist_ok=True)
    return d


def latest_page(mode: str | None = None) -> Path | None:
    """The most recently written newsletter page, optionally restricted to one loop."""
    pages = [p for p in runs_root().glob("*/*/newsletter*.html") if not mode or p.parent.name == mode]
    pages += [p for p in runs_root().glob("*/newsletter*.html") if not mode]   # pre-split layout
    pages = [p for p in pages if p.name == "newsletter.html"]
    return max(pages, key=lambda p: p.stat().st_mtime) if pages else None


def latest_run_dir() -> Path | None:
    p = latest_page()
    return p.parent if p else None


def open_in_browser(path: Path) -> bool:
    """Done by the harness for zero tokens; never raises."""
    try:
        if sys.platform == "darwin":
            cmd = ["open", str(path)]
        elif sys.platform.startswith("win"):
            import os
            os.startfile(str(path))  # type: ignore[attr-defined]
            return True
        else:
            cmd = ["xdg-open", str(path)]
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         stdin=subprocess.DEVNULL, start_new_session=True)
        return True
    except Exception:  # noqa: BLE001
        return False
