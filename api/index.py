import os
import sys
from pathlib import Path

# Add backend directory to sys.path so app modules are discoverable
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"

for p in [str(BACKEND_DIR), str(ROOT_DIR), str(Path(__file__).resolve().parent)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from app.main import app

__all__ = ["app"]
