"""Qt widgets for the desktop adapter.

The window contains no prompt, SQL, or provider-selection logic: it only
collects input, calls the pipeline through the ``AsyncWorker`` bridge, and
renders the result (see spec, section 10).
"""

from pathlib import Path

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.ai_girlfriend.gf_pipeline import GfPipeline
from src.ai_girlfriend.ui_builder.async_worker import AsyncWorker


class ChatWindow(QWidget):
    """The main companion window: portrait, transcript, and input."""

    def __init__(self, pipeline: GfPipeline, worker: AsyncWorker):
        super().__init__()
        self.pipeline = pipeline
        self.worker = worker

        self.setWindowTitle(pipeline.gf_config.name)
        self.resize(720, 480)

        self.portrait = QLabel("No portrait")
        self.portrait.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.portrait.setMinimumSize(200, 200)

        self.transcript = QTextEdit()
        self.transcript.setReadOnly(True)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Type a message...")
        self.input.returnPressed.connect(self.send)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send)

        input_row = QHBoxLayout()
        input_row.addWidget(self.input)
        input_row.addWidget(self.send_button)

        text_column = QVBoxLayout()
        text_column.addWidget(self.transcript)
        text_column.addLayout(input_row)

        root = QHBoxLayout(self)
        root.addWidget(self.portrait)
        root.addLayout(text_column)

        self.worker.finished.connect(self._on_response)
        self.worker.failed.connect(self._on_error)

        # Show the greeting and the initial portrait.
        if pipeline.gf_config.greeting_message:
            self.transcript.append(
                f"<b>{pipeline.gf_config.name}:</b> "
                f"{pipeline.gf_config.greeting_message}"
            )
        self._update_portrait(pipeline.gf_config.initial_expression)

    @Slot()
    def send(self) -> None:
        """Read the input and submit a chat call to the background loop."""
        message = self.input.text().strip()
        if not message:
            return
        self.input.clear()
        self.transcript.append(f"<b>You:</b> {message}")
        self.send_button.setEnabled(False)
        self.worker.submit(self.pipeline.chat(message))

    @Slot(object)
    def _on_response(self, response) -> None:
        self.transcript.append(
            f"<b>{self.pipeline.gf_config.name}:</b> {response.text}"
        )
        self._update_portrait(response.expression)
        self.send_button.setEnabled(True)

    @Slot(object)
    def _on_error(self, exc: Exception) -> None:
        self.transcript.append(f"<i>Error: {exc}</i>")
        self.send_button.setEnabled(True)

    def _update_portrait(self, expression: str) -> None:
        try:
            path = self.pipeline.expression_manager.asset_path(expression)
        except Exception:
            self.portrait.setText(f"Missing asset: {expression}")
            return
        if isinstance(path, Path) and path.exists():
            self.portrait.setPixmap(QPixmap(str(path)))
        else:
            self.portrait.setText(f"[{expression}]")


__all__ = ["ChatWindow"]
