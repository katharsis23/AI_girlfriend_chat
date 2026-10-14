"""Small filesystem helpers exposed to QML (image browser, task 3).

QML's own ``FileDialog`` needs a platform dialog implementation that is not
always present; a lightweight in-app browser built on top of these slots is
predictable everywhere. The backend is intentionally read-only: it lists
directories and image files and resolves a chosen path to a ``file://`` URL.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Property, QObject, Signal, Slot

# Extensions we treat as selectable images.
IMAGE_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".bmp",
    ".gif",
    ".tif",
    ".tiff",
    ".svg",
}


class FileSystemBackend(QObject):
    """Read-only filesystem navigation for the QML image picker."""

    cwdChanged = Signal()

    def __init__(self, start_dir: Path | None = None, parent=None):
        super().__init__(parent)
        self._cwd = (start_dir or Path.home()).expanduser()

    @Property(str, notify=cwdChanged)
    def cwd(self):
        return str(self._cwd)

    @Property(str, notify=cwdChanged)
    def home(self):
        return str(Path.home())

    @Slot(str, result=str)
    def parent(self, path: str) -> str:
        """Return the parent directory of ``path`` (clamped at the root)."""
        p = Path(path).expanduser()
        return str(p.parent if p.parent != p else p)

    @Slot(str, result="QVariantList")
    def listDir(self, path: str) -> list:
        """List sub-directories and image files of ``path``.

        Returns a list of ``{name, path, isDir, url}`` maps. Unreadable
        directories yield an empty list instead of raising.
        """
        p = Path(path).expanduser()
        try:
            entries = sorted(
                p.iterdir(),
                key=lambda e: (not e.is_dir(), e.name.lower()),
            )
        except OSError:
            return []

        result: list[dict] = []
        for entry in entries:
            if entry.name.startswith("."):
                continue
            try:
                is_dir = entry.is_dir()
            except OSError:
                continue
            if not is_dir and entry.suffix.lower() not in IMAGE_SUFFIXES:
                continue
            result.append(
                {
                    "name": entry.name,
                    "path": str(entry),
                    "isDir": is_dir,
                    "url": f"file://{entry}" if not is_dir else "",
                }
            )
        return result

    @Slot(str, result=bool)
    def setCwd(self, path: str) -> bool:
        """Change the current directory; returns ``True`` on success."""
        p = Path(path).expanduser()
        if p.is_dir():
            self._cwd = p
            self.cwdChanged.emit()
            return True
        return False


__all__ = ["IMAGE_SUFFIXES", "FileSystemBackend"]
