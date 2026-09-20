import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.database import Base
from app.core.seed import seed_database
from app.schemas.generation import GenerationRequest, SectionRule
from app.services.agents.orchestrator import AgenticGenerationOrchestrator
from app.services.pdf_generator import QuestionPaperPDFGenerator

@pytest.mark.asyncio
async def test_full_agentic_workflow_and_pdf():
    # In-memory test db
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        await seed_database(session)

        req = GenerationRequest(
            course_id=1,
            title="Mid-Term Examination 2026",
            examination_name="University Mid-Semester Exam",
            institution_name="Department of Computer Science & Engineering",
            duration_minutes=120,
            total_marks=30,
            sections=[
                SectionRule(name="Section A", total_questions=5, questions_to_answer=5, marks_per_question=2, question_type="Short"),
                SectionRule(name="Section B", total_questions=2, questions_to_answer=2, marks_per_question=10, question_type="Descriptive")
            ]
        )

        paper, steps_log, duration = await AgenticGenerationOrchestrator.run_pipeline(
            db=session,
            request=req,
            override_provider="deterministic"
        )

        assert paper is not None
        assert paper.id is not None
        assert len(paper.questions) == 7
        assert sum(q.marks for q in paper.questions) == 30
        assert len(steps_log) >= 5
        assert paper.syllabus_coverage_score > 0

        # Test PDF generator with this generated paper
        paper_dict = {
            "title": paper.title,
            "examination_name": paper.examination_name,
            "institution_name": paper.institution_name,
            "course_code": "CS301",
            "course_name": "Data Structures & Algorithms",
            "duration_minutes": paper.duration_minutes,
            "total_marks": paper.total_marks,
            "instructions": paper.instructions,
            "questions": [
                {
                    "section_name": q.section_name,
                    "question_number": q.question_number,
                    "question_text": q.question_text,
                    "marks": q.marks,
                    "course_outcome": q.course_outcome,
                    "bloom_level": q.bloom_level
                }
                for q in paper.questions
            ]
        }

        pdf_bytes = QuestionPaperPDFGenerator.generate_pdf(paper_dict)
        assert len(pdf_bytes) > 1000
        assert pdf_bytes.startswith(b"%PDF")

@pytest.mark.asyncio
async def test_create_custom_course_and_generate_paper():
    from app.schemas.academic import CourseCreate, UnitCreate, CourseOutcomeCreate
    from app.models.academic import Course, Unit, CourseOutcome

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Create new course
        course_in = CourseCreate(
            code="CS501",
            name="Operating Systems & Concurrency",
            department="Computer Science & Engineering",
            semester="Semester V",
            academic_year="2025-2026",
            description="Process management, scheduling, and concurrency control.",
            units=[
                UnitCreate(unit_number=1, title="Processes and CPU Scheduling", topics="Process State, PCB, Scheduling Algorithms (FCFS, Round Robin, SJF)."),
                UnitCreate(unit_number=2, title="Synchronization & Deadlocks", topics="Critical Section, Semaphores, Banker's Algorithm."),
            ],
            course_outcomes=[
                CourseOutcomeCreate(code="CO1", description="Understand process management and state models.", target_bloom_level="Understand"),
                CourseOutcomeCreate(code="CO2", description="Compute CPU scheduling turnarounds and apply Banker's algorithm.", target_bloom_level="Apply"),
            ]
        )

        course = Course(
            code=course_in.code,
            name=course_in.name,
            department=course_in.department,
            semester=course_in.semester,
            academic_year=course_in.academic_year,
            description=course_in.description
        )
        session.add(course)
        await session.flush()

        for u in course_in.units:
            unit = Unit(
                course_id=course.id,
                unit_number=u.unit_number,
                title=u.title,
                topics=u.topics
            )
            session.add(unit)

        for co in course_in.course_outcomes:
            co_item = CourseOutcome(
                course_id=course.id,
                code=co.code,
                description=co.description,
                target_bloom_level=co.target_bloom_level
            )
            session.add(co_item)

        await session.commit()
        await session.refresh(course)

        assert course.id is not None
        assert course.code == "CS501"

        # Now generate a question paper for this new course
        gen_req = GenerationRequest(
            course_id=course.id,
            title="Operating Systems Semester Assessment",
            examination_name="Mid-Term Regular Examination",
            institution_name="Department of Computer Science & Engineering",
            duration_minutes=90,
            total_marks=20,
            sections=[
                SectionRule(name="Section A", total_questions=5, questions_to_answer=5, marks_per_question=2, question_type="Short", unit_distribution=[1, 2]),
                SectionRule(name="Section B", total_questions=1, questions_to_answer=1, marks_per_question=10, question_type="Descriptive", unit_distribution=[1, 2])
            ],
            target_course_outcomes=["CO1", "CO2"]
        )

        paper, steps_log, duration = await AgenticGenerationOrchestrator.run_pipeline(
            db=session,
            request=gen_req,
            override_provider="deterministic"
        )

        assert paper is not None
        assert paper.course_id == course.id
        assert len(paper.questions) == 6
        assert sum(q.marks for q in paper.questions) == 20
        assert all(q.unit_number in [1, 2] for q in paper.questions)
        assert all(q.course_outcome in ["CO1", "CO2"] for q in paper.questions)

