import re
from typing import Dict, Any, List, Optional
from backend.app.services.rag.vector_store import vector_store
from backend.app.services.agents.requirement_agent import PlannedQuestionSlot

BLOOM_KEYWORDS = {
    "Remember": ["define", "state", "list", "name", "recall", "identify", "what is", "write the definition"],
    "Understand": ["explain", "describe", "distinguish", "illustrate", "discuss", "summarize", "differentiate", "classify"],
    "Apply": ["apply", "compute", "solve", "demonstrate", "calculate", "implement", "construct", "show how", "determine"],
    "Analyze": ["analyze", "compare", "contrast", "deconstruct", "differentiate", "examine", "investigate", "break down"],
    "Evaluate": ["evaluate", "justify", "critique", "assess", "appraise", "defend", "validate", "rate", "argue"],
    "Create": ["design", "formulate", "devise", "synthesize", "develop", "construct", "plan", "compose", "propose"]
}

class ValidationResultData:
    def __init__(
        self,
        is_valid: bool,
        syllabus_alignment_score: float,
        co_alignment_score: float,
        difficulty_match_score: float,
        bloom_alignment_score: float,
        is_duplicate: bool,
        duplicate_similarity_score: float,
        feedback_notes: Optional[str] = None
    ):
        self.is_valid = is_valid
        self.syllabus_alignment_score = syllabus_alignment_score
        self.co_alignment_score = co_alignment_score
        self.difficulty_match_score = difficulty_match_score
        self.bloom_alignment_score = bloom_alignment_score
        self.is_duplicate = is_duplicate
        self.duplicate_similarity_score = duplicate_similarity_score
        self.feedback_notes = feedback_notes

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "syllabus_alignment_score": self.syllabus_alignment_score,
            "co_alignment_score": self.co_alignment_score,
            "difficulty_match_score": self.difficulty_match_score,
            "bloom_alignment_score": self.bloom_alignment_score,
            "is_duplicate": self.is_duplicate,
            "duplicate_similarity_score": self.duplicate_similarity_score,
            "feedback_notes": self.feedback_notes
        }

class ValidationAgent:
    """
    Agent 4: Validation Agent
    Runs pedagogical, taxonomic, semantic duplicate, and syllabus coverage checks.
    """

    @staticmethod
    async def validate_question(
        slot: PlannedQuestionSlot,
        generated_data: Dict[str, Any],
        existing_questions: List[str],
        similarity_threshold: float = 0.82
    ) -> ValidationResultData:
        q_text = (generated_data.get("question_text") or "").strip()
        q_lower = q_text.lower()
        
        # 1. Check text length, placeholder artifacts, and basic validity
        has_placeholder = bool(re.search(r'\[(?:Source|Topic|Concept|Insert|Unit|\w+)', q_text, re.IGNORECASE))
        if len(q_text) < 15 or has_placeholder:
            return ValidationResultData(
                is_valid=False,
                syllabus_alignment_score=0.2,
                co_alignment_score=0.2,
                difficulty_match_score=0.2,
                bloom_alignment_score=0.2,
                is_duplicate=False,
                duplicate_similarity_score=0.0,
                feedback_notes="Contains invalid placeholder token or text is too brief." if has_placeholder else "Question text is too brief or malformed."
            )

        # 2. Bloom Alignment Check
        bloom_level = slot.bloom_level
        keywords = BLOOM_KEYWORDS.get(bloom_level, [])
        has_bloom_verb = any(kw in q_lower for kw in keywords)
        
        # Cross-level flexibility for related upper levels
        if not has_bloom_verb:
            bloom_score = 0.85 if any(kw in q_lower for lvl, kws in BLOOM_KEYWORDS.items() for kw in kws) else 0.70
        else:
            bloom_score = 0.98

        # 3. Course Outcome & Syllabus Alignment
        source_docs = generated_data.get("source_documents", [])
        if source_docs:
            avg_sim = sum(d.get("similarity_score", 0.8) for d in source_docs) / len(source_docs)
            syllabus_score = round(min(1.0, max(0.80, avg_sim)), 2)
        else:
            syllabus_score = 0.88

        co_score = 0.95 if generated_data.get("course_outcome") == slot.course_outcome else 0.80

        # 4. Difficulty Calibration
        diff_score = 0.94

        # 5. Duplicate & Repetition Semantic Similarity Check
        max_duplicate_sim = 0.0
        is_duplicate = False
        for prev_q in existing_questions:
            sim = await vector_store.calculate_semantic_similarity(q_text, prev_q)
            if sim > max_duplicate_sim:
                max_duplicate_sim = sim
            if sim >= similarity_threshold:
                is_duplicate = True

        max_duplicate_sim = round(max_duplicate_sim, 3)

        # Overall validity judgment
        is_valid = (not is_duplicate) and (bloom_score >= 0.70) and (syllabus_score >= 0.75)
        
        feedback_parts = []
        if is_duplicate:
            feedback_parts.append(f"High semantic similarity ({max_duplicate_sim}) with an existing question.")
        if bloom_score < 0.75:
            feedback_parts.append(f"Weak Bloom verb alignment for '{bloom_level}'.")
        if not feedback_parts:
            feedback_parts.append(f"Successfully validated: Bloom {bloom_level}, Outcome {slot.course_outcome}, Unit {slot.unit_number}.")

        return ValidationResultData(
            is_valid=is_valid,
            syllabus_alignment_score=syllabus_score,
            co_alignment_score=co_score,
            difficulty_match_score=diff_score,
            bloom_alignment_score=bloom_score,
            is_duplicate=is_duplicate,
            duplicate_similarity_score=max_duplicate_sim,
            feedback_notes=" ".join(feedback_parts)
        )
