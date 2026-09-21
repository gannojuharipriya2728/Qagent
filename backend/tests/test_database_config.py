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
    # 1. postgres:// with sslmode
    url1 = "postgres://qagent_user:StrongPass123@postgres-host:5432/qagent_prod?sslmode=require"
    norm1 = get_normalized_database_url(url1)
    assert norm1.startswith("postgresql+asyncpg://")
    assert "sslmode" not in norm1
    assert "StrongPass123@postgres-host:5432/qagent_prod" in norm1

    # 2. postgresql:// with special character in password (e.g. '@', '#')
    url2 = "postgresql://postgres:Hari@priya#27@db.supabase.co:5432/postgres"
    norm2 = get_normalized_database_url(url2)
    assert norm2.startswith("postgresql+asyncpg://")
    assert "Hari%40priya%2327@db.supabase.co:5432/postgres" in norm2

    # 3. Already encoded password
    url3 = "postgresql+asyncpg://admin:Secr%40t@host:6543/db"
    norm3 = get_normalized_database_url(url3)
    assert norm3 == "postgresql+asyncpg://admin:Secr%40t@host:6543/db"

    # 4. SQLite normalization
    url4 = "sqlite:///./data/academic.db"
    norm4 = get_normalized_database_url(url4)
    assert norm4 == "sqlite+aiosqlite:///./data/academic.db"

def test_safe_database_info_redaction():
    url = "postgresql://postgres:SuperSecretPassword123@dpg-c12345.render.com:5432/qagent_production?sslmode=require"
    info = get_safe_db_info(url)
    assert info["driver"] == "postgresql+asyncpg"
    assert info["hostname"] == "dpg-c12345.render.com"
    assert info["port"] == 5432
    assert info["database"] == "qagent_production"
    assert "SuperSecretPassword123" not in str(info)
    assert "postgres:" not in str(info)

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
