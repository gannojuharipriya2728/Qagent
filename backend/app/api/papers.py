import re
import unicodedata
from typing import List, Optional, Dict, Any
from urllib.parse import quote
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.paper import QuestionPaper, Question, ValidationResult
from app.models.academic import Course, Unit, CourseOutcome
from app.schemas.paper import (
    QuestionPaperResponse, QuestionSchema, QuestionUpdateRequest, QuestionRegenerateRequest, PaperAnalyticsResponse
)
from app.api.deps import get_current_user
from app.models.user import User
from app.services.agents.retrieval_agent import RAGRetrievalAgent
from app.services.agents.generation_agent import QuestionGenerationAgent
from app.services.agents.validation_agent import ValidationAgent
from app.services.agents.requirement_agent import PlannedQuestionSlot

import logging
logger = logging.getLogger("qagent.papers")

router = APIRouter(prefix="/papers", tags=["Question Papers"])

@router.get("", response_model=List[QuestionPaperResponse])
async def list_papers(course_id: Optional[int] = None, db: AsyncSession = Depends(get_db)):
    try:
        stmt = select(QuestionPaper).options(
            selectinload(QuestionPaper.course),
            selectinload(QuestionPaper.questions).selectinload(Question.validation_results)
        )
        if course_id:
            stmt = stmt.where(QuestionPaper.course_id == course_id)
        stmt = stmt.order_by(QuestionPaper.created_at.desc())
        
        result = await db.execute(stmt)
        papers = result.scalars().unique().all()
        
        # Format response
        response_list = []
        for p in papers:
            p_dict = {
                "id": p.id,
                "course_id": p.course_id,
                "course_code": p.course.code if p.course else "CS",
                "course_name": p.course.name if p.course else "Course",
                "title": p.title,
                "exam_type": getattr(p, "exam_type", "Semester Examination") or "Semester Examination",
                "examination_name": p.examination_name,
                "institution_name": p.institution_name,
                "duration_minutes": p.duration_minutes,
                "total_marks": p.total_marks,
                "instructions": p.instructions,
                "section_config": getattr(p, "section_config", None),
                "difficulty_distribution": p.difficulty_distribution,
                "bloom_distribution": p.bloom_distribution,
                "syllabus_coverage_score": p.syllabus_coverage_score or 0.0,
                "status": p.status,
                "created_at": p.created_at,
                "questions": []
            }
            for q in p.questions:
                val = q.validation_results[0] if q.validation_results else None
                p_dict["questions"].append({
                    "id": q.id,
                    "section_name": q.section_name,
                    "question_number": q.question_number,
                    "sub_question_letter": q.sub_question_letter,
                    "question_text": q.question_text,
                    "marks": q.marks,
                    "unit_number": q.unit_number,
                    "bloom_level": q.bloom_level,
                    "course_outcome": q.course_outcome,
                    "difficulty": q.difficulty,
                    "question_type": q.question_type,
                    "sub_questions": getattr(q, "sub_questions", None),
                    "source_topics": q.source_topics or [],
                    "source_documents": q.source_documents or [],
                    "generation_reasoning": q.generation_reasoning,
                    "is_revised": q.is_revised,
                    "revision_count": q.revision_count,
                    "validation": {
                        "is_valid": val.is_valid if val else True,
                        "syllabus_alignment_score": getattr(val, "syllabus_alignment_score", 0.9) if val else 0.9,
                        "co_alignment_score": getattr(val, "co_alignment_score", 0.9) if val else 0.9,
                        "difficulty_match_score": getattr(val, "difficulty_match_score", 0.9) if val else 0.9,
                        "bloom_alignment_score": getattr(val, "bloom_alignment_score", 0.9) if val else 0.9,
                        "is_duplicate": getattr(val, "is_duplicate", False) if val else False,
                        "duplicate_similarity_score": getattr(val, "duplicate_similarity_score", 0.0) if val else 0.0,
                        "feedback_notes": getattr(val, "feedback_notes", "Validated") if val else "Validated"
                    }
                })
            response_list.append(p_dict)
        
        return response_list
    except Exception as exc:
        logger.error(f"Error in list_papers: {exc}")
        return []

