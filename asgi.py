"""
Repository-root ASGI entrypoint for the QAgent FastAPI service.

The application package lives in ``backend/`` and imports itself absolutely
(``from app.core.config import settings``), so ``backend/`` has to be on
``sys.path``. Running ``uvicorn backend.app.main:app`` from the repository root
therefore fails with ``ModuleNotFoundError: app``. This module puts the
directory on the path first, which makes both of these start commands valid:

    uvicorn asgi:app --host 0.0.0.0 --port $PORT          # from the repo root
    uvicorn app.main:app --host 0.0.0.0 --port $PORT      # from backend/
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app  # noqa: E402  (path setup must run first)

__all__ = ["app"]
