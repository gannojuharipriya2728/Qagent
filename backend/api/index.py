import os
import sys
import urllib.parse
from pathlib import Path

# Add backend directory to sys.path so app modules are discoverable
BACKEND_DIR = Path(__file__).resolve().parent.parent

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Import the main FastAPI application instance
from app.main import app as fastapi_app

async def app(scope, receive, send):
    if scope.get("type") in ("http", "websocket"):
        path = scope.get("path", "")
        raw_query = scope.get("query_string", b"").decode("latin-1")
        
        # 1. Extract __path__ query param injected by Vercel rewrites
        if "__path__=" in raw_query:
            parsed_qs = urllib.parse.parse_qs(raw_query, keep_blank_values=True)
            if "__path__" in parsed_qs and parsed_qs["__path__"]:
                extracted = parsed_qs.pop("__path__")[0]
                if not extracted.startswith("/"):
                    extracted = "/" + extracted
                path = extracted
                clean_query = urllib.parse.urlencode(parsed_qs, doseq=True)
                scope["query_string"] = clean_query.encode("latin-1")
        
        # 2. Check headers if path is still a serverless filename
        if path in ["", "/", "/api/index.py", "/api/index", "/index.py", "/index"]:
            headers = dict(scope.get("headers", []))
            for h in [b"x-forwarded-uri", b"x-matched-path", b"x-vercel-matched-path"]:
                val = headers.get(h, b"").decode("latin-1")
                if val and val not in ["/api/index.py", "/index.py", "/api/index", "/index", "/"]:
                    path = val.split("?")[0]
                    break

        # 3. Strip any serverless file prefix
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
