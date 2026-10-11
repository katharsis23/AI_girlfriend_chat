"""Qt desktop adapter (outside the core).

``UIBuilder`` assembles the window and the async bridge; ``QtDesktopAdapter``
owns the application lifecycle. Qt imports the core, never the other way round
(see spec, sections 2/10).
"""

import sys

from PySide6.QtWidgets import QApplication

from src.ai_girlfriend.config.config import Config
from src.ai_girlfriend.gf_pipeline import GfPipeline
from src.ai_girlfriend.ui_builder.async_worker import AsyncWorker
from src.ai_girlfriend.ui_builder.chat_window import ChatWindow


class UIBuilder:
    """Builds the Qt application and wires it to a ready ``GfPipeline``."""

    def build(
        self, pipeline: GfPipeline, config: Config, argv: list[str] | None = None
    ) -> QApplication:
        app = QApplication(argv if argv is not None else sys.argv)

        worker = AsyncWorker()
        worker.start()

        window = ChatWindow(pipeline, worker)
        window.show()

        # Keep strong references so they are not garbage-collected.
        app._companion_worker = worker  # type: ignore[attr-defined]
        app._companion_window = window  # type: ignore[attr-defined]
        return app


class QtDesktopAdapter:
    """Entry point that runs the companion desktop application."""

    def __init__(self, pipeline: GfPipeline, config: Config):
        self.pipeline = pipeline
        self.config = config
        self._worker: AsyncWorker | None = None

    def run(self) -> None:
        """Initialize the pipeline and enter the Qt event loop."""
        import asyncio

        asyncio.run(self.pipeline.init())

        app = UIBuilder().build(self.pipeline, self.config)
        self._worker = app._companion_worker  # type: ignore[attr-defined]
        try:
            app.exec()
        finally:
            if self._worker is not None:
                self._worker.stop()
            asyncio.run(self.pipeline.close())


__all__ = ["QtDesktopAdapter", "UIBuilder"]
