"""Bootstrap: wires worker, backends and the QML engine (spec §2, §10)."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterSingletonInstance
from PySide6.QtQuickControls2 import QQuickStyle

from src.ai_girlfriend.ui.backends import AsyncWorker, ChatBackend, SettingsBackend
from src.ai_girlfriend.ui.plugins import builtin_registry
from src.ai_girlfriend.ui.themes import ThemeController

QML_DIR = Path(__file__).resolve().parent / "qml"


def run(root=None, demo: bool = False) -> int:
    """`root` is the CompositionRoot: needs `.config.characters` and `.build_pipeline(character=...)`.

    With no ``root`` and no ``--demo``, the real ``CompositionRoot`` is built
    from ``config.json``.
    """
    if root is None:
        if demo:
            from src.ai_girlfriend.ui.demo import DemoRoot

            root = DemoRoot()
        else:
            from src.ai_girlfriend.composition_root import CompositionRoot
            from src.ai_girlfriend.config.config import config as app_config

            root = CompositionRoot(app_config)

    QQuickStyle.setStyle("Material")
    app = QGuiApplication(sys.argv)
    app.setApplicationName("Companion")

    worker = AsyncWorker()
    worker.start_and_wait()
    app.aboutToQuit.connect(worker.stop)

    character = root.config.characters[0]
    pipeline = root.build_pipeline(character=character)

    theme = ThemeController()
    chat = ChatBackend(worker, pipeline, character)
    settings = SettingsBackend(worker, root, chat, theme, character)

    qmlRegisterSingletonInstance(ThemeController, "App", 1, 0, "ThemeController", theme)

    engine = QQmlApplicationEngine()
    ctx = engine.rootContext()
    ctx.setContextProperty("chatBackend", chat)
    ctx.setContextProperty("settingsBackend", settings)
    registry = builtin_registry()
    registry.expose(engine)

    engine.load(QUrl.fromLocalFile(str(QML_DIR / "Main.qml")))
    if not engine.rootObjects():
        return 1
    return app.exec()
