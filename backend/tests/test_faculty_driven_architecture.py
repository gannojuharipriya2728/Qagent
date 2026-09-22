import pytest
from app.schemas.generation import GenerationRequest, SectionRule, SubQuestionPart
from app.services.agents.requirement_agent import RequirementAnalyzerAgent, PlannedQuestionSlot
from app.services.pdf_generator import QuestionPaperPDFGenerator
from app.services.agents.validation_agent import ValidationAgent

@pytest.mark.asyncio
async def test_mid_examination_marks_calculation():
    """
    CRITICAL TEST 1:
    Exam: Mid Examination
    Section A: Questions provided = 5, Questions to attempt = 4, Marks/question = 5.
    Calculated evaluated total MUST be 20 Marks (NOT 25 Marks).
    """
    sec_a = SectionRule(
        name="Section A",
        total_questions=5,
        questions_to_answer=4,
        marks_per_question=5,
        question_type="Descriptive / Analytical",
        internal_choice=True
    )
    req = GenerationRequest(
        course_id=1,
        title="Mid Subjective Examination",
        examination_name="Mid-I Examination 2026",
        exam_type="Mid-I",
        institution_name="Department of Computer Science & Engineering",
        duration_minutes=60,
        total_marks=20,
        sections=[sec_a]
    )

    # Section evaluated marks
    sec_evaluated = sec_a.questions_to_answer * sec_a.marks_per_question
    assert sec_evaluated == 20, f"Expected 20 evaluated marks, got {sec_evaluated}"

    # Plan slots with RequirementAnalyzerAgent
    slots = RequirementAnalyzerAgent.analyze_and_plan(
        request=req,
        available_units=[1, 2],
        available_cos=["CO1", "CO2"]
    )
    
    # 5 candidate question slots are planned
    assert len(slots) == 5
    # Every slot carries 5 marks
    for slot in slots:
        assert slot.marks == 5
        assert slot.internal_choice is True


@pytest.mark.asyncio
async def test_multi_section_70_mark_calculation():
    """
    CRITICAL TEST 2:
    Section A: 5 provided, 4 attempted, 5 marks each -> 20 Marks
    Section B: 6 provided, 5 attempted, 10 marks each -> 50 Marks
    Grand Total = 20 + 50 = 70 Marks.
    """
    sec_a = SectionRule(
        name="Section A",
        total_questions=5,
        questions_to_answer=4,
        marks_per_question=5,
        question_type="Short / Conceptual",
        internal_choice=True
    )
    sec_b = SectionRule(
        name="Section B",
        total_questions=6,
        questions_to_answer=5,
        marks_per_question=10,
        question_type="Descriptive",
        internal_choice=True
    )
    req = GenerationRequest(
        course_id=1,
        title="End Semester Examination",
        examination_name="Semester Examination 2026",
        exam_type="Semester Examination",
        institution_name="Department of Information Technology",
        duration_minutes=180,
        total_marks=70,
        sections=[sec_a, sec_b]
    )

    grand_total = sum(s.questions_to_answer * s.marks_per_question for s in req.sections)
    assert grand_total == 70, f"Expected 70 marks, got {grand_total}"

    slots = RequirementAnalyzerAgent.analyze_and_plan(
        request=req,
        available_units=[1, 2],
        available_cos=["CO1", "CO2"]
    )
    # Total planned slots = 5 + 6 = 11
    assert len(slots) == 11


@pytest.mark.asyncio
async def test_custom_examination_marks_calculation():
    """
    CRITICAL TEST 3:
    Custom Examination:
    8 provided, 6 attempted, 4 marks each.
    Calculated total = 6 * 4 = 24 Marks.
    """
    sec = SectionRule(
        name="Section 1",
        total_questions=8,
        questions_to_answer=6,
        marks_per_question=4,
        question_type="Analytical",
        internal_choice=True
    )
    req = GenerationRequest(
        course_id=2,
        title="Continuous Assessment",
        examination_name="Custom Assessment 2026",
        exam_type="Custom Examination",
        institution_name="CSE Department",
        duration_minutes=90,
        total_marks=24,
        sections=[sec]
    )

    evaluated_marks = sec.questions_to_answer * sec.marks_per_question
    assert evaluated_marks == 24

    slots = RequirementAnalyzerAgent.analyze_and_plan(
        request=req,
        available_units=[1],
        available_cos=["CO1"]
    )
    assert len(slots) == 8