@pytest.mark.asyncio
async def test_it701pc_information_security_course_isolation_and_flow():
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.models.academic import Course

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        await seed_database(session)

        # 1. Fetch IT701PC and verify structure
        stmt = select(Course).options(
            selectinload(Course.units),
            selectinload(Course.course_outcomes)
        ).where(Course.code == "IT701PC")
        course = (await session.execute(stmt)).scalar_one_or_none()

        assert course is not None, "IT701PC must exist in the database"
        assert course.name == "Information Security"
        assert course.semester == "IV Year I Semester"
        assert len(course.units) == 5, "Must have exactly 5 units"
        
        # Verify Unit titles and topics
        unit_1 = next(u for u in course.units if u.unit_number == 1)
        assert "Security Attacks" in unit_1.topics or "Classical Encryption" in unit_1.topics
        
        unit_2 = next(u for u in course.units if u.unit_number == 2)
        assert "RSA" in unit_2.topics or "Public Key" in unit_2.topics

        # Verify only official CO1, CO2, CO3 exist
        co_codes = [co.code for co in course.course_outcomes]
        assert co_codes == ["CO1", "CO2", "CO3"], f"Expected exactly ['CO1', 'CO2', 'CO3'], got {co_codes}"

        # 2. Generate Question Paper for IT701PC
        gen_req = GenerationRequest(
            course_id=course.id,
            title="University Semester End Examination",
            examination_name="End Semester Regular Examination 2026",
            institution_name="Department of Information Technology",
            duration_minutes=180,
            total_marks=30,
            instructions="Answer all questions in Section A and Section B.",
            sections=[
                SectionRule(name="Section A", total_questions=5, questions_to_answer=5, marks_per_question=2, question_type="Short"),
                SectionRule(name="Section B", total_questions=2, questions_to_answer=2, marks_per_question=10, question_type="Descriptive")
            ],
            difficulty_distribution={"Easy": 30, "Medium": 50, "Hard": 20},
            bloom_distribution={"Remember": 20, "Understand": 30, "Apply": 25, "Analyze": 15, "Evaluate": 5, "Create": 5},
            target_course_outcomes=["CO1", "CO2", "CO3"]
        )

        paper, steps_log, duration = await AgenticGenerationOrchestrator.run_pipeline(
            db=session,
            request=gen_req,
            override_provider="deterministic"
        )

        # 3. Assertions on generated paper
        assert paper is not None
        assert paper.course_id == course.id
        assert len(paper.questions) == 7
        assert sum(q.marks for q in paper.questions) == 30

        # Validate that no questions have CO4 or CO5
        for q in paper.questions:
            assert q.course_outcome in ["CO1", "CO2", "CO3"], f"Question {q.question_number} has invalid CO: {q.course_outcome}"
            
            # Verify RAG citations belong ONLY to IT701PC
            for doc in q.source_documents:
                assert doc.get("course_id") == course.id or doc.get("course_code") == "IT701PC", (
                    f"RAG Leakage detected! Citation belongs to {doc.get('course_code')} instead of IT701PC"
                )

            # Verify no cross-course contamination with DSA concepts
            q_text_lower = q.question_text.lower()
            forbidden_terms = ["avl tree", "dijkstra", "b-tree", "linked list", "binary search tree", "relational algebra", "sql schema"]
            for term in forbidden_terms:
                assert term not in q_text_lower, f"Cross-course contamination found: '{term}' in question '{q.question_text}'"


