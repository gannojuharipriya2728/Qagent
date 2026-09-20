"""
QAgent Production Initial Admin Creator
Location: backend/scripts/create_initial_admin.py

Usage:
  py backend/scripts/create_initial_admin.py --email admin@university.edu --password "SecureAdminPass2026!" --name "Dean of Examinations"
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))
load_dotenv(dotenv_path=ROOT_DIR / ".env")

from sqlalchemy import select
from backend.app.core.config import settings
from backend.app.core.database import engine, AsyncSessionLocal
from backend.app.core.security import get_password_hash
from backend.app.models.user import User

async def create_admin(email: str, password: str, name: str, department: str):
    async with AsyncSessionLocal() as session:
        clean_email = email.strip().lower()
        stmt = select(User).where(User.email == clean_email)
        existing = (await session.execute(stmt)).scalar_one_or_none()
        
        if existing:
            print(f"[ERROR] User with email '{clean_email}' already exists (Role: {existing.role}, ID: {existing.id}).")
            sys.exit(1)

        admin = User(
            email=clean_email,
            full_name=name.strip(),
            department=department.strip(),
            hashed_password=get_password_hash(password),
            role="admin",
            is_active=True
        )
        session.add(admin)
        await session.commit()
        await session.refresh(admin)
        print("=" * 60)
        print("  PRODUCTION ADMINISTRATOR CREATED SUCCESSFULLY")
        print("=" * 60)
        print(f"  ID:         {admin.id}")
        print(f"  Email:      {admin.email}")
        print(f"  Full Name:  {admin.full_name}")
        print(f"  Role:       {admin.role}")
        print(f"  Department: {admin.department}")
        print(f"  Active:     {admin.is_active}")
        print("=" * 60)

    await engine.dispose()

def main():
    parser = argparse.ArgumentParser(description="Create QAgent Initial Production Admin Account")
    parser.add_argument("--email", type=str, required=True, help="Administrator email address")
    parser.add_argument("--password", type=str, required=True, help="Administrator strong password")
    parser.add_argument("--name", type=str, default="Production Administrator", help="Administrator full display name")
    parser.add_argument("--department", type=str, default="Academic Administration", help="Academic department")
    args = parser.parse_args()

    if len(args.password) < 8:
        print("[ERROR] Password must be at least 8 characters long for production security.")
        sys.exit(1)

    asyncio.run(create_admin(
        email=args.email,
        password=args.password,
        name=args.name,
        department=args.department
    ))

if __name__ == "__main__":
    main()
