import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base, AsyncSessionLocal
from app.core.seed import seed_database
from app.api.auth import router as auth_router
from app.api.courses import router as courses_router
from app.api.resources import router as resources_router
from app.api.generate import router as generate_router
from app.api.papers import router as papers_router
from app.api.admin import router as admin_router
from app.api.ai import router as ai_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # In development/test environments, auto-create tables if missing.
    # In production, schema migrations are explicitly managed via Alembic.
    if settings.ENVIRONMENT.lower() != "production":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    # Seed demo academic data only if explicitly enabled in non-production
    if settings.SEED_DEMO_DATA and settings.ENVIRONMENT.lower() != "production":
        async with AsyncSessionLocal() as session:
            await seed_database(session)

    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Agentic AI-Based Question Generator using Retrieval-Augmented Generation (RAG)",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)

# Mount Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(courses_router, prefix=settings.API_V1_STR)
app.include_router(resources_router, prefix=settings.API_V1_STR)
app.include_router(generate_router, prefix=settings.API_V1_STR)
app.include_router(papers_router, prefix=settings.API_V1_STR)
app.include_router(admin_router, prefix=settings.API_V1_STR)
app.include_router(ai_router, prefix=settings.API_V1_STR)

import logging

logger = logging.getLogger("qagent.main")

@app.get("/", tags=["Health"])
async def root_status():
    """
    Root entrypoint for Vercel deployment verification.
    """
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "docs_url": "/docs",
        "health_url": "/health"
    }

@app.get("/health", tags=["Health"])
@app.get(f"{settings.API_V1_STR}/health", tags=["Health"])
async def health_check():
    db_status = "connected"
    db_error_type = None
    try:
        from sqlalchemy import text
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception as e:
        db_status = "unreachable"
        db_error_type = e.__class__.__name__
        sanitized_msg = str(e).splitlines()[0] if str(e) else "Connection failed"
        # Sanitize against any accidental secret leakage in error string
        for secret in [settings.SECRET_KEY, getattr(settings, "NVIDIA_API_KEY", ""), getattr(settings, "OPENROUTER_API_KEY", "")]:
            if secret and len(secret) > 4:
                sanitized_msg = sanitized_msg.replace(secret, "[REDACTED]")
        logger.error(f"Database health check failed ({db_error_type}): {sanitized_msg}")

    storage_status = "connected"
    try:
        from app.services.storage import get_storage_service
        svc = get_storage_service()
        if hasattr(svc, "base_dir"):
            storage_status = "connected" if os.path.exists(svc.base_dir) else "missing_dir"
        else:
            storage_status = "configured"
    except Exception:
        storage_status = "error"

    active_model = settings.NVIDIA_MODEL if settings.LLM_PROVIDER == "nvidia" else settings.OPENROUTER_MODEL

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "database": db_status,
        "database_driver": settings.SAFE_DATABASE_INFO.get("driver"),
        "storage_provider": settings.STORAGE_PROVIDER,
        "storage": storage_status,
        "llm_provider": settings.LLM_PROVIDER,
        "llm_model": active_model
    }

@app.get("/health/db", tags=["Health"])
@app.get(f"{settings.API_V1_STR}/health/db", tags=["Health"])
async def health_db_check():
    """
    Safe diagnostic endpoint for database connection status and dialect info.
    Never returns secrets, passwords, or connection credentials.
    """
    db_info = settings.SAFE_DATABASE_INFO
    status = "connected"
    error_type = None
    error_detail = None

    try:
        from sqlalchemy import text
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception as e:
        status = "unreachable"
        error_type = e.__class__.__name__
        raw_msg = str(e).splitlines()[0] if str(e) else "Connection error"
        # Strip any credential strings
        error_detail = raw_msg
        for secret in [settings.SECRET_KEY, getattr(settings, "NVIDIA_API_KEY", ""), getattr(settings, "OPENROUTER_API_KEY", "")]:
            if secret and len(secret) > 4:
                error_detail = error_detail.replace(secret, "[REDACTED]")
        logger.error(f"Database diagnostic check failed: [{error_type}] {error_detail}")

    return {
        "status": status,
        "driver": db_info.get("driver"),
        "hostname": db_info.get("hostname"),
        "port": db_info.get("port"),
        "database": db_info.get("database"),
        "environment": settings.ENVIRONMENT,
        "error_type": error_type,
        "error_detail": error_detail if status != "connected" else None
    }


@app.get("/health/llm", tags=["Health"])
@app.get(f"{settings.API_V1_STR}/health/llm", tags=["Health"])
async def health_llm_check():
    """
    Safe diagnostic endpoint for LLM provider configuration.
    Never returns secrets, authorization headers, or API keys.
    """
    provider = settings.LLM_PROVIDER.lower().strip()
    if provider == "nvidia":
        model = settings.NVIDIA_MODEL
        is_configured = bool(settings.NVIDIA_API_KEY and settings.NVIDIA_API_KEY.strip())
    elif provider == "openrouter":
        model = settings.OPENROUTER_MODEL
        is_configured = bool(settings.OPENROUTER_API_KEY and settings.OPENROUTER_API_KEY.strip())
    elif provider == "ollama":
        model = settings.OLLAMA_MODEL
        is_configured = bool(settings.OLLAMA_BASE_URL and settings.OLLAMA_BASE_URL.strip())
    else:
        model = "deterministic-rule-engine"
        is_configured = True

    return {
        "provider": provider,
        "model": model,
        "configured": is_configured
    }


