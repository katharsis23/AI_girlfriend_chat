"""Domain error hierarchy.

Providers raise these typed errors instead of raw library exceptions; adapters
map them to HTTP statuses or UI messages (see spec, section 6.5).
"""


class CompanionError(Exception):
    """Base class for all domain errors raised by the companion core."""


class ConfigError(CompanionError):
    """Raised when configuration is missing, malformed, or inconsistent."""


class ProviderError(CompanionError):
    """Raised when an external provider (LLM, ...) fails."""


class GenerationTimeoutError(ProviderError):
    """Raised when a generation call exceeds the configured timeout."""


class StorageError(CompanionError):
    """Raised when a database operation fails."""


class InvalidExpressionError(CompanionError):
    """Raised when an expression id is not part of the character's dictionary."""


__all__ = [
    "CompanionError",
    "ConfigError",
    "GenerationTimeoutError",
    "InvalidExpressionError",
    "ProviderError",
    "StorageError",
]
