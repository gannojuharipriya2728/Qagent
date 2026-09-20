from typing import List, Dict, Any
from backend.app.schemas.generation import GenerationRequest

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
        question_type: str
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
            "question_type": self.question_type
        }

class RequirementAnalyzerAgent:
    """
    Agent 1: Requirement Analyzer
    Deconstructs user examination criteria into structured, balanced question blueprints.
    """
    
    @staticmethod
    def analyze_and_plan(request: GenerationRequest, available_units: List[int], available_cos: List[str]) -> List[PlannedQuestionSlot]:
        # Fallbacks if courses have no predefined units or COs
        units = available_units if available_units else [1, 2, 3, 4, 5]
        cos = available_cos if available_cos else ["CO1", "CO2", "CO3", "CO4", "CO5"]

        # Validate section marks match total marks
        calculated_total = sum(s.questions_to_answer * s.marks_per_question for s in request.sections)
        if calculated_total != request.total_marks:
            # Adjust total marks if mismatched
            pass

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

        slots: List[PlannedQuestionSlot] = []
        slot_idx = 0
        q_num = 1

        for sec in request.sections:
            target_units = sec.unit_distribution if sec.unit_distribution else units
            
            for i in range(sec.total_questions):
                assigned_unit = target_units[i % len(target_units)]
                assigned_co = cos[i % len(cos)]
                assigned_bloom = bloom_pool[slot_idx % len(bloom_pool)]
                
                # In Section A (low marks short questions), bias towards Remember/Understand
                if sec.marks_per_question <= 2 and assigned_bloom in ["Evaluate", "Create"]:
                    assigned_bloom = "Remember" if i % 2 == 0 else "Understand"

                # In Section B (high marks descriptive), bias towards Apply/Analyze/Evaluate
                if sec.marks_per_question >= 10 and assigned_bloom == "Remember":
                    assigned_bloom = "Analyze" if i % 2 == 0 else "Apply"

                assigned_diff = diff_pool[slot_idx % len(diff_pool)]

                slots.append(PlannedQuestionSlot(
                    slot_index=slot_idx,
                    section_name=sec.name,
                    question_number=q_num,
                    marks=sec.marks_per_question,
                    unit_number=assigned_unit,
                    bloom_level=assigned_bloom,
                    course_outcome=assigned_co,
                    difficulty=assigned_diff,
                    question_type=sec.question_type
                ))
                slot_idx += 1
                q_num += 1

        return slots
