"""Shared fixtures for unit tests."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture
def anyio_backend() -> str:
    """Force the asyncio backend for any async fixtures/markers."""
    return "asyncio"
