"""Factory that creates the database provider configured in settings.

Called only from the composition root (see spec, section 7). The factory
returns a configured provider instance; it does not initialize the connection.
"""

from pathlib import Path

from src.ai_girlfriend.exc import ConfigError
from src.ai_girlfriend.models.database import IDatabaseStorage

DatabaseProviders = {
    "sqlite": "src.ai_girlfriend.database.sqlite_provider.SQLiteProvider"
}


class DatabaseFactory:
    """Creates a database provider instance based on the configured name."""

    def create(self, provider: str, url: str) -> IDatabaseStorage:
        if provider != "sqlite":
            raise ConfigError(
                f"Unsupported database provider: {provider!r}. "
                f"Supported: {sorted(DatabaseProviders)}"
            )

        from src.ai_girlfriend.database.sqlite_provider import SQLiteProvider

        return SQLiteProvider(db_path=self._normalize_url(url))

    @staticmethod
    def _normalize_url(url: str) -> Path:
        """Convert ``sqlite:///path`` (or a bare path) into a filesystem path."""
        prefix = "sqlite:///"
        if url.startswith(prefix):
            return Path(url[len(prefix) :])
        if url.startswith("sqlite://"):
            return Path(url[len("sqlite://") :])
        return Path(url)


__all__ = ["DatabaseFactory"]
