import os
import sys
from pathlib import Path

# Add backend directory to sys.path so app modules are discoverable
BACKEND_DIR = Path(__file__).resolve().parent.parent

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Import the main FastAPI application instance directly
from app.main import app

__all__ = ["app"]
