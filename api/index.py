import os
import sys
import traceback
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI(title="QAgent Diagnostic")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure paths
curr_dir = os.path.abspath(os.path.dirname(__file__))
parent_dir = os.path.abspath(os.path.join(curr_dir, ".."))
backend_dir = os.path.join(parent_dir, "backend")
for p in [curr_dir, parent_dir, backend_dir]:
    if os.path.exists(p) and p not in sys.path:
        sys.path.insert(0, p)

@app.get("/")
@app.get("/health")
@app.get("/api/health")
async def health_diag():
    diag = {
        "status": "online",
        "python_version": sys.version,
        "cwd": os.getcwd(),
        "sys_path": sys.path[:8],
        "dir_contents": os.listdir(".") if os.path.exists(".") else [],
        "modules": {}
    }
    
    modules_to_test = [
        "fastapi",
        "pydantic",
        "pydantic_settings",
        "sqlalchemy",
        "aiosqlite",
        "asyncpg",
        "jose",
        "app.core.config",
        "app.core.database",
        "app.core.security",
        "app.models.user",
        "app.models.academic",
        "app.models.paper",
        "app.models.resource",
        "app.api.auth",
        "app.api.courses",
        "app.services.rag.embeddings",
        "app.services.pdf_generator",
        "app.main"
    ]
    
    for mod in modules_to_test:
        try:
            __import__(mod)
            diag["modules"][mod] = "OK"
        except Exception as e:
            diag["modules"][mod] = f"FAILED: {e} -> {traceback.format_exc()}"
            
    return diag

__all__ = ["app"]
