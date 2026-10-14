"""Role-based Material 3 tokens (spec §5).

Every theme — built-in or custom — is a mapping with three keys::

    {
        "name":   "Human readable name",
        "dark":   True | False,               # drives Material.theme
        "colors": {<token>: "#RRGGBB", ...},  # one entry per REQUIRED_TOKENS
    }

The ``colors`` mapping must use the *Material 3 role names* (``background``,
``surfaceVariant``, ``primary``, ``onPrimary``, ``onSurface`` …) because that is
what :mod:`Theme.qml` binds to and what ``SettingsBackend.themeInfo`` reads.
Historically the built-in themes used ad-hoc keys (``bg``, ``accent`` …) while
QML looked up the M3 role names, so every role resolved to ``undefined`` — which
QML paints as black. The tokens below are the single source of truth and the
built-ins are authored against them directly.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Property, QObject, Signal, Slot

# The full set of color roles every theme (built-in or custom) must define.
REQUIRED_TOKENS = [
    "background",
    "surface",
    "surfaceVariant",
    "primary",
    "onPrimary",
    "secondary",
    "tertiary",
    "onSurface",
    "onSurfaceVariant",
    "text",
    "outline",
    "error",
    "onError",
    "userBubble",
    "onUserBubble",
    "assistantBubble",
    "onAssistantBubble",
]

# Tokens added after a theme may have been saved. A missing token is filled
# from this sibling instead of invalidating the whole theme (see themes_store).
OPTIONAL_TOKEN_DEFAULTS = {"text": "onSurface"}


def _theme(name: str, dark: bool, colors: dict[str, str]) -> dict[str, Any]:
    """Build a fully-populated theme record from a partial color mapping.

    Missing required tokens are backfilled from sensible siblings so a single
    omission never leaves a role ``undefined`` (which QML renders as black).
    """
    resolved = dict(colors)
    fallback = {
        "background": resolved.get("surface", "#101010"),
        "surface": resolved.get("background", "#181818"),
        "surfaceVariant": resolved.get("surface", "#222222"),
        "primary": resolved.get("secondary", "#7C4DFF"),
        "onPrimary": "#FFFFFF",
        "secondary": resolved.get("primary", "#9A7BFF"),
        "tertiary": resolved.get("secondary", "#FF7BAC"),
        "onSurface": resolved.get("text", "#F5F5F5"),
        "onSurfaceVariant": resolved.get("text", "#C4C4C4"),
        "text": resolved.get("onSurface", "#F5F5F5"),
        "outline": resolved.get("surfaceVariant", "#4A4A4A"),
        "error": "#F07178",
        "onError": "#FFFFFF",
        "userBubble": resolved.get("primary", "#333355"),
        "onUserBubble": resolved.get("onPrimary", "#FFFFFF"),
        "assistantBubble": resolved.get("surfaceVariant", "#222222"),
        "onAssistantBubble": resolved.get("onSurface", "#F5F5F5"),
    }
    for token in REQUIRED_TOKENS:
        if not resolved.get(token):
            resolved[token] = fallback[token]
    return {"name": name, "dark": dark, "colors": resolved}


# Built-in themes, authored directly against the M3 role tokens above.
THEMES: dict[str, Any] = {
    "crimson_cathedral": _theme(
        "Crimson Cathedral",
        True,
        {
            "background": "#100B10",
            "surface": "#25151E",
            "surfaceVariant": "#351D2A",
            "primary": "#C54B70",
            "onPrimary": "#FFFFFF",
            "secondary": "#E16B8D",
            "tertiary": "#FFB4A8",
            "onSurface": "#F2E8EE",
            "onSurfaceVariant": "#BBA8B5",
            "text": "#F2E8EE",
            "outline": "#513043",
            "error": "#F07178",
            "onError": "#FFFFFF",
            "userBubble": "#492033",
            "onUserBubble": "#F2E8EE",
            "assistantBubble": "#20151F",
            "onAssistantBubble": "#F2E8EE",
        },
    ),
    "obsidian_protocol": _theme(
        "Obsidian Protocol",
        True,
        {
            "background": "#0B0D10",
            "surface": "#171B21",
            "surfaceVariant": "#222832",
            "primary": "#9AAFC5",
            "onPrimary": "#10151C",
            "secondary": "#C3D2E2",
            "tertiary": "#8FB8D8",
            "onSurface": "#E5EAF0",
            "onSurfaceVariant": "#9BA7B5",
            "text": "#E5EAF0",
            "outline": "#343C48",
            "error": "#F07178",
            "onError": "#10151C",
            "userBubble": "#293441",
            "onUserBubble": "#E5EAF0",
            "assistantBubble": "#15191F",
            "onAssistantBubble": "#E5EAF0",
        },
    ),
    "ghost_terminal": _theme(
        "Ghost Terminal",
        True,
        {
            "background": "#050806",
            "surface": "#101A13",
            "surfaceVariant": "#17251B",
            "primary": "#58FF91",
            "onPrimary": "#00120A",
            "secondary": "#9AFFB8",
            "tertiary": "#E8D66D",
            "onSurface": "#D8FFE2",
            "onSurfaceVariant": "#83B895",
            "text": "#D8FFE2",
            "outline": "#284632",
            "error": "#FF7474",
            "onError": "#2A0000",
            "userBubble": "#193523",
            "onUserBubble": "#D8FFE2",
            "assistantBubble": "#0B120D",
            "onAssistantBubble": "#D8FFE2",
        },
    ),
    "seaside_morning": _theme(
        "Seaside Morning",
        False,
        {
            "background": "#F4F7FB",
            "surface": "#FFFFFF",
            "surfaceVariant": "#E4EBF3",
            "primary": "#1E6FB8",
            "onPrimary": "#FFFFFF",
            "secondary": "#3F8FCB",
            "tertiary": "#5BA8C4",
            "onSurface": "#1A2530",
            "onSurfaceVariant": "#5A6B7B",
            "text": "#1A2530",
            "outline": "#B8C4D2",
            "error": "#C0392B",
            "onError": "#FFFFFF",
            "userBubble": "#D6E8FA",
            "onUserBubble": "#12314F",
            "assistantBubble": "#EAEFF5",
            "onAssistantBubble": "#1A2530",
        },
    ),
    "blush": _theme(
        "Blush",
        False,
        {
            "background": "#FBF5F7",
            "surface": "#FFFFFF",
            "surfaceVariant": "#F3E1E8",
            "primary": "#B83B6A",
            "onPrimary": "#FFFFFF",
            "secondary": "#D96C94",
            "tertiary": "#C98A5B",
            "onSurface": "#3A1F29",
            "onSurfaceVariant": "#7A5A66",
            "text": "#3A1F29",
            "outline": "#D8B9C4",
            "error": "#C0392B",
            "onError": "#FFFFFF",
            "userBubble": "#F8D7E2",
            "onUserBubble": "#4A1E2E",
            "assistantBubble": "#F1EAEE",
            "onAssistantBubble": "#3A1F29",
        },
    ),
}
DEFAULT_THEME = "crimson_cathedral"


class ThemeController(QObject):
    """Holds the active theme and the registry of available themes.

    Built-in themes come from :data:`THEMES`; user-defined themes are merged on
    top at construction time and persisted through an optional ``ThemeStore``.
    """

    themeChanged = Signal()
    themesChanged = Signal()

    def __init__(self, theme_id: str = DEFAULT_THEME, store=None, parent=None):
        super().__init__(parent)
        self._store = store
        self._themes: dict[str, dict] = dict(THEMES)
        if self._store is not None:
            self._themes.update(self._store.load())
        self._id = theme_id if theme_id in self._themes else DEFAULT_THEME

    @property
    def themes(self) -> dict[str, dict]:
        """All available themes (built-in + custom)."""
        return self._themes

    @property
    def theme_id(self) -> str:
        return self._id

    @Property("QVariantMap", notify=themeChanged)
    def colors(self):
        """The active theme's colors, guaranteed to contain every required role.

        Older/custom themes may predate a token (e.g. ``text``); we backfill it
        from :data:`OPTIONAL_TOKEN_DEFAULTS` so QML never reads ``undefined``
        for a color role (which would fall back to the default black text).
        """
        return self._resolved_colors(self._id)

    def _resolved_colors(self, theme_id: str) -> dict[str, str]:
        colors = dict(self._themes[theme_id]["colors"])
        for token, fallback in OPTIONAL_TOKEN_DEFAULTS.items():
            if colors.get(token) is None:
                colors[token] = colors.get(fallback, colors.get("onSurface", "#000000"))
        return colors

    @Property(bool, notify=themeChanged)
    def isDark(self):
        return self._themes[self._id]["dark"]

    @Property(str, notify=themeChanged)
    def themeId(self):
        return self._id

    @Slot(str)
    def setTheme(self, theme_id: str) -> None:
        if theme_id in self._themes and theme_id != self._id:
            self._id = theme_id
            self.themeChanged.emit()

    def resolved_colors(self, theme_id: str) -> dict[str, str]:
        """Public helper: colors for ``theme_id`` with optional tokens filled."""
        if theme_id not in self._themes:
            return {}
        return self._resolved_colors(theme_id)

    @Slot(str, str, bool, "QVariantMap", result=str)
    def saveCustomTheme(self, theme_id: str, name: str, dark: bool, colors) -> str:
        """Create or update a custom theme; return the id, or '' on error."""
        from src.ai_girlfriend.ui.themes_store import ThemeStore, ThemeStoreError

        if theme_id in THEMES:
            return ""  # never overwrite a built-in theme
        try:
            normalized = ThemeStore.validate(theme_id, name, dict(colors))
        except (ThemeStoreError, TypeError, ValueError):
            return ""
        self._themes[theme_id] = {
            "name": normalized["name"],
            "dark": bool(dark),
            "colors": normalized["colors"],
            "custom": True,
        }
        self._persist()
        self.themesChanged.emit()
        self.setTheme(theme_id)
        return theme_id

    @Slot(str, result=bool)
    def deleteCustomTheme(self, theme_id: str) -> bool:
        """Delete a custom theme; returns ``True`` if it existed."""
        theme = self._themes.get(theme_id)
        if theme is None or not theme.get("custom"):
            return False
        del self._themes[theme_id]
        if self._id == theme_id:
            self._id = DEFAULT_THEME
            self.themeChanged.emit()
        self._persist()
        self.themesChanged.emit()
        return True

    def _persist(self) -> None:
        if self._store is not None:
            self._store.save(self._themes)
