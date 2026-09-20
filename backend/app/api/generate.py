from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.schemas.generation import GenerationRequest, GenerationSessionResponse
from backend.app.services.agents.orchestrator import AgenticGenerationOrchestrator
from backend.app.api.deps import get_current_user_optional
from backend.app.models.user import User

router = APIRouter(prefix="/generate", tags=["Agentic Generation"])

@router.post("", response_model=GenerationSessionResponse)
async def generate_question_paper(
    request: GenerationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
):
    user_id = current_user.id if current_user else None
    
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
