"""Entry point: ``python -m src.ai_girlfriend.ui [--demo]``.

``--demo`` runs an offline fake core so the UI can be exercised without the real
pipeline. Without it, the real ``CompositionRoot`` is built from ``config.json``.
"""

import sys

from src.ai_girlfriend.ui.app import run

if __name__ == "__main__":
    sys.exit(run(demo="--demo" in sys.argv))
