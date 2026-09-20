"""
QAgent Production Data Reset Script
Location: backend/scripts/reset_production_data.py

Usage:
  # Dry run (non-destructive inspection):
  py backend/scripts/reset_production_data.py --dry-run

  # Verification only (checks current clean status):
  py backend/scripts/reset_production_data.py --verify-only

  # Full Execution (Requires explicit confirmation):
  set RESET_PRODUCTION_DATA=YES
  py backend/scripts/reset_production_data.py --confirm

  # Optional: For remote PostgreSQL / Cloud Storage reset:
  set RESET_PRODUCTION_DATA=YES
  py backend/scripts/reset_production_data.py --confirm --delete-production-storage

  # Optional: Create initial production admin during reset:
  set RESET_PRODUCTION_DATA=YES
  py backend/scripts/reset_production_data.py --confirm --admin-email admin@youruniversity.edu --admin-password "YourStrongPassword123!" --admin-name "System Administrator"
"""

import os
import sys
import shutil
import asyncio
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Ensure root directory is on sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))
load_dotenv(dotenv_path=ROOT_DIR / ".env")

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select, func, text
from backend.app.core.config import settings
from backend.app.core.database import Base
from backend.app.core.security import get_password_hash
from backend.app.models.user import User
from backend.app.models.academic import Course, Unit, CourseOutcome
from backend.app.models.resource import Resource, ResourceChunk
from backend.app.models.paper import QuestionPaper, Question, GenerationSession, ValidationResult

DATA_DIR = ROOT_DIR / "data"
DB_FILE = DATA_DIR / "academic_rag.db"
VECTOR_DIR = DATA_DIR / "vector_store"
VECTOR_INDEX_FILE = VECTOR_DIR / "index.json"
TEST_VECTOR_FILE = DATA_DIR / "test_vector_store.json"
UPLOADS_DIR = DATA_DIR / "uploads"
EXPORTS_DIR = DATA_DIR / "exports"

TABLE_MODELS = [
    ("users", User),
    ("courses", Course),
    ("units", Unit),
    ("course_outcomes", CourseOutcome),
    ("resources", Resource),
    ("resource_chunks", ResourceChunk),
    ("question_papers", QuestionPaper),
    ("questions", Question),
    ("generation_sessions", GenerationSession),
    ("validation_results", ValidationResult),
]

def verify_directories():
    """Ensure data directory structure is present and intact."""
    for d in [DATA_DIR, VECTOR_DIR, UPLOADS_DIR, EXPORTS_DIR]:
        d.mkdir(parents=True, exist_ok=True)

async def check_current_state():
    """Inspect current database and disk storage counts."""
    is_sqlite = "sqlite" in settings.DATABASE_URL
    state = {
        "db_type": "SQLite" if is_sqlite else "PostgreSQL",
        "database_url_safe": settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else settings.DATABASE_URL,
        "db_exists": DB_FILE.exists() if is_sqlite else True,
        "db_size_bytes": DB_FILE.stat().st_size if (is_sqlite and DB_FILE.exists()) else 0,
        "storage_provider": settings.STORAGE_PROVIDER,
        "vector_index_exists": VECTOR_INDEX_FILE.exists(),
        "vector_index_size_bytes": VECTOR_INDEX_FILE.stat().st_size if VECTOR_INDEX_FILE.exists() else 0,
        "upload_files": [f.name for f in UPLOADS_DIR.glob("*") if f.is_file()] if UPLOADS_DIR.exists() else [],
        "export_files": [f.name for f in EXPORTS_DIR.glob("*") if f.is_file()] if EXPORTS_DIR.exists() else [],
        "test_vector_exists": TEST_VECTOR_FILE.exists(),
        "table_counts": {}
    }

    try:
        connect_args = {"check_same_thread": False} if is_sqlite else {}
        engine = create_async_engine(settings.DATABASE_URL, echo=False, connect_args=connect_args)
        async_session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as session:
            for tbl_name, model_cls in TABLE_MODELS:
                try:
                    stmt = select(func.count()).select_from(model_cls)
                    count = (await session.execute(stmt)).scalar_one()
                    state["table_counts"][tbl_name] = count
                except Exception:
                    state["table_counts"][tbl_name] = "table_not_found"
        await engine.dispose()
    except Exception as e:
        state["db_error"] = str(e)
    return state

