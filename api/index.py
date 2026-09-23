import os
import sys
from pathlib import Path

# Add all candidate paths to sys.path so 'app' and 'backend' are discoverable
curr_dir = Path(__file__).resolve().parent
candidates = [
    curr_dir,
    curr_dir.parent,
    curr_dir.parent / "backend",
    curr_dir.parent.parent,
    curr_dir.parent.parent / "backend",
]

for p in candidates:
    if p.exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

try:
    from app.main import app
except ImportError:
    from backend.app.main import app

__all__ = ["app"]
