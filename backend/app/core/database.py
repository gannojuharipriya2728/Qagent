import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.core.config import settings

import logging

logger = logging.getLogger("qagent.database")

# Ensure data directories exist (safely ignore in read-only serverless filesystems)
try:
    os.makedirs(settings.STORAGE_DIR, exist_ok=True)
    os.makedirs(settings.VECTOR_STORAGE_DIR, exist_ok=True)
    os.makedirs(settings.EXPORTS_DIR, exist_ok=True)
except OSError:
    pass

db_url = settings.ASYNC_DATABASE_URL
is_postgres = settings.IS_POSTGRES

engine_kwargs = {
    "echo": False,
    "future": True,
}

if is_postgres:
    # PostgreSQL configuration with SSL and connection pooling for Render / Managed Postgres
    ssl_mode = settings.DB_SSL_MODE.lower().strip()
    if ssl_mode in ["require", "true", "1"]:
        engine_kwargs["connect_args"] = {"ssl": "require"}
    elif ssl_mode in ["disable", "false", "0", "off"]:
        engine_kwargs["connect_args"] = {}
    else:
        engine_kwargs["connect_args"] = {"ssl": ssl_mode}
        
    engine_kwargs["pool_size"] = settings.DB_POOL_SIZE
    engine_kwargs["max_overflow"] = settings.DB_MAX_OVERFLOW
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 1800
else:
    # SQLite configuration for local development and test environments
    engine_kwargs["connect_args"] = {"check_same_thread": False}

safe_info = settings.SAFE_DATABASE_INFO
logger.info(
    f"Initializing database engine with driver={safe_info.get('driver')}, "
    f"host={safe_info.get('hostname')}:{safe_info.get('port')}, "
    f"database={safe_info.get('database')}, environment={settings.ENVIRONMENT}"
)

engine = create_async_engine(db_url, **engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
