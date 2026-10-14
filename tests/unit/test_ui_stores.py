"""Unit tests for the custom theme and character stores + ThemeController."""

import json

import pytest

pytest.importorskip("PySide6")

from src.ai_girlfriend.models.character import CharacterInfo
from src.ai_girlfriend.ui.characters_store import CharacterStore
from src.ai_girlfriend.ui.themes import REQUIRED_TOKENS, THEMES, ThemeController
from src.ai_girlfriend.ui.themes_store import ThemeStore, ThemeStoreError

pytestmark = pytest.mark.unit


def _valid_colors() -> dict:
    return {token: "#123456" for token in REQUIRED_TOKENS}


# --- ThemeStore --------------------------------------------------------
def test_theme_store_roundtrip(tmp_path):
    store = ThemeStore(tmp_path / "themes.json")
    themes = {
        # Not flagged ``custom`` -> treated like a built-in, never persisted.
        "rose": {"name": "Rose", "dark": True, "colors": _valid_colors()},
        "custom-x": {
            "name": "Custom X",
            "dark": False,
            "colors": _valid_colors(),
            "custom": True,
        },
    }
    store.save(themes)

    loaded = store.load()
    assert set(loaded) == {"custom-x"}
    assert loaded["custom-x"]["name"] == "Custom X"
    assert loaded["custom-x"]["custom"] is True


def test_theme_store_skips_invalid_records(tmp_path):
    path = tmp_path / "themes.json"
    path.write_text(
        json.dumps(
            [
                {"id": "ok", "name": "Ok", "colors": _valid_colors()},
                {"id": "bad id", "name": "Bad", "colors": _valid_colors()},
                {"id": "bad-color", "name": "Bad", "colors": {"primary": "red"}},
            ]
        ),
        encoding="utf-8",
    )
    assert set(ThemeStore(path).load()) == {"ok"}


def test_theme_store_missing_file_is_empty(tmp_path):
    assert ThemeStore(tmp_path / "nope.json").load() == {}


def test_theme_store_validate_rejects_builtin_id():
    builtin_id = next(iter(THEMES))
    with pytest.raises(ThemeStoreError):
        ThemeStore.validate(builtin_id, "Copy of builtin", _valid_colors())


# --- ThemeController ---------------------------------------------------
def test_theme_controller_saves_and_deletes_custom(tmp_path):
    store = ThemeStore(tmp_path / "themes.json")
    controller = ThemeController(store=store)

    saved = controller.saveCustomTheme("sunset", "Sunset", True, _valid_colors())
    assert saved == "sunset"
    assert controller.theme_id == "sunset"
    assert "sunset" in controller.themes

    # Persisted across a fresh controller.
    reloaded = ThemeController(store=store)
    assert "sunset" in reloaded.themes

    assert controller.deleteCustomTheme("sunset") is True
    assert "sunset" not in controller.themes
    assert controller.theme_id != "sunset"


def test_theme_controller_refuses_to_overwrite_builtin():
    controller = ThemeController()
    builtin_id = next(iter(THEMES))
    assert (
        controller.saveCustomTheme(builtin_id, "Copy of builtin", True, _valid_colors())
        == ""
    )
    assert controller.themes[builtin_id]["colors"] == THEMES[builtin_id]["colors"]


# --- CharacterStore ----------------------------------------------------
def test_character_store_roundtrip(tmp_path):
    store = CharacterStore(tmp_path / "characters.json")
    characters = [
        CharacterInfo(name="Nova", personality="Energetic", greeting_message="Hey!"),
    ]
    store.save(characters)

    loaded = store.load()
    assert len(loaded) == 1
    assert loaded[0].name == "Nova"
    assert loaded[0].character_id == "nova"


def test_character_store_skips_invalid(tmp_path):
    path = tmp_path / "characters.json"
    path.write_text(
        json.dumps(
            [
                {"name": "Good", "personality": "ok"},
                {"personality": "no name"},  # invalid: name required
            ]
        ),
        encoding="utf-8",
    )
    loaded = CharacterStore(path).load()
    assert [c.name for c in loaded] == ["Good"]