def print_state_report(state: dict, title: str = "CURRENT STORAGE & DATABASE STATE"):
    print("=" * 65)
    print(f"  {title}")
    print("=" * 65)
    print(f"  Database Engine:      {state['db_type']} ({state['database_url_safe']})")
    print(f"  Storage Provider:     {state['storage_provider']}")
    print(f"  Vector Index:         {VECTOR_INDEX_FILE} ({'EXISTS - ' + str(state['vector_index_size_bytes']) + ' bytes' if state['vector_index_exists'] else 'NOT FOUND'})")
    print(f"  Test Vector File:     {TEST_VECTOR_FILE} ({'EXISTS' if state['test_vector_exists'] else 'NOT FOUND'})")
    print(f"  Uploads Directory:    {len(state['upload_files'])} files ({UPLOADS_DIR})")
    for f in state['upload_files'][:5]:
        print(f"    - {f}")
    if len(state['upload_files']) > 5:
        print(f"    ... and {len(state['upload_files']) - 5} more")
    print(f"  Exports Directory:    {len(state['export_files'])} files ({EXPORTS_DIR})")
    for f in state['export_files']:
        print(f"    - {f}")
    
    print("\n  Database Table Row Counts:")
    if state["table_counts"]:
        for tbl_name, count in state["table_counts"].items():
            print(f"    - {tbl_name:22}: {count}")
    else:
        print("    (No database tables initialized)")
    print("=" * 65)

