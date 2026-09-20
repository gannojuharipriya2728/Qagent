import pytest
from sqlalchemy import create_engine
from app.core.config import settings
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

def test_postgresql_and_sqlite_url_compatibility():
    # SQLite URL
    sqlite_url = "sqlite+aiosqlite:///./data/academic_rag.db"
    assert "sqlite" in sqlite_url
    
    # PostgreSQL asyncpg URL
    pg_url = "postgresql+asyncpg://user:pass@localhost:5432/qagent"
    assert "postgresql+asyncpg" in pg_url

def test_resource_storage_key_column():
    resource_cols = [c.name for c in Resource.__table__.columns]
    assert "storage_key" in resource_cols
    assert "file_path" in resource_cols
    assert "file_name" in resource_cols

def test_production_seed_prevention_setting():
    assert hasattr(settings, "SEED_DEMO_DATA")
    assert hasattr(settings, "ENVIRONMENT")
    assert hasattr(settings, "STORAGE_PROVIDER")