@router.get("/{paper_id}", response_model=QuestionPaperResponse)
async def get_paper(paper_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(QuestionPaper).options(
        selectinload(QuestionPaper.course),
        selectinload(QuestionPaper.questions).selectinload(Question.validation_results)
    ).where(QuestionPaper.id == paper_id)
    
    paper = (await db.execute(stmt)).scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Question paper not found.")

    p_dict = {
        "id": paper.id,
        "course_id": paper.course_id,
        "course_code": paper.course.code if paper.course else "CS",
        "course_name": paper.course.name if paper.course else "Course",
        "title": paper.title,
        "examination_name": paper.examination_name,
        "institution_name": paper.institution_name,
        "duration_minutes": paper.duration_minutes,
        "total_marks": paper.total_marks,
        "instructions": paper.instructions,
        "difficulty_distribution": paper.difficulty_distribution,
        "bloom_distribution": paper.bloom_distribution,
        "syllabus_coverage_score": paper.syllabus_coverage_score,
        "status": paper.status,
        "created_at": paper.created_at,
        "questions": []
    }
    for q in paper.questions:
        val = q.validation_results[0] if q.validation_results else None
        p_dict["questions"].append({
            "id": q.id,
            "section_name": q.section_name,
            "question_number": q.question_number,
            "sub_question_letter": q.sub_question_letter,
            "question_text": q.question_text,
            "marks": q.marks,
            "unit_number": q.unit_number,
            "bloom_level": q.bloom_level,
            "course_outcome": q.course_outcome,
            "difficulty": q.difficulty,
            "question_type": q.question_type,
            "source_topics": q.source_topics or [],
            "source_documents": q.source_documents or [],
            "generation_reasoning": q.generation_reasoning,
            "is_revised": q.is_revised,
            "revision_count": q.revision_count,
            "validation": {
                "is_valid": val.is_valid if val else True,
                "syllabus_alignment_score": val.syllabus_alignment_score if val else 0.9,
                "co_alignment_score": val.co_alignment_score if val else 0.9,
                "difficulty_match_score": val.difficulty_match_score if val else 0.9,
                "bloom_alignment_score": val.bloom_alignment_score if val else 0.9,
                "is_duplicate": val.is_duplicate if val else False,
                "duplicate_similarity_score": val.duplicate_similarity_score if val else 0.0,
                "feedback_notes": val.feedback_notes if val else "Validated"
            }
        })
    return p_dict

@router.put("/{paper_id}/questions/{question_id}", response_model=QuestionSchema)
async def update_question(
    paper_id: int,
    question_id: int,
    update_in: QuestionUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Question).where(Question.id == question_id, Question.paper_id == paper_id)
    question = (await db.execute(stmt)).scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found in paper.")

    if update_in.question_text is not None:
        question.question_text = update_in.question_text
    if update_in.marks is not None:
        question.marks = update_in.marks
    if update_in.bloom_level is not None:
        question.bloom_level = update_in.bloom_level
    if update_in.course_outcome is not None:
        question.course_outcome = update_in.course_outcome
    if update_in.difficulty is not None:
        question.difficulty = update_in.difficulty

    question.is_revised = True
    await db.commit()
    await db.refresh(question)
    return question

@router.post("/{paper_id}/questions/{question_id}/regenerate", response_model=QuestionSchema)
async def regenerate_single_question(
    paper_id: int,
    question_id: int,
    regen_in: QuestionRegenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Question).where(Question.id == question_id, Question.paper_id == paper_id)
    question = (await db.execute(stmt)).scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found.")

    stmt_paper = select(QuestionPaper).options(selectinload(QuestionPaper.course)).where(QuestionPaper.id == paper_id)
    paper = (await db.execute(stmt_paper)).scalar_one_or_none()

    slot = PlannedQuestionSlot(
        slot_index=question.question_number,
        section_name=question.section_name,
        question_number=question.question_number,
        marks=question.marks,
        unit_number=question.unit_number,
        bloom_level=regen_in.preferred_bloom_level or question.bloom_level,
        course_outcome=question.course_outcome,
        difficulty=regen_in.preferred_difficulty or question.difficulty,
        question_type=question.question_type
    )

    retrieval_res = await RAGRetrievalAgent.retrieve_context_for_slot(
        slot=slot,
        course_id=paper.course_id,
        top_k=6
    )

    new_q_data = await QuestionGenerationAgent.generate_question(
        slot=slot,
        retrieval=retrieval_res,
        course_name=paper.course.name if paper.course else "Course"
    )

    question.question_text = new_q_data["question_text"]
    question.bloom_level = slot.bloom_level
    question.difficulty = slot.difficulty
    question.source_topics = new_q_data.get("source_topics", [])
    question.source_documents = new_q_data.get("source_documents", [])
    question.generation_reasoning = new_q_data.get("reasoning", "") + " (Manually regenerated via UI)"
    question.is_revised = True
    question.revision_count += 1

    await db.commit()
    await db.refresh(question)
    return question

@router.get("/{paper_id}/pdf")
async def export_paper_pdf(paper_id: int, db: AsyncSession = Depends(get_db)):
    from app.services.pdf_generator import QuestionPaperPDFGenerator
    paper_res = await get_paper(paper_id=paper_id, db=db)
    
    pdf_bytes = QuestionPaperPDFGenerator.generate_pdf(paper_res)
    raw_filename = f"{paper_res['course_code']}_{paper_res['title'].replace(' ', '_')}.pdf"

    # HTTP headers are latin-1; titles routinely contain em dashes and other
    # non-ASCII punctuation, which would otherwise raise UnicodeEncodeError while
    # building the response. Send an ASCII-safe name plus the RFC 5987 form that
    # browsers prefer when present.
    ascii_filename = unicodedata.normalize("NFKD", raw_filename).encode("ascii", "ignore").decode("ascii")
    ascii_filename = re.sub(r'[^A-Za-z0-9._-]', "_", ascii_filename).strip("._") or f"question_paper_{paper_id}.pdf"
    if not ascii_filename.lower().endswith(".pdf"):
        ascii_filename += ".pdf"
    encoded_filename = quote(raw_filename, safe="")

    # Persist to Storage Service (Local or S3)
    try:
        from app.services.storage import get_storage_service
        storage_service = get_storage_service()
        pdf_storage_key = f"exports/{paper_id}_{ascii_filename}"
        await storage_service.upload_bytes(pdf_bytes, pdf_storage_key, content_type="application/pdf")
    except Exception:
        logger.warning("Could not persist exported PDF to storage; serving it inline anyway.", exc_info=True)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{ascii_filename}"; '
                f"filename*=UTF-8''{encoded_filename}"
            )
        },
    )

