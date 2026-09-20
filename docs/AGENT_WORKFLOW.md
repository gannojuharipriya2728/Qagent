# Multi-Agent Workflow Engine

## 1. Agent Design Principles
The system rejects single-prompt LLM wrappers in favor of a **5-Agent Autonomous Pipeline** with separation of concerns:

```
[Requirement Agent] ──> [Retrieval Agent] ──> [Generation Agent] ──> [Validation Agent]
                                                    ▲                      │
                                                    │ (Invalid)            │ (Valid)
                                                    └─── [Revision Agent] ─┴──> [Final Paper]
```

---

## 2. Detailed Agent Specifications

### Agent 1: Requirement Analyzer (`requirement_agent.py`)
- **Input**: User exam parameters (Total Marks, Sections, Questions per Section, Target Bloom levels, Target COs, Difficulty splits).
- **Processing**:
  - Validates section formula: $\sum (\text{questions} \times \text{marks}) = \text{total marks}$.
  - Allocates Bloom levels proportionally across sections.
  - Distributes Course Outcomes (CO1 to CO5) across units.
- **Output**: Array of `PlannedQuestionSlot` objects.

### Agent 2: RAG Retrieval Agent (`retrieval_agent.py`)
- **Input**: `PlannedQuestionSlot` (unit number, bloom level, course ID, target topic).
- **Processing**:
  - Queries vector store with metadata filter on `course_id` and `unit_number`.
  - Performs top-k cosine similarity search.
  - Formats retrieved chunks with document citations, page numbers, and similarity scores.
- **Output**: `RetrievalResult` (assembled context + source provenance list).

### Agent 3: Question Generation Agent (`generation_agent.py`)
- **Input**: Question slot metadata and retrieved context citations.
- **Processing**:
  - Selects Bloom cognitive action verbs matching the target level (e.g., *Remember: Define/State; Understand: Explain/Distinguish; Apply: Compute/Implement; Analyze: Analyze/Compare; Evaluate: Justify/Critique; Create: Design/Formulate*).
  - Formats multi-part questions for high-mark descriptive slots (e.g. (a) and (b)).
- **Output**: Structured question data with grounding rationale.

### Agent 4: Validation Agent (`validation_agent.py`)
- **Input**: Generated question text, slot constraints, and all previously accepted questions in the paper.
- **Processing**:
  - Taxonomic action verb validation.
  - Syllabus context grounding check.
  - **Duplicate & Repetition Detection**: Computes token overlap and vector cosine similarity. Questions with similarity $> 0.82$ against previous questions are flagged as duplicates.
- **Output**: `ValidationResultData` with individual scores (`syllabus_alignment`, `bloom_alignment`, `co_alignment`, `is_duplicate`).

### Agent 5: Revision Agent (`revision_agent.py`)
- **Input**: Failed question data and validation feedback notes.
- **Processing**:
  - Broadens context retrieval with higher top-k or alternative unit topics.
  - Injects repair constraints into the generation prompt.
  - Re-evaluates question with Agent 4 up to `MAX_REVISION_ATTEMPTS = 3`.
- **Output**: Revised, validated question with incremented revision counter.
