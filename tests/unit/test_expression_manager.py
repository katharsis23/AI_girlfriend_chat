"""Unit tests for ``ExpressionManager`` and ``CharacterInfo`` path validation."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from src.ai_girlfriend.character.expression_manager import ExpressionManager
from src.ai_girlfriend.exc import InvalidExpressionError
from src.ai_girlfriend.models.character import CharacterInfo

pytestmark = pytest.mark.unit


def make_character(expressions=None, initial="neutral") -> CharacterInfo:
    return CharacterInfo(
        name="Aria",
        personality="You are Aria.",
        photo_emoji_map=expressions
        if expressions is not None
        else {"neutral": "neutral.png", "happy": "faces/happy.png"},
        initial_expression=initial,
    )


def test_resolve_returns_known_expression():
    manager = ExpressionManager(make_character())
    assert manager.resolve("happy") == "happy"


def test_resolve_falls_back_on_unknown_or_none():
    manager = ExpressionManager(make_character())
    assert manager.resolve("angry") == "neutral"
    assert manager.resolve(None) == "neutral"


def test_validate_raises_on_unknown():
    manager = ExpressionManager(make_character())
    with pytest.raises(InvalidExpressionError):
        manager.validate("angry")


def test_asset_path_is_relative_to_base_dir():
    manager = ExpressionManager(make_character(), base_dir=Path("/assets/aria"))
    assert manager.asset_path("happy") == Path("/assets/aria/faces/happy.png")


def test_character_config_allows_absolute_paths():
    # Users keep their photos outside the character directory, so absolute
    # paths (and ~ paths) must be accepted as-is.
    character = make_character(expressions={"neutral": "/home/user/photo.png"})
    assert character.expressions["neutral"] == "/home/user/photo.png"


def test_asset_path_returns_absolute_path_as_is():
    manager = ExpressionManager(
        make_character(expressions={"neutral": "/home/user/photo.png"}),
        base_dir=Path("/assets/aria"),
    )
    assert manager.asset_path("neutral") == Path("/home/user/photo.png")


def test_character_config_rejects_parent_traversal():
    with pytest.raises(ValidationError):
        make_character(expressions={"neutral": "../../secret.png"})


def test_asset_path_rejects_traversal_after_resolve():
    # A dictionary that somehow bypassed validation must still be caught.
    character = make_character(expressions={"neutral": "neutral.png"})
    character.photo_emoji_map["evil"] = "../../secret.png"
    manager = ExpressionManager(character, base_dir=Path("/assets"))

    with pytest.raises(InvalidExpressionError):
        manager.asset_path("evil")
