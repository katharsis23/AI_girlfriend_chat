"""Desktop QML adapter (Material 3). See docs/ui_spec.md.

The UI imports the core; the core never imports the UI. QML documents live in
``ui/qml`` and are shipped inside the package (see ``pyproject.toml``).

PySide6 is an *optional* dependency (the ``qt`` extra), so this package exposes
:func:`run` lazily: importing ``src.ai_girlfriend.ui`` must not fail on machines
without Qt installed.
"""

from pathlib import Path
from typing import TYPE_CHECKING

QML_DIR: Path = Path(__file__).resolve().parent / "qml"

if TYPE_CHECKING:
    from src.ai_girlfriend.ui.app import run as run

__all__ = ["QML_DIR", "run"]


def __getattr__(name: str):
    """Lazily resolve :func:`run` so PySide6 is imported only on demand."""
    if name == "run":
        from src.ai_girlfriend.ui.app import run

        return run
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
