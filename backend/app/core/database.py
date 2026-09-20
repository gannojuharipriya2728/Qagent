import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from backend.app.core.config import settings

# Ensure data directories exist
os.makedirs(settings.STORAGE_DIR, exist_ok=True)
os.makedirs(settings.VECTOR_STORAGE_DIR, exist_ok=True)
os.makedirs(settings.EXPORTS_DIR, exist_ok=True)

db_url = settings.ASYNC_DATABASE_URL
is_postgres = settings.IS_POSTGRES

engine_kwargs = {
    "echo": False,
    "future": True,
}

if is_postgres:
    # Supabase PostgreSQL configuration with SSL and connection pooling
    engine_kwargs["connect_args"] = {"ssl": "require"}
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 1800
else:
    # SQLite configuration for development/testing
    engine_kwargs["connect_args"] = {"check_same_thread": False}

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
