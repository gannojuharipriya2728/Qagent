from typing import Dict, Any, List, Optional
from backend.app.services.agents.requirement_agent import PlannedQuestionSlot
from backend.app.services.agents.retrieval_agent import RAGRetrievalAgent, RetrievalResult
from backend.app.services.agents.generation_agent import QuestionGenerationAgent
from backend.app.services.agents.validation_agent import ValidationAgent, ValidationResultData

class RevisionAgent:
    """
    Agent 5: Revision Agent
    Performs targeted repair, retrieves fresh context if necessary, and re-validates.
    """

    @staticmethod
    async def revise_question(
        slot: PlannedQuestionSlot,
        previous_data: Dict[str, Any],
        validation_result: ValidationResultData,
        course_id: int,
        course_name: str,
        unit_topics: Optional[str],
        existing_questions: List[str],
        attempt_number: int = 1,
        override_provider: Optional[str] = None
    ) -> tuple[Dict[str, Any], ValidationResultData]:
        # 1. Retrieve alternative context chunks
        new_retrieval = await RAGRetrievalAgent.retrieve_context_for_slot(
            slot=slot,
            course_id=course_id,
            unit_topics=unit_topics,
            top_k=7
        )

        # 2. Modify slot slightly if duplicate to explore complementary topics
        revised_data = await QuestionGenerationAgent.generate_question(
            slot=slot,
            retrieval=new_retrieval,
            course_name=course_name,
            override_provider=override_provider
        )

        revised_data["is_revised"] = True
        revised_data["revision_count"] = attempt_number
        revised_data["reasoning"] += f" (Revised in attempt #{attempt_number} due to: {validation_result.feedback_notes})"

        # 3. Re-validate
        new_validation = await ValidationAgent.validate_question(
            slot=slot,
            generated_data=revised_data,
            existing_questions=existing_questions
        )

        return revised_data, new_validation
