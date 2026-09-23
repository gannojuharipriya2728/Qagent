import os
import sys
from pathlib import Path

# Add backend directory to sys.path so app modules are discoverable
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Import the main FastAPI application instance
from app.main import app as fastapi_app

async def app(scope, receive, send):
    if scope.get("type") in ("http", "websocket"):
        path = scope.get("path", "")
        # Normalize any serverless file prefix injected by Vercel ASGI
        for prefix in ["/api/index.py", "/index.py", "/api/index", "/index"]:
            if path.startswith(prefix):
                path = path[len(prefix):]
                break
        
        if not path:
            path = "/"
        elif not path.startswith("/"):
            path = "/" + path
            
        scope["path"] = path
        scope["raw_path"] = path.encode("ascii")

    await fastapi_app(scope, receive, send)

__all__ = ["app"]
