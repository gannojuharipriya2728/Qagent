import os
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import engine, Base, AsyncSessionLocal, get_db
from app.core.security import decode_access_token
from app.core.seed import seed_database
from app.api.deps import security_bearer
from app.api.auth import router as auth_router, faculty_router
from app.api.courses import router as courses_router
from app.api.resources import router as resources_router
from app.api.generate import router as generate_router
from app.api.papers import router as papers_router
from app.api.admin import router as admin_router
from app.api.ai import router as ai_router
from app.services.llm.factory import get_llm_provider

@asynccontextmanager
async def lifespan(app: FastAPI):
    # In development/test environments, auto-create tables if missing.
    if settings.ENVIRONMENT.lower() != "production":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    else:
        # In production, automatically apply Alembic migrations to keep Neon PostgreSQL schema in sync
        try:
            from alembic.config import Config
            from alembic import command
            import asyncio
            from pathlib import Path
            root_dir = Path(__file__).resolve().parent.parent.parent
            ini_path = root_dir / "alembic.ini"
            if ini_path.exists():
                alembic_cfg = Config(str(ini_path))
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, lambda: command.upgrade(alembic_cfg, "head"))
                logger.info("DATABASE_MIGRATION_AUTO_UPGRADE_COMPLETE")
        except Exception as m_err:
            logger.warning(f"Production startup migration check warning: {m_err}")

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

# Mount Routers (mount both with API_V1_STR and without prefix for flexible serverless routing)
routers = [
    auth_router,
    faculty_router,
    courses_router,
    resources_router,
    generate_router,
    papers_router,
    admin_router,
    ai_router,
]

for r in routers:
    app.include_router(r, prefix=settings.API_V1_STR)
    # Also mount directly without prefix if API_V1_STR is non-empty
    if settings.API_V1_STR:
        app.include_router(r)

import logging

logger = logging.getLogger("qagent.main")

@app.get("/", tags=["Health"])
@app.get("/index.html", tags=["Health"], include_in_schema=False)
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
@app.get("/api/health", tags=["Health"])
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
@app.get("/api/health/db", tags=["Health"])
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
@app.get("/api/health/llm", tags=["Health"])
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


# =================================================================
# LLM DIAGNOSTIC & RUNTIME VERIFICATION ENDPOINTS (SAFE & NON-SECRET)
# =================================================================

@app.get("/debug/llm-config", tags=["Diagnostics"])
@app.get(f"{settings.API_V1_STR}/debug/llm-config", tags=["Diagnostics"])
async def debug_llm_config():
    """
    Diagnostic endpoint returning LLM configuration and key presence.
    Never exposes actual keys or secrets.
    """
    configured_provider = settings.LLM_PROVIDER.lower().strip()
    resolved_provider = configured_provider if configured_provider in ["openrouter", "nvidia", "ollama", "deterministic"] else "openrouter"
    
    if resolved_provider == "openrouter":
        model = settings.OPENROUTER_MODEL
        base_url = settings.OPENROUTER_BASE_URL
    elif resolved_provider == "nvidia":
        model = settings.NVIDIA_MODEL
        base_url = settings.NVIDIA_BASE_URL
    elif resolved_provider == "ollama":
        model = settings.OLLAMA_MODEL
        base_url = settings.OLLAMA_BASE_URL
    else:
        model = "deterministic-rule-engine"
        base_url = "local"

    return {
        "configured_provider": configured_provider,
        "resolved_provider": resolved_provider,
        "model": model,
        "base_url": base_url,
        "openrouter_key_configured": bool(settings.OPENROUTER_API_KEY and settings.OPENROUTER_API_KEY.strip()),
        "nvidia_key_configured": bool(settings.NVIDIA_API_KEY and settings.NVIDIA_API_KEY.strip())
    }


@app.get("/debug/llm-provider-path", tags=["Diagnostics"])
@app.get(f"{settings.API_V1_STR}/debug/llm-provider-path", tags=["Diagnostics"])
async def debug_llm_provider_path():
    """
    Instantiates the LLM provider through the same centralized factory used by
    the agentic workflow and reports the concrete runtime class and configuration.
    """
    provider_inst = get_llm_provider()
    return {
        "provider_class": provider_inst.__class__.__name__,
        "provider": getattr(provider_inst, "provider_name", settings.LLM_PROVIDER.lower().strip()),
        "model": getattr(provider_inst, "model", settings.OPENROUTER_MODEL)
    }


@app.get("/debug/routes", tags=["Diagnostics"])
@app.get(f"{settings.API_V1_STR}/debug/routes", tags=["Diagnostics"])
async def debug_routes():
    """
    Diagnostic endpoint returning registered routes and HTTP methods safely.
    NEVER exposes secrets, passwords, tokens, DATABASE_URL, or API keys.
    """
    routes = []
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            routes.append({
                "path": route.path,
                "methods": sorted(list(route.methods))
            })
    return {
        "count": len(routes),
        "routes": routes
    }