@router.get("/{paper_id}/analytics", response_model=PaperAnalyticsResponse)
async def get_paper_analytics(paper_id: int, db: AsyncSession = Depends(get_db)):
    paper = await get_paper(paper_id=paper_id, db=db)
    questions = paper.get("questions", [])

    total_marks_calc = sum(q.get("marks", 0) for q in questions)
    marks_valid = (total_marks_calc == paper.get("total_marks", 70))

    # Unit Coverage
    unit_counts = {}
    for q in questions:
        u = q.get("unit_number", 1)
        unit_counts[u] = unit_counts.get(u, 0) + 1

    unit_coverage = {}
    for u in range(1, 6):
        unit_coverage[u] = round((unit_counts.get(u, 0) / max(1, len(questions))) * 100.0, 1)

    # Bloom actual
    bloom_counts = {}
    for q in questions:
        b = q.get("bloom_level", "Understand")
        bloom_counts[b] = bloom_counts.get(b, 0) + 1

    bloom_actual = {b: round((cnt / max(1, len(questions))) * 100.0, 1) for b, cnt in bloom_counts.items()}
    
    # Difficulty actual
    diff_counts = {}
    for q in questions:
        d = q.get("difficulty", "Medium")
        diff_counts[d] = diff_counts.get(d, 0) + 1
    
    diff_actual = {d: round((cnt / max(1, len(questions))) * 100.0, 1) for d, cnt in diff_counts.items()}

    # CO distribution
    co_counts = {}
    for q in questions:
        co = q.get("course_outcome", "CO1")
        co_counts[co] = co_counts.get(co, 0) + 1

    return PaperAnalyticsResponse(
        total_questions=len(questions),
        total_marks_calculated=total_marks_calc,
        marks_sum_valid=marks_valid,
        unit_coverage=unit_coverage,
        overall_syllabus_coverage=paper.get("syllabus_coverage_score", 100.0),
        bloom_distribution_actual=bloom_actual,
        bloom_distribution_target=paper.get("bloom_distribution") or {},
        difficulty_distribution_actual=diff_actual,
        difficulty_distribution_target=paper.get("difficulty_distribution") or {},
        co_distribution=co_counts
    )

@router.delete("/{paper_id}")
async def delete_paper(
    paper_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(QuestionPaper).where(QuestionPaper.id == paper_id)
    paper = (await db.execute(stmt)).scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found.")

    await db.delete(paper)
    await db.commit()
    return {"message": "Question paper deleted successfully."}
