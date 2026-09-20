import pytest
from backend.app.services.agents.validation_agent import ValidationAgent
from backend.app.services.agents.requirement_agent import PlannedQuestionSlot

@pytest.mark.asyncio
async def test_validation_agent_valid_and_duplicate():
    slot = PlannedQuestionSlot(
        slot_index=1,
        section_name="Section A",
        question_number=1,
        marks=2,
        unit_number=1,
        bloom_level="Remember",
        course_outcome="CO1",
        difficulty="Easy",
        question_type="Short"
    )

    valid_q = {
        "question_text": "Define asymptotic notations and state the difference between Big-O and Theta.",
        "course_outcome": "CO1",
        "source_documents": [{"similarity_score": 0.92}]
    }

    res = await ValidationAgent.validate_question(
        slot=slot,
        generated_data=valid_q,
        existing_questions=[]
    )
    assert res.is_valid is True
    assert res.bloom_alignment_score >= 0.8
    assert res.is_duplicate is False

    # Test duplicate detection
    res_dup = await ValidationAgent.validate_question(
        slot=slot,
        generated_data=valid_q,
        existing_questions=["Define asymptotic notations and state the difference between Big-O and Theta."],
        similarity_threshold=0.80
    )
    assert res_dup.is_duplicate is True
    assert res_dup.is_valid is False
