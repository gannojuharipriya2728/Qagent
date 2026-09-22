from typing import List, Dict, Any, Optional
from app.schemas.generation import GenerationRequest, SectionRule

class PlannedQuestionSlot:
    def __init__(
        self,
        slot_index: int,
        section_name: str,
        question_number: int,
        marks: int,
        unit_number: int,
        bloom_level: str,
        course_outcome: str,
        difficulty: str,
        question_type: str,
        has_sub_questions: bool = False,
        sub_question_parts: Optional[List[Dict[str, Any]]] = None,
        internal_choice: bool = False,
        choice_note: Optional[str] = None
    ):
        self.slot_index = slot_index
        self.section_name = section_name
        self.question_number = question_number
        self.marks = marks
        self.unit_number = unit_number
        self.bloom_level = bloom_level
        self.course_outcome = course_outcome
        self.difficulty = difficulty
        self.question_type = question_type
        self.has_sub_questions = has_sub_questions
        self.sub_question_parts = sub_question_parts or []
        self.internal_choice = internal_choice
        self.choice_note = choice_note

    def to_dict(self) -> Dict[str, Any]:
        return {
            "slot_index": self.slot_index,
            "section_name": self.section_name,
            "question_number": self.question_number,
            "marks": self.marks,
            "unit_number": self.unit_number,
            "bloom_level": self.bloom_level,
            "course_outcome": self.course_outcome,
            "difficulty": self.difficulty,
            "question_type": self.question_type,
            "has_sub_questions": self.has_sub_questions,
            "sub_question_parts": self.sub_question_parts,
            "internal_choice": self.internal_choice,
            "choice_note": self.choice_note
        }

class RequirementAnalyzerAgent:
    """
    Agent 1: Requirement Analyzer
    Deconstructs faculty examination criteria into structured, balanced question blueprints.
    """
    
    @staticmethod
    def analyze_and_plan(request: GenerationRequest, available_units: List[int], available_cos: List[str]) -> List[PlannedQuestionSlot]:
        # Fallbacks if courses have no predefined units or COs
        units = available_units if available_units else [1, 2, 3, 4, 5]
        cos = available_cos if available_cos else ["CO1", "CO2", "CO3", "CO4", "CO5"]

        # Calculate evaluated total marks = sum(questions_to_answer * marks_per_question)
        calculated_total = sum(s.questions_to_answer * s.marks_per_question for s in request.sections)

        # Prepare Bloom level pool based on distribution
        bloom_levels_order = ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"]
        bloom_pool = []
        for level in bloom_levels_order:
            pct = request.bloom_distribution.get(level, 10.0)
            count = max(1, int(round(pct / 10)))
            bloom_pool.extend([level] * count)

        # Prepare Difficulty pool
        diff_pool = (
            ["Easy"] * int(request.difficulty_distribution.get("Easy", 30.0) / 10) +
            ["Medium"] * int(request.difficulty_distribution.get("Medium", 50.0) / 10) +
            ["Hard"] * int(request.difficulty_distribution.get("Hard", 20.0) / 10)
        )
        if not diff_pool:
            diff_pool = ["Medium", "Easy", "Hard"]

        # Prepare CO pool if configured
        co_pool = []
        if request.co_distribution:
            for co_name, val in request.co_distribution.items():
                count = max(1, int(round(float(val) / 10))) if float(val) > 0 else 1
                co_pool.extend([co_name] * count)
        if not co_pool:
            co_pool = list(cos)

        slots: List[PlannedQuestionSlot] = []
        slot_idx = 0
        q_num = 1

        for sec in request.sections:
            target_units = sec.unit_distribution if sec.unit_distribution else units
            
            for i in range(sec.total_questions):
                assigned_unit = target_units[i % len(target_units)]
                assigned_co = co_pool[slot_idx % len(co_pool)]
                assigned_bloom = bloom_pool[slot_idx % len(bloom_pool)]
                
                # In low mark questions (<= 2M), bias towards Remember/Understand
                if sec.marks_per_question <= 2 and assigned_bloom in ["Evaluate", "Create"]:
                    assigned_bloom = "Remember" if i % 2 == 0 else "Understand"

                # In high mark questions (>= 10M), bias towards Apply/Analyze/Evaluate
                if sec.marks_per_question >= 10 and assigned_bloom == "Remember":
                    assigned_bloom = "Analyze" if i % 2 == 0 else "Apply"

                assigned_diff = diff_pool[slot_idx % len(diff_pool)]

                # Generate default sub-question parts if sub-questions enabled and parts not defined
                sub_parts = None
                if sec.sub_question_parts:
                    sub_parts = [
                        p.model_dump() if hasattr(p, 'model_dump') else (p.dict() if hasattr(p, 'dict') else dict(p))
                        for p in sec.sub_question_parts
                    ]
                elif sec.has_sub_questions:
                    half_marks = max(1, sec.marks_per_question // 2)
                    rem_marks = sec.marks_per_question - half_marks
                    sub_parts = [
                        {"part": "a", "marks": half_marks, "bloom_level": "Understand"},
                        {"part": "b", "marks": rem_marks, "bloom_level": assigned_bloom}
                    ]

                choice_note = None
                if sec.total_questions > sec.questions_to_answer:
                    choice_note = f"Answer any {sec.questions_to_answer} of {sec.total_questions}"

                slots.append(PlannedQuestionSlot(
                    slot_index=slot_idx,
                    section_name=sec.name,
                    question_number=q_num,
                    marks=sec.marks_per_question,
                    unit_number=assigned_unit,
                    bloom_level=assigned_bloom,
                    course_outcome=assigned_co,
                    difficulty=assigned_diff,
                    question_type=sec.question_type,
                    has_sub_questions=sec.has_sub_questions,
                    sub_question_parts=sub_parts,
                    internal_choice=sec.internal_choice,
                    choice_note=choice_note
                ))
                slot_idx += 1
                q_num += 1

        return slots

