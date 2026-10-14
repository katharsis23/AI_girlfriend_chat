"""Persistence for user-defined color themes.

Built-in themes live in :mod:`themes`. Custom themes are stored in a separate
JSON file (``themes.json``) so the app config stays untouched and themes can be
shared/backed up on their own. The file is a list of records:

    [
      {"id": "my-theme", "name": "My theme", "dark": true,
       "colors": {"background": "#...", ...}}
    ]

Every theme (built-in or custom) must provide the full set of color tokens; the
:data:`~themes.REQUIRED_TOKENS` list is the source of truth for validation.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from src.ai_girlfriend.ui.themes import (
    DEFAULT_THEME,
    OPTIONAL_TOKEN_DEFAULTS,
    REQUIRED_TOKENS,
    THEMES,
)

_THEME_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_HEX_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")


def default_themes_path() -> Path:
    """Location of the custom themes file (next to the app config)."""
    # Imported lazily to avoid a hard dependency on the config module here.
    try:
        from src.ai_girlfriend.config.config import _CONFIG_JSON

        return _CONFIG_JSON.parent / "themes.json"
    except Exception:  # pragma: no cover - defensive fallback
        return Path.cwd() / "themes.json"


class ThemeStoreError(ValueError):
    """Raised when a custom theme record is malformed."""


class ThemeStore:
    """Loads and saves custom themes from a JSON file."""

    def __init__(self, path: Path | None = None):
        self.path = Path(path) if path is not None else default_themes_path()

    # -- validation ------------------------------------------------------
    @classmethod
    def validate(cls, theme_id: str, name: str, colors: dict) -> dict:
        """Validate and normalize a theme record; raise ``ThemeStoreError``."""
        if not isinstance(theme_id, str) or not _THEME_ID_RE.match(theme_id):
            raise ThemeStoreError(
                "Theme id must be lowercase letters, digits and dashes."
            )
        if theme_id in THEMES:
            raise ThemeStoreError(f"{theme_id!r} clashes with a built-in theme.")
        if not isinstance(name, str) or not name.strip():
            raise ThemeStoreError("Theme name must not be empty.")
        if not isinstance(colors, dict):
            raise ThemeStoreError("Theme colors must be an object.")

        normalized: dict[str, str] = {}
        for token in REQUIRED_TOKENS:
            value = colors.get(token)
            # A token added after a theme was saved may be missing: fill it from
            # its sibling default instead of rejecting the whole theme.
            if value is None and token in OPTIONAL_TOKEN_DEFAULTS:
                value = colors.get(OPTIONAL_TOKEN_DEFAULTS[token])
            if not isinstance(value, str) or not _HEX_RE.match(value):
                raise ThemeStoreError(f"Invalid color for {token!r}: {value!r}.")
            normalized[token] = value
        return {"name": name.strip(), "colors": normalized}

    # -- I/O -------------------------------------------------------------
    def load(self) -> dict[str, dict]:
        """Return ``{theme_id: theme_dict}`` for all valid custom themes.

        A missing or unreadable file yields an empty dict: custom themes are an
        enhancement, never a hard requirement to start the app.
        """
        if not self.path.is_file():
            return {}
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        if not isinstance(raw, list):
            return {}

        themes: dict[str, dict] = {}
        for record in raw:
            if not isinstance(record, dict):
                continue
            theme_id = record.get("id")
            try:
                normalized = self.validate(
                    theme_id, record.get("name", ""), record.get("colors", {})
                )
            except ThemeStoreError:
                continue  # skip broken records instead of crashing the app
            themes[theme_id] = {
                "name": normalized["name"],
                "dark": bool(record.get("dark", False)),
                "colors": normalized["colors"],
                "custom": True,
            }
        return themes

    def save(self, themes: dict[str, dict]) -> None:
        """Write all custom themes (the ones flagged ``custom``) to disk."""
        records = [
            {
                "id": theme_id,
                "name": theme["name"],
                "dark": theme.get("dark", False),
                "colors": theme["colors"],
            }
            for theme_id, theme in themes.items()
            if theme.get("custom")
        ]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(records, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


__all__ = ["DEFAULT_THEME", "ThemeStore", "ThemeStoreError", "default_themes_path"]
