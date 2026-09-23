import os
import sys
import traceback
from pathlib import Path

# Add all candidate paths to sys.path
for base in [Path(__file__).resolve().parent, Path.cwd(), Path("/var/task"), Path("/var/task/backend")]:
    for candidate in [base, base.parent, base / "backend", base.parent / "backend"]:
        p_str = str(candidate.resolve())
        if candidate.exists() and p_str not in sys.path:
            sys.path.insert(0, p_str)

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

try:
    try:
        from app.main import app
    except ImportError:
        from backend.app.main import app
except Exception as e:
    err_trace = traceback.format_exc()
    app = FastAPI(title="QAgent Diagnostic")
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
                "error": "Failed to import FastAPI application",
                "exception": str(e),
                "traceback": err_trace,
                "sys_path": sys.path[:8],
                "cwd": os.getcwd()
            }
        )

__all__ = ["app"]
