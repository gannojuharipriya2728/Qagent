import asyncio
import sys
from pathlib import Path
from sqlalchemy import text
from sqlalchemy.engine.reflection import Inspector

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "backend"))

from app.core.config import settings
from app.core.database import engine, AsyncSessionLocal

EXPECTED_TABLES = [
    "users",
    "courses",
    "units",
    "course_outcomes",
    "resources",
    "resource_chunks",
    "question_papers",
    "questions",
    "generation_sessions",
    "validation_results"
]

async def verify_database():
    print("=" * 65)
    print("  QAgent Database Health & Verification Check")
    print("=" * 65)
    print(f"Environment:       {settings.ENVIRONMENT}")
    print(f"Database Dialect:  {'PostgreSQL (Neon)' if settings.IS_POSTGRES else 'SQLite'}")
    print(f"Seed Demo Data:    {settings.SEED_DEMO_DATA}")
    print("-" * 65)

    try:
        async with engine.connect() as conn:
            # 1. Connection ping
            res = await conn.execute(text("SELECT 1"))
            assert res.scalar() == 1
            print("[PASS] Database connectivity verified.")

            # 2. Server version
            if settings.IS_POSTGRES:
                ver = await conn.execute(text("SELECT version()"))
                ver_str = ver.scalar()
                print(f"[PASS] PostgreSQL Engine: {ver_str.split(',')[0]}")
            else:
                ver = await conn.execute(text("SELECT sqlite_version()"))
                print(f"[PASS] SQLite Engine: {ver.scalar()}")

            # 3. Check table existence
            def get_tables(sync_conn):
                inspector = Inspector.from_engine(sync_conn)
                return inspector.get_table_names()

            tables = await conn.run_sync(get_tables)
            print(f"[INFO] Tables found ({len(tables)}): {', '.join(sorted(tables)) if tables else 'None'}")

            missing_tables = [t for t in EXPECTED_TABLES if t not in tables]
            if missing_tables:
                print(f"[WARN] Missing expected tables: {missing_tables}")
            else:
                print("[PASS] All 10 required production tables are present.")

            # 4. Table row counts
            print("\nTable Row Counts:")
            print("-" * 40)
            total_rows = 0
            for tbl in EXPECTED_TABLES:
                if tbl in tables:
                    count_res = await conn.execute(text(f"SELECT COUNT(*) FROM {tbl}"))
                    count = count_res.scalar()
                    total_rows += count
                    print(f"  - {tbl:<25}: {count} rows")
                else:
                    print(f"  - {tbl:<25}: [TABLE NOT FOUND]")
            print("-" * 40)
            print(f"Total production records: {total_rows}")

            if total_rows == 0:
                print("[PASS] Database is completely clean (0 demo/test records). Ready for initial admin creation.")
            else:
                print(f"[INFO] Database contains {total_rows} existing records.")

    except Exception as e:
        print(f"[FAIL] Database verification failed: {e}")
        sys.exit(1)
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(verify_database())
