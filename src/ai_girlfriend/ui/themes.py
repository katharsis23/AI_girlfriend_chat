"""Role-based Material 3 tokens (spec §5). Hex values are placeholders for the design pass."""

from __future__ import annotations

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
    "outline",
    "error",
    "onError",
    "userBubble",
    "onUserBubble",
    "assistantBubble",
    "onAssistantBubble",
]

THEMES: dict[str, dict] = {
    "rose": {
        "name": "Rose",
        "dark": True,
        "colors": {
            "background": "#1E1418",
            "surface": "#2A1D23",
            "surfaceVariant": "#3B2A32",
            "primary": "#FFB1C8",
            "onPrimary": "#5E1133",
            "secondary": "#E3BDC6",
            "tertiary": "#EFBD94",
            "onSurface": "#F2DEE2",
            "onSurfaceVariant": "#D6C2C7",
            "outline": "#9F8C91",
            "error": "#FFB4AB",
            "onError": "#690005",
            "userBubble": "#7B2D4C",
            "onUserBubble": "#FFD9E3",
            "assistantBubble": "#3B2A32",
            "onAssistantBubble": "#F2DEE2",
        },
    },
    "mint": {
        "name": "Mint",
        "dark": False,
        "colors": {
            "background": "#F4FBF7",
            "surface": "#FFFFFF",
            "surfaceVariant": "#DBE5DE",
            "primary": "#006C4C",
            "onPrimary": "#FFFFFF",
            "secondary": "#4C6358",
            "tertiary": "#3D6373",
            "onSurface": "#171D1A",
            "onSurfaceVariant": "#404943",
            "outline": "#707973",
            "error": "#BA1A1A",
            "onError": "#FFFFFF",
            "userBubble": "#9CF2CB",
            "onUserBubble": "#002114",
            "assistantBubble": "#E3EBE5",
            "onAssistantBubble": "#171D1A",
        },
    },
    "midnight": {
        "name": "Midnight",
        "dark": True,
        "colors": {
            "background": "#000000",
            "surface": "#0D1117",
            "surfaceVariant": "#1B2230",
            "primary": "#A8C8FF",
            "onPrimary": "#00315F",
            "secondary": "#BCC7DC",
            "tertiary": "#DABCE2",
            "onSurface": "#FFFFFF",
            "onSurfaceVariant": "#C4C6D0",
            "outline": "#8E9099",
            "error": "#FFB4AB",
            "onError": "#690005",
            "userBubble": "#1D4ED8",
            "onUserBubble": "#FFFFFF",
            "assistantBubble": "#1B2230",
            "onAssistantBubble": "#FFFFFF",
        },
    },
}
DEFAULT_THEME = "rose"


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
        return self._themes[self._id]["colors"]

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
