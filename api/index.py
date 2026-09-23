import os
import sys
import traceback
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
    try:
        from app.main import app
    except ImportError:
        from backend.app.main import app
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
