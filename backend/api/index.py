import os
import sys
import traceback
from pathlib import Path

# Add backend directory to sys.path so app modules are discoverable
BACKEND_DIR = Path(__file__).resolve().parent.parent

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

try:
    from app.main import app
except Exception as e:
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    from fastapi.middleware.cors import CORSMiddleware

    err_trace = traceback.format_exc()
    app = FastAPI(title="Emergency Diagnostic App")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"])
    async def emergency_catch_all(path_name: str):
        return JSONResponse(
            status_code=500,
            content={
                "error": "FastAPI App Import Failed on Serverless Runtime",
                "exception": str(e),
                "traceback": err_trace,
                "sys_path": sys.path[:8],
                "cwd": os.getcwd()
            }
        )

__all__ = ["app"]
