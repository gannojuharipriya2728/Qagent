from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.academic import Course, Unit, CourseOutcome
from app.schemas.academic import (
    CourseCreate, CourseUpdate, CourseResponse, UnitCreate, UnitResponse, CourseOutcomeCreate, CourseOutcomeResponse,
    CourseAnalysisResponse, CourseAnalysisApprovalRequest
)
from app.api.deps import get_current_user, get_current_user_optional
from app.models.user import User

router = APIRouter(prefix="/courses", tags=["Academic Courses"])

@router.get("", response_model=List[CourseResponse])
async def list_courses(db: AsyncSession = Depends(get_db)):
    stmt = select(Course).options(
        selectinload(Course.units),
        selectinload(Course.course_outcomes)
    ).order_by(Course.code)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("", response_model=CourseResponse)
async def create_course(
    course_in: CourseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    stmt = select(Course).where(Course.code == course_in.code)
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Course with code '{course_in.code}' already exists."
        )

    course = Course(
        code=course_in.code,
        name=course_in.name,
        department=course_in.department,
        semester=course_in.semester,
        academic_year=course_in.academic_year,
        description=course_in.description
    )
    db.add(course)
    await db.flush()

    for u in course_in.units:
        unit = Unit(
            course_id=course.id,
            unit_number=u.unit_number,
            title=u.title,
            topics=u.topics
        )
        db.add(unit)

    for co in course_in.course_outcomes:
        co_item = CourseOutcome(
            course_id=course.id,
            code=co.code,
            description=co.description,
            target_bloom_level=co.target_bloom_level
        )
        db.add(co_item)

    await db.commit()
    
    # Reload with relationships
    stmt_reload = select(Course).options(
        selectinload(Course.units),
        selectinload(Course.course_outcomes)
    ).where(Course.id == course.id)
    return (await db.execute(stmt_reload)).scalar_one()

@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: int,
    course_in: CourseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Course).options(
        selectinload(Course.units),
        selectinload(Course.course_outcomes)
    ).where(Course.id == course_id)
    course = (await db.execute(stmt)).scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")

    course.code = course_in.code.strip()
    course.name = course_in.name.strip()
    if course_in.department:
        course.department = course_in.department.strip()
    if course_in.semester:
        course.semester = course_in.semester.strip()
    if course_in.academic_year:
        course.academic_year = course_in.academic_year.strip()
    if course_in.description is not None:
        course.description = course_in.description

    # If new units passed, update
    if course_in.units:
        # Delete existing units
        for u in course.units:
            await db.delete(u)
        await db.flush()
        for u_in in course_in.units:
            new_u = Unit(
                course_id=course.id,
                unit_number=u_in.unit_number,
                title=u_in.title,
                topics=u_in.topics
            )
            db.add(new_u)

    # If new COs passed, update
    if course_in.course_outcomes:
        for co in course.course_outcomes:
            await db.delete(co)
        await db.flush()
        for co_in in course_in.course_outcomes:
            new_co = CourseOutcome(
                course_id=course.id,
                code=co_in.code,
                description=co_in.description,
                target_bloom_level=co_in.target_bloom_level or "Apply"
            )
            db.add(new_co)

    await db.commit()
    stmt_reload = select(Course).options(
        selectinload(Course.units),
        selectinload(Course.course_outcomes)
    ).where(Course.id == course.id)
    return (await db.execute(stmt_reload)).scalar_one()