@pytest.mark.asyncio
async def test_sub_question_structure_planning():
    """
    Test sub-question structures:
    Q1: Part A (3 Marks) + Part B (2 Marks) = 5 Marks.
    """
    sub_parts = [
        SubQuestionPart(part="a", marks=3),
        SubQuestionPart(part="b", marks=2)
    ]
    sec = SectionRule(
        name="Section A",
        total_questions=2,
        questions_to_answer=2,
        marks_per_question=5,
        has_sub_questions=True,
        sub_question_parts=sub_parts,
        question_type="Descriptive"
    )
    req = GenerationRequest(
        course_id=1,
        title="Mid Exam with Sub-questions",
        examination_name="Mid-I Examination",
        exam_type="Mid-I",
        institution_name="IT Dept",
        duration_minutes=60,
        total_marks=10,
        sections=[sec]
    )

    slots = RequirementAnalyzerAgent.analyze_and_plan(
        request=req,
        available_units=[1],
        available_cos=["CO1"]
    )
    assert len(slots) == 2
    for slot in slots:
        assert slot.has_sub_questions is True
        assert len(slot.sub_question_parts) == 2
        sum_parts = sum(p["marks"] for p in slot.sub_question_parts)
        assert sum_parts == slot.marks == 5


@pytest.mark.asyncio
async def test_pdf_generation_dynamic_exam():
    """
    Test PDF generator with dynamic exam metadata and sub-questions.
    """
    paper_payload = {
        "title": "Information Security Mid Subjective Exam",
        "examination_name": "Mid-I Subjective Examination 2026",
        "exam_type": "Mid-I",
        "institution_name": "Department of Information Technology",
        "course_code": "IT701PC",
        "course_name": "Information Security",
        "duration_minutes": 60,
        "total_marks": 20,
        "instructions": "Answer any FOUR questions out of FIVE. Draw neat diagrams wherever required.",
        "questions": [
            {
                "section_name": "Section A",
                "question_number": 1,
                "question_text": "Explain classical encryption techniques with examples.",
                "marks": 5,
                "course_outcome": "CO1",
                "bloom_level": "Understand",
                "sub_questions": [
                    {"part": "a", "question_text": "Define Caesar cipher and give an example.", "marks": 3},
                    {"part": "b", "question_text": "Differentiate between substitution and transposition ciphers.", "marks": 2}
                ]
            },
            {
                "section_name": "Section A",
                "question_number": 2,
                "question_text": "Discuss AES architecture and key expansion round functions.",
                "marks": 5,
                "course_outcome": "CO2",
                "bloom_level": "Apply"
            }
        ]
    }

    pdf_bytes = QuestionPaperPDFGenerator.generate_pdf(paper_payload)
    assert pdf_bytes is not None
    assert len(pdf_bytes) > 500
    assert pdf_bytes.startswith(b"%PDF")


@pytest.mark.asyncio
async def test_validation_agent_grounding_and_duplicate():
    """
    Test Question Validation Agent against syllabus alignment and duplication.
    """
    slot = PlannedQuestionSlot(
        slot_index=1,
        section_name="Section A",
        question_number=1,
        marks=5,
        unit_number=1,
        bloom_level="Understand",
        course_outcome="CO1",
        difficulty="Medium",
        question_type="Descriptive"
    )

    generated = {
        "question_text": "Explain symmetric and asymmetric encryption algorithms and compare their key distribution mechanisms.",
        "course_outcome": "CO1",
        "source_documents": [{"similarity_score": 0.88, "topic": "Cryptography"}]
    }

    validation = await ValidationAgent.validate_question(
        slot=slot,
        generated_data=generated,
        existing_questions=[]
    )
    assert validation.is_valid is True
    assert validation.is_duplicate is False

    # Duplication check
    dup_validation = await ValidationAgent.validate_question(
        slot=slot,
        generated_data=generated,
        existing_questions=["Explain symmetric and asymmetric encryption algorithms and compare their key distribution mechanisms."],
        similarity_threshold=0.85
    )
    assert dup_validation.is_duplicate is True
    assert dup_validation.is_valid is False
