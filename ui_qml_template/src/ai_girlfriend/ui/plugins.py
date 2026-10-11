"""Declared Qt modules and QML plugins (spec §10.2–10.4)."""

from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from typing import Any

QT_MODULES = (
    "QtCore",
    "QtGui",
    "QtQml",
    "QtQuick",
    "QtQuickControls2",
    "QtQuickLayouts",
)
QT_OPTIONAL_MODULES = ("QtMultimedia", "QtSvg")
QML_PLUGINS = (
    "QtQuick",
    "QtQuick.Controls",
    "QtQuick.Layouts",
    "QtQuick.Window",
    "QtQml",
)


def check_qt_modules() -> dict[str, bool]:
    """Import-verify every declared PySide6 module."""
    result: dict[str, bool] = {}
    for name in (*QT_MODULES, *QT_OPTIONAL_MODULES):
        try:
            importlib.import_module(f"PySide6.{name}")
            result[name] = True
        except ImportError:
            result[name] = False
    return result


@dataclass
class UiPlugin:
    name: str
    qml_component: str
    backend: Any = None


@dataclass
class UiPluginRegistry:
    plugins: dict[str, UiPlugin] = field(default_factory=dict)

    def register(self, plugin: UiPlugin) -> None:
        self.plugins[plugin.name] = plugin

    def expose(self, engine) -> None:
        """Expose each plugin's Python backend to QML under the plugin name."""
        for p in self.plugins.values():
            if p.backend is not None:
                engine.rootContext().setContextProperty(p.name, p.backend)


def builtin_registry() -> UiPluginRegistry:
    reg = UiPluginRegistry()
    for name, comp in (
        ("portrait", "Portrait.qml"),
        ("chat", "ChatView.qml"),
        ("theme", "ThemePicker.qml"),
    ):
        reg.register(UiPlugin(name, comp))
    return reg
