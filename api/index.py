import os
import sys
import traceback
from pathlib import Path

# Add backend directory to sys.path so app modules are discoverable
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"

for p in [str(BACKEND_DIR), str(ROOT_DIR), str(Path(__file__).resolve().parent)]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from app.main import app
except Exception as e:
    try:
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse
        from fastapi.middleware.cors import CORSMiddleware

        err_trace = traceback.format_exc()
        app = FastAPI(title="Diagnostic Fallback")
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        @app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"])
        async def diag_catch_all(path_name: str = ""):
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Failed to import app.main",
                    "exception": str(e),
                    "traceback": err_trace
                }
            )
    except Exception:
        def app(environ, start_response):
            status = '500 Internal Server Error'
            response_headers = [('Content-type', 'text/plain; charset=utf-8')]
            start_response(status, response_headers)
            return [f"Bootstrap Error:\n{traceback.format_exc()}".encode("utf-8")]

__all__ = ["app"]
