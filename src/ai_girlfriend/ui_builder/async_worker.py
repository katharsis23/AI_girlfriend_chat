"""Deprecated location of ``AsyncWorker``.

The worker lives in :mod:`src.ai_girlfriend.ui.backends`. This module is kept
as a thin re-export so existing imports keep working.
"""

from src.ai_girlfriend.ui.backends import AsyncWorker

__all__ = ["AsyncWorker"]
