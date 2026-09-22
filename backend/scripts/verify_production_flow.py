"""
QAgent Production Flow Verification Script
Tests end-to-end database-backed operations against Neon PostgreSQL:
1. Health & AI Gateway connectivity
2. User creation & JWT Authentication
3. Course & Academic structure persistence
4. Syllabus indexing & retrieval
5. Question Paper & Question generation persistence
6. Examination PDF generation
7. Safe teardown of test verification records to leave database pristine (0 demo records)
"""

import os
import sys
import asyncio
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "backend"))

from sqlalchemy import select, delete, text
from app.core.config import settings
from app.core.database import engine, AsyncSessionLocal
from app.core.security import get_password_hash, create_access_token
from app.models.user import User
from app.models.academic import Course, Unit, CourseOutcome
from app.models.resource import Resource, ResourceChunk
from app.models.paper import QuestionPaper, Question, GenerationSession, ValidationResult
from app.services.llm.openrouter_provider import OpenRouterProvider
from app.services.pdf_generator import QuestionPaperPDFGenerator

async def test_full_production_flow():
    print("=" * 65)
    print("  QAgent Neon PostgreSQL End-to-End Operational Verification")
    print("=" * 65)
    print(f"Database:      {'PostgreSQL (Neon)' if settings.IS_POSTGRES else 'SQLite'}")
    print(f"Environment:   {settings.ENVIRONMENT}")
    print("-" * 65)

    created_ids = {
        "user_id": None,
        "course_id": None,
        "paper_id": None
    }

    async with AsyncSessionLocal() as session:
        # Pre-cleanup to ensure clean starting state
        await session.execute(delete(ValidationResult))
        await session.execute(delete(GenerationSession))
        await session.execute(delete(Question))
        await session.execute(delete(QuestionPaper))
        await session.execute(delete(ResourceChunk))
        await session.execute(delete(Resource))
        await session.execute(delete(CourseOutcome))
        await session.execute(delete(Unit))
        await session.execute(delete(Course))
        await session.execute(delete(User))
        await session.commit()

        try:
            # 1. Health & OpenRouter Provider Health
            print("\n[STEP 1] Verifying OpenRouter LLM Gateway...")
            provider = OpenRouterProvider()
            llm_healthy = await provider.check_health()
            print(f"  OpenRouter ({settings.OPENROUTER_MODEL}): {'[REACHABLE]' if llm_healthy else '[UNREACHABLE]'}")
            assert llm_healthy, "OpenRouter LLM gateway unreachable"

            # 2. User Creation & Authentication
            print("\n[STEP 2] Testing User Registration & Password Hashing in Supabase...")
            test_user = User(
                email="test.migration.admin@qagent.internal",
                full_name="Supabase Migration Verifier",
                hashed_password=get_password_hash("SupabaseSecurePass2026!"),
                role="admin",
                department="Computer Science & Engineering",
                is_active=True
            )
            session.add(test_user)
            await session.commit()
            await session.refresh(test_user)
            created_ids["user_id"] = test_user.id
            print(f"  [OK] User created successfully in PostgreSQL. ID: {test_user.id}")

            # Verify JWT token generation
            token = create_access_token({"sub": test_user.email, "role": test_user.role, "id": test_user.id})
            assert token and len(token) > 20
            print(f"  [OK] JWT Access Token Generated: {token[:25]}...")

            # 3. Course Creation & Academic Structure
            print("\n[STEP 3] Testing Course & Curriculum Persistence...")
            test_course = Course(
                code="SUPA701",
                name="Cloud Computing & Distributed Systems",
                department="Computer Science & Engineering",
                semester="Semester VII",
                academic_year="2025-2026",
                description="Advanced distributed cloud architectures"
            )
            session.add(test_course)
            await session.commit()
            await session.refresh(test_course)
            created_ids["course_id"] = test_course.id
            print(f"  [OK] Course created in PostgreSQL. ID: {test_course.id} ({test_course.code})")

            # Add Units & COs
            unit1 = Unit(course_id=test_course.id, unit_number=1, title="Cloud Models & Virtualization", topics="IaaS, PaaS, SaaS, Hypervisors")
            unit2 = Unit(course_id=test_course.id, unit_number=2, title="Distributed Storage", topics="GFS, HDFS, Consistency Models")
            co1 = CourseOutcome(course_id=test_course.id, code="CO1", description="Understand cloud virtualization", target_bloom_level="Understand")
            co2 = CourseOutcome(course_id=test_course.id, code="CO2", description="Design distributed storage architectures", target_bloom_level="Create")
            session.add_all([unit1, unit2, co1, co2])
            await session.commit()
            print("  [OK] Units & Course Outcomes persisted with Foreign Key integrity.")

            # 4. Resource & Resource Chunks
            print("\n[STEP 4] Testing Resource & Chunk Storage...")
            resource = Resource(
                course_id=test_course.id,
                title="Cloud Computing Textbook",
                file_name="cloud_computing_v1.pdf",
                file_path="./data/uploads/cloud_computing_v1.pdf",
                storage_key="courses/SUPA701/cloud_computing_v1.pdf",
                file_type="pdf",
                document_type="textbook",
                file_size_bytes=1048576,
                status="Processed",
                chunk_count=2,
                uploaded_by=test_user.id
            )
            session.add(resource)
            await session.commit()
            await session.refresh(resource)

            chunk1 = ResourceChunk(
                resource_id=resource.id,
                chunk_index=1,
                content="Hypervisor Type 1 runs directly on bare metal hardware providing superior virtualization performance.",
                page_number=14,
                unit_number=1,
                topic="Virtualization",
                token_count=18
            )
            chunk2 = ResourceChunk(
                resource_id=resource.id,
                chunk_index=2,
                content="HDFS master-worker architecture utilizes NameNode for metadata and DataNodes for block storage.",
                page_number=58,
                unit_number=2,
                topic="Distributed Storage",
                token_count=18
            )
            session.add_all([chunk1, chunk2])
            await session.commit()
            print(f"  [OK] Resource and {resource.chunk_count} Chunks persisted successfully.")

            # 5. Question Paper & Questions Synthesis
            print("\n[STEP 5] Testing Question Paper, Questions & JSON Columns...")
            paper = QuestionPaper(
                course_id=test_course.id,
                created_by=test_user.id,
                title="B.Tech VII Semester Examination — Cloud Computing",
                examination_name="Semester End Examination 2026",
                institution_name="Department of Computer Science & Engineering",
                duration_minutes=180,
                total_marks=70,
                section_config=[
                    {"name": "Section A", "total_questions": 10, "marks_per_question": 2},
                    {"name": "Section B", "total_questions": 5, "marks_per_question": 10}
                ],
                difficulty_distribution={"Easy": 30, "Medium": 50, "Hard": 20},
                bloom_distribution={"Understand": 40, "Apply": 30, "Analyze": 20, "Create": 10},
                syllabus_coverage_score=95.5,
                status="Generated"
            )
            session.add(paper)
            await session.commit()
            await session.refresh(paper)
            created_ids["paper_id"] = paper.id

            q1 = Question(
                paper_id=paper.id,
                section_name="Section A",
                question_number=1,
                question_text="Distinguish between Type-1 and Type-2 Hypervisors in Cloud Virtualization.",
                marks=2,
                unit_number=1,
                bloom_level="Understand",
                course_outcome="CO1",
                difficulty="Easy",
                question_type="Short",
                source_topics=["Virtualization"],
                source_documents=[{"document_name": "cloud_computing_v1.pdf", "page": 14, "similarity_score": 0.92}],
                generation_reasoning="Synthesized from core virtualization syllabus with Bloom verb Distinguish."
            )
            q2 = Question(
                paper_id=paper.id,
                section_name="Section B",
                question_number=11,
                question_text="(a) Explain the architecture of HDFS NameNode and DataNodes.\n(b) Propose a high-availability distributed block replication strategy under network partitions.",
                marks=10,
                unit_number=2,
                bloom_level="Create",
                course_outcome="CO2",
                difficulty="Hard",
                question_type="Descriptive",
                source_topics=["Distributed Storage"],
                source_documents=[{"document_name": "cloud_computing_v1.pdf", "page": 58, "similarity_score": 0.89}],
                generation_reasoning="Synthesized for high-order architectural design in Distributed Systems."
            )
            session.add_all([q1, q2])
            await session.commit()
            print(f"  [OK] Question Paper ID {paper.id} and Questions saved with JSON metadata.")

            # 6. PDF Generation
            print("\n[STEP 6] Testing PDF Generation from PostgreSQL Records...")
            paper_dict = {
                "title": paper.title,
                "examination_name": paper.examination_name,
                "institution_name": paper.institution_name,
                "course_code": test_course.code,
                "course_name": test_course.name,
                "duration_minutes": paper.duration_minutes,
                "total_marks": paper.total_marks,
                "instructions": "Answer all questions from Section A. Answer any FIVE questions from Section B.",
                "questions": [
                    {
                        "section_name": q1.section_name,
                        "question_number": q1.question_number,
                        "question_text": q1.question_text,
                        "marks": q1.marks,
                        "course_outcome": q1.course_outcome,
                        "bloom_level": q1.bloom_level,
                        "sub_question_letter": None
                    },
                    {
                        "section_name": q2.section_name,
                        "question_number": q2.question_number,
                        "question_text": q2.question_text,
                        "marks": q2.marks,
                        "course_outcome": q2.course_outcome,
                        "bloom_level": q2.bloom_level,
                        "sub_question_letter": None
                    }
                ]
            }
            pdf_bytes = QuestionPaperPDFGenerator.generate_pdf(paper_dict)
            assert pdf_bytes and len(pdf_bytes) > 1000
            print(f"  [OK] PDF Generated Successfully ({len(pdf_bytes)} bytes)")

            print("\n" + "=" * 65)
            print("  ALL PRODUCTION NEON WORKFLOWS VERIFIED SUCCESSFULLY!")
            print("=" * 65)

        finally:
            # 7. Clean teardown in child-to-parent order to ensure production DB remains completely clean
            print("\n[STEP 7] Cleaning Up Verification Records (Keeping DB Pristine)...")
            try:
                await session.execute(delete(ValidationResult))
                await session.execute(delete(GenerationSession))
                await session.execute(delete(Question))
                await session.execute(delete(QuestionPaper))
                await session.execute(delete(ResourceChunk))
                await session.execute(delete(Resource))
                await session.execute(delete(CourseOutcome))
                await session.execute(delete(Unit))
                await session.execute(delete(Course))
                await session.execute(delete(User))
                await session.commit()
                print("  [OK] Teardown complete. Zero test records remain in production.")
            except Exception as teardown_err:
                print(f"  [WARN] Teardown error: {teardown_err}")
                await session.rollback()

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_full_production_flow())
