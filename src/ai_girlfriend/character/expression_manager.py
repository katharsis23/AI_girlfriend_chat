"""Stateless validator for character expressions.

The manager owns no mutable state: the active emotion belongs to the
conversation/client, not to a global singleton (see spec, "What changed").
It validates expression ids against the character dictionary so the model can
never resolve an arbitrary filesystem path (see spec, section 6.1).
"""

from pathlib import Path

from src.ai_girlfriend.exc import InvalidExpressionError
from src.ai_girlfriend.models.character import CharacterInfo


class ExpressionManager:
    """Validates expressions and resolves their asset paths."""

    def __init__(self, character: CharacterInfo, base_dir: Path | None = None):
        self.character = character
        self.base_dir = Path(base_dir) if base_dir is not None else None

    def resolve(self, expression_id: str | None) -> str:
        """Return a valid expression id.

        Resolution order:

        1. the requested id, if it is a known expression;
        2. ``initial_expression``, if it is a known expression;
        3. a ``default`` expression, if mapped;
        4. any expression that has an asset;
        5. ``initial_expression`` verbatim (or ``"default"``).

        This guarantees a deterministic, always-usable fallback even when the
        model hallucinates an unknown emotion or the character has an
        incomplete expression map (see spec, section 6.1).
        """
        expressions = self.character.expressions
        if expression_id is not None and expression_id in expressions:
            return expression_id
        initial = self.character.initial_expression
        if initial in expressions:
            return initial
        if "default" in expressions:
            return "default"
        if expressions:
            return next(iter(expressions))
        return initial or "default"

    def validate(self, expression_id: str) -> None:
        """Raise ``InvalidExpressionError`` if the id is not known."""
        if expression_id not in self.character.expressions:
            raise InvalidExpressionError(
                f"Unknown expression {expression_id!r} for character "
                f"{self.character.character_id!r}."
            )

    def asset_path(self, expression_id: str) -> Path:
        """Return the on-disk path of an expression asset (validated, safe).

        Absolute (or ``~``) paths are returned as-is; relative paths are
        resolved against ``base_dir`` and may not escape it with ``..``.
        """
        resolved_id = self.resolve(expression_id)
        asset = self.character.expressions.get(resolved_id)
        if asset is None:
            raise InvalidExpressionError(
                f"No asset mapped for expression {resolved_id!r}."
            )
        path = Path(asset).expanduser()
        if path.is_absolute():
            return path
        if ".." in path.parts:
            raise InvalidExpressionError(
                f"Expression {resolved_id!r} escapes the character directory."
            )
        return self.base_dir / path if self.base_dir is not None else path


__all__ = ["ExpressionManager"]
