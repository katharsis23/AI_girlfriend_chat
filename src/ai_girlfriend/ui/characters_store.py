"""Persistence for user-defined characters (added/edited from the UI).

Built-in characters come from ``config.json``; characters created or edited in
the Settings UI are stored in a separate JSON file (``characters.json``) so the
app config stays untouched. A record mirrors the shape of ``CharacterInfo``:

    {
      "name": "...", "personality": "...", "greeting_message": "...",
      "initial_expression": "neutral",
      "photo_emoji_map": {"neutral": "/abs/path.png"}
    }

The store only validates structure; it never mutates ``CharacterInfo`` objects.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.ai_girlfriend.models.character import CharacterInfo


def default_characters_path() -> Path:
    """Location of the custom characters file (next to the app config)."""
    try:
        from src.ai_girlfriend.config.config import _CONFIG_JSON

        return _CONFIG_JSON.parent / "characters.json"
    except Exception:  # pragma: no cover - defensive fallback
        return Path.cwd() / "characters.json"


class CharacterStoreError(ValueError):
    """Raised when a character record is malformed."""


class CharacterStore:
    """Loads and saves custom characters from a JSON file."""

    def __init__(self, path: Path | None = None):
        self.path = Path(path) if path is not None else default_characters_path()

    def load(self) -> list[CharacterInfo]:
        """Return valid custom characters; unreadable files yield ``[]``."""
        if not self.path.is_file():
            return []
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        if not isinstance(raw, list):
            return []

        characters: list[CharacterInfo] = []
        for record in raw:
            try:
                characters.append(CharacterInfo.model_validate(record))
            except Exception:
                continue  # skip broken records, keep the app usable
        return characters

    def save(self, characters: list[CharacterInfo]) -> None:
        """Write the custom characters to disk (full replace)."""
        records = [c.model_dump(mode="json") for c in characters]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(records, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


__all__ = ["CharacterStore", "CharacterStoreError", "default_characters_path"]
