"""Lab settings: /newsletter (plugin state) > env NEWSLETTER_LAB_MODE > config.yaml > defaults."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

MODES = ("open", "closed", "off")
DEFAULTS = {"mode": "open", "open_page": True, "run_dir": ""}
_STATE_KEY = "newsletter_settings"
_ctx: Any = None
_overrides: dict[str, Any] = {}


def bind(ctx: Any) -> None:
    global _ctx
    _ctx = ctx


@dataclass(frozen=True)
class Settings:
    mode: str
    open_page: bool
    run_dir: str


def _coerce(key: str, value: Any) -> Any:
    default = DEFAULTS[key]
    if value is None:
        return default
    if isinstance(default, bool):
        return str(value).strip().lower() in ("1", "true", "yes", "on")
    if key == "mode":
        v = str(value).strip().lower()
        return v if v in MODES else "open"
    return str(value)


def _from_state() -> dict:
    if _ctx is None:
        return {}
    try:
        data = _ctx.state.get(_STATE_KEY, default={}) or {}
        return data if isinstance(data, dict) else {}
    except Exception:  # noqa: BLE001
        return {}


def _from_config(key: str) -> Any:
    if _ctx is None:
        return None
    try:
        return _ctx.get_config(key, default=None)
    except Exception:  # noqa: BLE001
        return None


_ENV = {"mode": "NEWSLETTER_LAB_MODE", "open_page": "NEWSLETTER_LAB_OPEN_PAGE", "run_dir": "NEWSLETTER_LAB_RUN_DIR"}


def get_settings() -> Settings:
    state = _from_state()
    values = {}
    for key in DEFAULTS:
        if key in _overrides:
            raw = _overrides[key]
        elif key in state:
            raw = state[key]
        elif os.environ.get(_ENV[key]) is not None:
            raw = os.environ.get(_ENV[key])
        else:
            raw = _from_config(key)
        values[key] = _coerce(key, raw)
    return Settings(**values)


def _invalidate_tool_list() -> None:
    """Hermes memoizes the model's tool list; make it follow /newsletter on the next turn."""
    try:
        from tools.registry import invalidate_check_fn_cache
        invalidate_check_fn_cache()
    except Exception:  # noqa: BLE001
        pass
    try:
        from model_tools import _clear_tool_defs_cache
        _clear_tool_defs_cache()
    except Exception:  # noqa: BLE001
        pass


def update_settings(**changes: Any) -> Settings:
    clean = {k: _coerce(k, v) for k, v in changes.items() if k in DEFAULTS}
    if _ctx is not None:
        try:
            data = _from_state()
            data.update(clean)
            _ctx.state.set(_STATE_KEY, data)
        except Exception:  # noqa: BLE001
            _overrides.update(clean)
    else:
        _overrides.update(clean)
    if "mode" in clean:
        _invalidate_tool_list()
    return get_settings()


def clear_overrides() -> None:
    _overrides.clear()
