import pytest
from unittest.mock import patch
from app.core.config import settings, get_normalized_database_url, get_safe_db_info, Settings
from app.core.database import Base
from app.models.user import User
from app.models.academic import Course, Unit, CourseOutcome
from app.models.resource import Resource, ResourceChunk
from app.models.paper import QuestionPaper, Question, GenerationSession, ValidationResult

def test_all_models_registered_in_metadata():
    tables = Base.metadata.tables.keys()
    expected_tables = {
        "users",
        "courses",
        "units",
        "course_outcomes",
        "resources",
        "resource_chunks",
        "question_papers",
        "questions",
        "generation_sessions",
        "validation_results",
    }
    for t in expected_tables:
        assert t in tables, f"Expected table '{t}' in Base.metadata"

def test_postgresql_and_sqlite_url_normalization():
    # 1. Neon PostgreSQL pooled connection with sslmode & channel_binding
    neon_url = "postgresql://neondb_owner:NeonPass123!@ep-cool-lake-123456-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
    norm_neon = get_normalized_database_url(neon_url)
    assert norm_neon.startswith("postgresql+asyncpg://")
    assert "sslmode" not in norm_neon
    assert "channel_binding" not in norm_neon
    assert "neondb_owner:NeonPass123%21@ep-cool-lake-123456-pooler.us-east-2.aws.neon.tech/neondb" in norm_neon

    # 2. postgres:// with sslmode
    url1 = "postgres://qagent_user:StrongPass123@postgres-host:5432/qagent_prod?sslmode=require"
    norm1 = get_normalized_database_url(url1)
    assert norm1.startswith("postgresql+asyncpg://")
    assert "sslmode" not in norm1
    assert "StrongPass123@postgres-host:5432/qagent_prod" in norm1

    # 3. postgresql:// with special characters in password (e.g. '@', '#')
    url2 = "postgresql://neondb_owner:Hari@priya#27@ep-example-pooler.us-east-2.aws.neon.tech:5432/neondb"
    norm2 = get_normalized_database_url(url2)
    assert norm2.startswith("postgresql+asyncpg://")
    assert "Hari%40priya%2327@ep-example-pooler.us-east-2.aws.neon.tech:5432/neondb" in norm2

    # 4. Already encoded password
    url3 = "postgresql+asyncpg://admin:Secr%40t@host:6543/db"
    norm3 = get_normalized_database_url(url3)
    assert norm3 == "postgresql+asyncpg://admin:Secr%40t@host:6543/db"

    # 5. SQLite normalization
    url4 = "sqlite:///./data/academic.db"
    norm4 = get_normalized_database_url(url4)
    assert norm4 == "sqlite+aiosqlite:///./data/academic.db"

def test_safe_database_info_redaction():
    url = "postgresql://neondb_owner:SuperSecretPassword123@ep-lively-star-a2b1c3-pooler.us-east-2.aws.neon.tech:5432/neondb?sslmode=require"
    info = get_safe_db_info(url)
    assert info["driver"] == "postgresql+asyncpg"
    assert info["hostname"] == "ep-lively-star-a2b1c3-pooler.us-east-2.aws.neon.tech"
    assert info["port"] == 5432
    assert info["database"] == "neondb"
    assert "SuperSecretPassword123" not in str(info)
    assert "neondb_owner:" not in str(info)

def test_production_database_url_enforcement():
    # In production mode, missing DATABASE_URL must raise ValueError
    with patch.dict("os.environ", {"ENVIRONMENT": "production", "DATABASE_URL": ""}):
        prod_settings = Settings()
        with pytest.raises(ValueError, match="DATABASE_URL environment variable is missing"):
            _ = prod_settings.RESOLVED_DATABASE_URL

    # In production mode, SQLite is forbidden
    with patch.dict("os.environ", {"ENVIRONMENT": "production", "DATABASE_URL": "sqlite:///./prod.db"}):
        prod_settings = Settings()
        with pytest.raises(ValueError, match="SQLite is not permitted in production mode"):
            _ = prod_settings.RESOLVED_DATABASE_URL

def test_resource_storage_key_column():
    resource_cols = [c.name for c in Resource.__table__.columns]
    assert "storage_key" in resource_cols
    assert "file_path" in resource_cols
    assert "file_name" in resource_cols

def test_production_seed_prevention_setting():
    assert hasattr(settings, "SEED_DEMO_DATA")
    assert hasattr(settings, "ENVIRONMENT")
    assert hasattr(settings, "STORAGE_PROVIDER")
    assert hasattr(settings, "SAFE_DATABASE_INFO")

def test_neon_production_dialect_and_no_sqlite_fallback():
    neon_url = "postgresql://neondb_owner:SamplePass@ep-icy-credit-b4pqfc0r-pooler.c-6.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
    with patch.dict("os.environ", {"ENVIRONMENT": "production", "DATABASE_URL": neon_url}):
        prod_settings = Settings()
        assert prod_settings.IS_POSTGRES is True
        assert prod_settings.ASYNC_DATABASE_URL.startswith("postgresql+asyncpg://")
        assert "sqlite" not in prod_settings.ASYNC_DATABASE_URL
        assert "channel_binding" not in prod_settings.ASYNC_DATABASE_URL
        assert "sslmode" not in prod_settings.ASYNC_DATABASE_URL
        info = prod_settings.SAFE_DATABASE_INFO
        assert info["driver"] == "postgresql+asyncpg"
        assert info["hostname"] == "ep-icy-credit-b4pqfc0r-pooler.c-6.us-east-2.aws.neon.tech"
        assert info["database"] == "neondb"