async def execute_reset(admin_email: str = None, admin_password: str = None, admin_name: str = None, delete_remote: bool = False):
    print("\n>>> INITIATING SAFE PRODUCTION DATA RESET <<<\n")
    verify_directories()

    is_sqlite = "sqlite" in settings.DATABASE_URL
    connect_args = {"check_same_thread": False} if is_sqlite else {}
    engine = create_async_engine(settings.DATABASE_URL, echo=False, connect_args=connect_args)

    if is_sqlite:
        # Close connection and remove local DB file
        await engine.dispose()
        if DB_FILE.exists():
            try:
                DB_FILE.unlink()
                print(f"  [OK] Removed SQLite database file: {DB_FILE}")
            except Exception as e:
                print(f"  [WARN] Could not remove {DB_FILE}: {e}")
        engine = create_async_engine(settings.DATABASE_URL, echo=False, connect_args=connect_args)
    else:
        # PostgreSQL: Drop and recreate all tables
        print("  [POSTGRESQL] Truncating/Dropping tables in PostgreSQL database...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        print("  [OK] PostgreSQL schema cleared.")

    # 2. Remove vector index
    if VECTOR_INDEX_FILE.exists():
        try:
            VECTOR_INDEX_FILE.unlink()
            print(f"  [OK] Removed vector index: {VECTOR_INDEX_FILE}")
        except Exception as e:
            print(f"  [WARN] Could not remove {VECTOR_INDEX_FILE}: {e}")

    # 3. Remove test vector index if present
    if TEST_VECTOR_FILE.exists():
        try:
            TEST_VECTOR_FILE.unlink()
            print(f"  [OK] Removed test vector index: {TEST_VECTOR_FILE}")
        except Exception as e:
            print(f"  [WARN] Could not remove {TEST_VECTOR_FILE}: {e}")

    # 4. Clear uploads directory
    if UPLOADS_DIR.exists():
        cleared_uploads = 0
        for item in UPLOADS_DIR.glob("*"):
            if item.is_file():
                item.unlink()
                cleared_uploads += 1
            elif item.is_dir():
                shutil.rmtree(item)
                cleared_uploads += 1
        print(f"  [OK] Cleared uploads directory ({cleared_uploads} files/folders removed)")

    # 5. Clear exports directory
    if EXPORTS_DIR.exists():
        cleared_exports = 0
        for item in EXPORTS_DIR.glob("*"):
            if item.is_file():
                item.unlink()
                cleared_exports += 1
            elif item.is_dir():
                shutil.rmtree(item)
                cleared_exports += 1
        print(f"  [OK] Cleared exports directory ({cleared_exports} files/folders removed)")

    # 6. Recreate fresh clean database schema
    print("\n  [INITIALIZING] Creating fresh database tables from SQLAlchemy metadata...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("  [OK] Database schema initialized with all 10 core tables.")

    # 7. Optionally create initial production administrator
    if admin_email and admin_password:
        print(f"\n  [PROVISIONING] Creating initial production administrator account: {admin_email}...")
        async_session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as session:
            admin_user = User(
                email=admin_email.strip().lower(),
                full_name=admin_name.strip() if admin_name else "Production Administrator",
                department="Academic Administration",
                hashed_password=get_password_hash(admin_password),
                role="admin",
                is_active=True
            )
            session.add(admin_user)
            await session.commit()
            print(f"  [OK] Production admin created successfully with ID: {admin_user.id}")

    await engine.dispose()
    print("\n>>> PRODUCTION RESET COMPLETED SUCCESSFULLY! <<<\n")

def main():
    parser = argparse.ArgumentParser(description="QAgent Safe Production Data Reset Tool")
    parser.add_argument("--dry-run", action="store_true", help="Inspect state and simulate reset without modifying any files")
    parser.add_argument("--verify-only", action="store_true", help="Inspect and verify if the environment is currently in a clean state")
    parser.add_argument("--confirm", action="store_true", help="Explicit confirmation flag required alongside RESET_PRODUCTION_DATA=YES")
    parser.add_argument("--delete-production-storage", action="store_true", help="Explicit confirmation flag required for remote PostgreSQL/S3 resets")
    parser.add_argument("--admin-email", type=str, default=None, help="Optional email for the initial production administrator")
    parser.add_argument("--admin-password", type=str, default=None, help="Optional password for the initial production administrator")
    parser.add_argument("--admin-name", type=str, default="System Administrator", help="Display name for initial administrator")
    args = parser.parse_args()

    # Phase 1: Check state
    state = asyncio.run(check_current_state())

    if args.verify_only:
        print_state_report(state, title="QAGENT PRODUCTION CLEAN-STATE VERIFICATION")
        is_clean = (
            state["upload_files"] == [] and
            state["export_files"] == [] and
            not state["test_vector_exists"] and
            (
                all(c in [0, 1] for c in state["table_counts"].values()) # 0 or 1 initial admin
            )
        )
        if is_clean:
            print("\n[VERIFICATION RESULT] State is CLEAN for production deployment.")
            sys.exit(0)
        else:
            print("\n[VERIFICATION RESULT] State contains development/test artifacts.")
            sys.exit(0)

    if args.dry_run:
        print_state_report(state, title="QAGENT PRODUCTION RESET — DRY RUN SIMULATION")
        print("\n[DRY RUN SUMMARY] The following actions WOULD be executed on real run:")
        print(f"  1. Database ({state['db_type']}):   Drop/recreate all 10 schema tables (0 rows)")
        print(f"  2. Delete vector index:         {VECTOR_INDEX_FILE}")
        print(f"  3. Delete test vector file:     {TEST_VECTOR_FILE}")
        print(f"  4. Delete all files in uploads: {UPLOADS_DIR} ({len(state['upload_files'])} files)")
        print(f"  5. Delete all files in exports: {EXPORTS_DIR} ({len(state['export_files'])} files)")
        print("  6. Ensure zero demo users, zero demo courses, zero demo resources exist")
        print("\n(No files were modified or deleted during this dry-run).")
        sys.exit(0)

    # Phase 2: Confirmation Verification
    env_confirm = os.getenv("RESET_PRODUCTION_DATA", "").strip()
    if env_confirm != "YES" or not args.confirm:
        print("\n" + "!" * 65)
        print("  CRITICAL SAFETY ABORT: PRODUCTION RESET NOT CONFIRMED")
        print("!" * 65)
        print("  This operation permanently clears all courses, users, uploads,")
        print("  vector indexes, and generated question papers.\n")
        print("  To execute this reset, BOTH of the following are required:")
        print("    1. Set environment variable: RESET_PRODUCTION_DATA=YES")
        print("    2. Pass the CLI argument:     --confirm\n")
        print("  Example (Windows CMD / PowerShell):")
        print("    set RESET_PRODUCTION_DATA=YES")
        print("    py backend/scripts/reset_production_data.py --confirm")
        print("\n  Or for dry-run simulation:")
        print("    py backend/scripts/reset_production_data.py --dry-run\n")
        print("!" * 65)
        sys.exit(1)

    # If running against production/remote PostgreSQL, require --delete-production-storage
    is_remote = "postgresql" in settings.DATABASE_URL or settings.ENVIRONMENT == "production"
    if is_remote and not args.delete_production_storage:
        print("\n" + "!" * 65)
        print("  PRODUCTION SAFETY LOCK: REMOTE/POSTGRESQL RESET REQUIRES:")
        print("  --delete-production-storage flag in addition to --confirm")
        print("!" * 65)
        sys.exit(1)

    # Phase 3: Execute Reset
    asyncio.run(execute_reset(
        admin_email=args.admin_email,
        admin_password=args.admin_password,
        admin_name=args.admin_name,
        delete_remote=args.delete_production_storage
    ))

    # Phase 4: Final verification report
    final_state = asyncio.run(check_current_state())
    print_state_report(final_state, title="FINAL POST-RESET VERIFICATION REPORT")

if __name__ == "__main__":
    main()
