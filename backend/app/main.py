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
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(courses_router, prefix=settings.API_V1_STR)
app.include_router(resources_router, prefix=settings.API_V1_STR)
app.include_router(generate_router, prefix=settings.API_V1_STR)
app.include_router(papers_router, prefix=settings.API_V1_STR)
app.include_router(admin_router, prefix=settings.API_V1_STR)
app.include_router(ai_router, prefix=settings.API_V1_STR)

@app.get("/health", tags=["Health"])
@app.get(f"{settings.API_V1_STR}/health", tags=["Health"])
async def health_check():
    db_status = "connected"
    try:
        from sqlalchemy import text
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        db_status = "unreachable"

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

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "database": db_status,
        "storage_provider": settings.STORAGE_PROVIDER,
        "storage": storage_status,
        "llm_provider": settings.LLM_PROVIDER,
        "llm_model": settings.OPENROUTER_MODEL
    }

