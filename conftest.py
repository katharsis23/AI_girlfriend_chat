"""Root pytest configuration.

Ensures the repository root is importable so tests can use the
``src.ai_girlfriend`` package path consistently.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
