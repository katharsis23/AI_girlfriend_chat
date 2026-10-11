"""Role-based Material 3 tokens (spec §5). Hex values are placeholders for the design pass."""

from __future__ import annotations

from PySide6.QtCore import Property, QObject, Signal, Slot

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
    """Holds the active theme; projected into QML by the `Theme` singleton."""

    themeChanged = Signal()

    def __init__(self, theme_id: str = DEFAULT_THEME, parent=None):
        super().__init__(parent)
        self._id = theme_id if theme_id in THEMES else DEFAULT_THEME

    @Property("QVariantMap", notify=themeChanged)
    def colors(self):
        return THEMES[self._id]["colors"]

    @Property(bool, notify=themeChanged)
    def isDark(self):
        return THEMES[self._id]["dark"]

    @Property(str, notify=themeChanged)
    def themeId(self):
        return self._id

    @Slot(str)
    def setTheme(self, theme_id: str) -> None:
        if theme_id in THEMES and theme_id != self._id:
            self._id = theme_id
            self.themeChanged.emit()
