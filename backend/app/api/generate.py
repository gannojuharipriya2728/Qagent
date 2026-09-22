from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.generation import GenerationRequest, GenerationSessionResponse
from app.services.agents.orchestrator import AgenticGenerationOrchestrator
from app.api.deps import get_current_user_optional
from app.models.user import User

router = APIRouter(prefix="/generate", tags=["Agentic Generation"])

@router.post("", response_model=GenerationSessionResponse)
async def generate_question_paper(
    request: GenerationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
):
    user_id = current_user.id if current_user else None

    # Server-Side Marks & Section Pattern Validation
    if not request.sections or len(request.sections) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one examination section must be defined."
        )

    for sec in request.sections:
        if sec.total_questions < sec.questions_to_answer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{sec.name}: Questions provided ({sec.total_questions}) cannot be less than questions to attempt ({sec.questions_to_answer})."
            )
        if sec.marks_per_question <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{sec.name}: Marks per question must be greater than 0."
            )

    calculated_marks = sum(s.questions_to_answer * s.marks_per_question for s in request.sections)
    if request.total_marks != calculated_marks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Marks mismatch. Expected: {request.total_marks}, Calculated from sections: {calculated_marks}."
        )
    
    try:
        paper, steps_log, duration = await AgenticGenerationOrchestrator.run_pipeline(
            db=db,
            request=request,
            user_id=user_id
        )

        return GenerationSessionResponse(
            session_id=paper.id,
            paper_id=paper.id,
            status="Completed",
            duration_seconds=duration,
            steps_log=steps_log
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agentic question generation failed: {str(e)}"
        )