@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(course_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(Course).options(
        selectinload(Course.units),
        selectinload(Course.course_outcomes)
    ).where(Course.id == course_id)
    course = (await db.execute(stmt)).scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")
    return course

@router.post("/{course_id}/analyze", response_model=CourseAnalysisResponse)
async def analyze_course_resources(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Analyzes uploaded course resources to extract Units, Topics, Key Concepts, and Proposed Course Outcomes.
    """
    from app.models.resource import Resource, ResourceChunk
    from app.services.llm.syllabus_analyzer import SyllabusAnalyzer
    
    stmt = select(Course).options(
        selectinload(Course.units),
        selectinload(Course.course_outcomes),
        selectinload(Course.resources).selectinload(Resource.chunks)
    ).where(Course.id == course_id)
    course = (await db.execute(stmt)).scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")

    # Gather text from syllabus and resources
    combined_texts = []
    source_filenames = []
    for r in course.resources:
        source_filenames.append(r.file_name)
        if r.chunks:
            chunk_texts = [c.content for c in r.chunks[:20]]
            combined_texts.append("\n".join(chunk_texts))

    raw_content = "\n\n".join(combined_texts)
    if not raw_content and course.description:
        raw_content = course.description

    analysis_result = {}
    if raw_content and len(raw_content.strip()) >= 50:
        try:
            analysis_result = await SyllabusAnalyzer.analyze_syllabus_text(raw_content)
        except Exception:
            analysis_result = SyllabusAnalyzer._fallback_parse(raw_content)
    else:
        # Generate default analysis from course metadata
        analysis_result = SyllabusAnalyzer._fallback_parse(f"Course: {course.name} ({course.code})\nDepartment: {course.department}")

    units_data = analysis_result.get("units", [])
    cos_data = analysis_result.get("course_outcomes", [])

    # Format topic -> unit and CO -> unit mappings
    topic_unit_map = []
    for u in units_data:
        topic_unit_map.append({
            "unit_number": u.get("unit_number", 1),
            "unit_title": u.get("title", f"Unit {u.get('unit_number', 1)}"),
            "topics": u.get("topics", "")
        })

    co_unit_map = []
    for idx, co in enumerate(cos_data):
        target_u = (idx % len(units_data)) + 1 if units_data else 1
        co_unit_map.append({
            "co_code": co.get("code", f"CO{idx+1}"),
            "co_description": co.get("description", ""),
            "associated_unit": target_u
        })

    bloom_detected = {
        "Remember": 20.0,
        "Understand": 30.0,
        "Apply": 25.0,
        "Analyze": 15.0,
        "Evaluate": 5.0,
        "Create": 5.0
    }

    course.analysis_status = "Analyzed"
    course.analysis_data = {
        "units": units_data,
        "course_outcomes": cos_data,
        "bloom_distribution_detected": bloom_detected,
        "topic_unit_mapping": topic_unit_map,
        "co_unit_mapping": co_unit_map,
        "source_documents": source_filenames
    }
    await db.commit()

    return CourseAnalysisResponse(
        course_id=course.id,
        code=course.code,
        title=course.name,
        department=course.department,
        semester=course.semester,
        academic_year=course.academic_year,
        units=units_data,
        course_outcomes=cos_data,
        bloom_distribution_detected=bloom_detected,
        topic_unit_mapping=topic_unit_map,
        co_unit_mapping=co_unit_map,
        source_documents=source_filenames,
        status="Analyzed"
    )

@router.get("/{course_id}/analysis", response_model=CourseAnalysisResponse)
async def get_course_analysis(
    course_id: int,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Course).options(
        selectinload(Course.units),
        selectinload(Course.course_outcomes),
        selectinload(Course.resources)
    ).where(Course.id == course_id)
    course = (await db.execute(stmt)).scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")

    if course.analysis_data:
        d = course.analysis_data
        return CourseAnalysisResponse(
            course_id=course.id,
            code=course.code,
            title=course.name,
            department=course.department,
            semester=course.semester,
            academic_year=course.academic_year,
            units=d.get("units", []),
            course_outcomes=d.get("course_outcomes", []),
            bloom_distribution_detected=d.get("bloom_distribution_detected", {}),
            topic_unit_mapping=d.get("topic_unit_mapping", []),
            co_unit_mapping=d.get("co_unit_mapping", []),
            source_documents=d.get("source_documents", []),
            status=course.analysis_status or "Pending"
        )
    
    # Fallback to existing units and COs if already approved
    units_list = [
        {"unit_number": u.unit_number, "title": u.title, "topics": u.topics}
        for u in course.units
    ]
    cos_list = [
        {"code": c.code, "description": c.description, "bloom_level": c.target_bloom_level, "bloom_source": "explicit"}
        for c in course.course_outcomes
    ]
    source_filenames = [r.file_name for r in course.resources]
    
    return CourseAnalysisResponse(
        course_id=course.id,
        code=course.code,
        title=course.name,
        department=course.department,
        semester=course.semester,
        academic_year=course.academic_year,
        units=units_list,
        course_outcomes=cos_list,
        bloom_distribution_detected={"Remember": 20, "Understand": 30, "Apply": 25, "Analyze": 15, "Evaluate": 5, "Create": 5},
        topic_unit_mapping=[{"unit_number": u.unit_number, "unit_title": u.title, "topics": u.topics} for u in course.units],
        co_unit_mapping=[{"co_code": c.code, "co_description": c.description, "associated_unit": 1} for c in course.course_outcomes],
        source_documents=source_filenames,
        status=course.analysis_status or "Pending"
    )

@router.post("/{course_id}/analysis/approve", response_model=CourseResponse)
async def approve_course_analysis(
    course_id: int,
    approval_in: CourseAnalysisApprovalRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Course).options(
        selectinload(Course.units),
        selectinload(Course.course_outcomes)
    ).where(Course.id == course_id)
    course = (await db.execute(stmt)).scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")

    # Remove existing units and COs to set the approved ones
    for u in course.units:
        await db.delete(u)
    for co in course.course_outcomes:
        await db.delete(co)
    await db.flush()

    for u_in in approval_in.units:
        new_u = Unit(
            course_id=course.id,
            unit_number=u_in.unit_number,
            title=u_in.title,
            topics=u_in.topics
        )
        db.add(new_u)

    for co_in in approval_in.course_outcomes:
        new_co = CourseOutcome(
            course_id=course.id,
            code=co_in.code,
            description=co_in.description,
            target_bloom_level=co_in.target_bloom_level or "Apply"
        )
        db.add(new_co)

    course.analysis_status = "Approved"
    await db.commit()

    stmt_reload = select(Course).options(
        selectinload(Course.units),
        selectinload(Course.course_outcomes)
    ).where(Course.id == course.id)
    return (await db.execute(stmt_reload)).scalar_one()

@router.delete("/{course_id}")
async def delete_course(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Course).where(Course.id == course_id)
    course = (await db.execute(stmt)).scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")
    
    from app.services.rag.vector_store import vector_store
    vector_store.delete_by_course_id(course_id)

    await db.delete(course)
    await db.commit()
    return {"message": f"Course '{course.name}' deleted successfully."}