@app.get("/debug/faculty-profile", tags=["Diagnostics"])
@app.get(f"{settings.API_V1_STR}/debug/faculty-profile", tags=["Diagnostics"])
async def debug_faculty_profile(
    auth_header: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: AsyncSession = Depends(get_db)
):
    """
    Diagnostic endpoint to verify faculty profile authentication and DB state.
    Never exposes secrets, tokens, password hashes, or API keys.
    """
    from app.models.user import User
    from sqlalchemy import select, text
    
    authenticated = False
    user_id_present = False
    user_found = False
    db_connected = False

    try:
        await db.execute(text("SELECT 1"))
        db_connected = True
    except Exception:
        db_connected = False

    if auth_header and auth_header.credentials:
        try:
            payload = decode_access_token(auth_header.credentials)
            if payload and payload.get("sub"):
                authenticated = True
                user_id_present = True
                sub_str = str(payload.get("sub")).strip()
                if sub_str.isdigit():
                    stmt = select(User).where(User.id == int(sub_str))
                else:
                    stmt = select(User).where(User.email == sub_str)
                user = (await db.execute(stmt)).scalar_one_or_none()
                if user and user.is_active:
                    user_found = True
        except Exception:
            pass

    return {
        "route_exists": True,
        "authenticated": authenticated,
        "user_id_present": user_id_present,
        "user_found": user_found,
        "database_connected": db_connected
    }


# =================================================================
# TEMPORARY REGISTRATION DIAGNOSTIC ENDPOINTS (SAFE & NON-SECRET)
# =================================================================

@app.get(f"{settings.API_V1_STR}/debug/register-config", tags=["Diagnostics"])
async def debug_register_config():
    """
    Temporary diagnostic endpoint to inspect registration configuration safely.
    NEVER exposes passwords, SECRET_KEY, DATABASE_URL, or API keys.
    """
    from app.models.user import User
    db_info = settings.SAFE_DATABASE_INFO
    routes_list = []
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            routes_list.append(f"{route.path} {sorted(list(route.methods))}")

    return {
        "route_exists": any("/api/auth/register" in r for r in routes_list),
        "environment": settings.ENVIRONMENT,
        "database_driver": db_info.get("driver"),
        "database_host": db_info.get("hostname"),
        "database_name": db_info.get("database"),
        "user_model_loaded": hasattr(User, "__tablename__") and User.__tablename__ == "users",
        "registered_routes": routes_list
    }


@app.post(f"{settings.API_V1_STR}/debug/register", tags=["Diagnostics"])
async def debug_register_trace(payload: dict):
    """
    Temporary diagnostic endpoint that simulates registration step-by-step
    and identifies the exact failing stage without crashing or exposing secrets.
    """
    from app.models.user import User
    from app.schemas.auth import UserCreate
    from app.core.security import get_password_hash, create_access_token
    from sqlalchemy import text, select

    report = {
        "status": "in_progress",
        "stage": "starting",
        "table_users_exists": False,
        "error_type": None,
        "error_detail": None,
        "user_lookup_ok": False,
        "password_hash_ok": False,
        "user_insert_ok": False,
        "token_generation_ok": False
    }

    # Stage 1: Schema Validation
    report["stage"] = "schema_validation"
    try:
        user_in = UserCreate(**payload)
    except Exception as e:
        report["status"] = "failed"
        report["error_type"] = e.__class__.__name__
        report["error_detail"] = str(e)
        return report

    # Stage 2: Database Table Check & Session
    report["stage"] = "table_check"
    try:
        async with AsyncSessionLocal() as session:
            # Check table existence
            table_check = await session.execute(
                text("SELECT 1 FROM information_schema.tables WHERE table_name = 'users'")
                if settings.IS_POSTGRES else
                text("SELECT 1 FROM sqlite_master WHERE type='table' AND name='users'")
            )
            report["table_users_exists"] = bool(table_check.scalar())

            # Stage 3: User Lookup
            report["stage"] = "user_lookup"
            stmt = select(User).where(User.email == user_in.email)
            existing = (await session.execute(stmt)).scalar_one_or_none()
            report["user_lookup_ok"] = True
            if existing:
                report["status"] = "failed"
                report["error_type"] = "UserAlreadyExists"
                report["error_detail"] = f"User with email '{user_in.email}' already exists."
                return report

            # Stage 4: Password Hash
            report["stage"] = "password_hash"
            hashed_pwd = get_password_hash(user_in.password)
            report["password_hash_ok"] = True

            # Stage 5: User Insert & Commit
            report["stage"] = "user_insert"
            user = User(
                email=user_in.email,
                full_name=user_in.full_name,
                department=user_in.department,
                role=user_in.role or "faculty",
                hashed_password=hashed_pwd,
                is_active=True
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            report["user_insert_ok"] = True

            # Stage 6: Token Generation
            report["stage"] = "token_generation"
            _ = create_access_token(subject=user.id, role=user.role)
            report["token_generation_ok"] = True

            # Cleanup test user created via debug endpoint if email starts with debug
            if "debug" in user_in.email.lower() or "test" in user_in.email.lower():
                await session.delete(user)
                await session.commit()
                report["cleaned_up"] = True

            report["status"] = "success"
            report["stage"] = "completed"
            return report

    except Exception as e:
        report["status"] = "failed"
        report["error_type"] = e.__class__.__name__
        sanitized_err = str(e).splitlines()[0] if str(e) else "Database execution error"
        for secret in [settings.SECRET_KEY, getattr(settings, "NVIDIA_API_KEY", ""), getattr(settings, "OPENROUTER_API_KEY", "")]:
            if secret and len(secret) > 4:
                sanitized_err = sanitized_err.replace(secret, "[REDACTED]")
        report["error_detail"] = sanitized_err
        return report



