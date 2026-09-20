# Automated Testing & Verification Suite

## Running Unit and Integration Tests

Run the full pytest suite:
```bash
python -m pytest backend/tests -v
```

### Covered Test Suites:
1. **`test_chunker.py`**:
   - Tests `AcademicChunker` token slicing, sliding window overlap, and automatic topic inference from headings.
2. **`test_vector_store.py`**:
   - Tests embedding generation, vector indexing, metadata filtering by `course_id` and `unit_number`, and top-k retrieval.
3. **`test_validation_agent.py`**:
   - Tests Bloom verb validation, Course Outcome mapping, and cosine repetition / duplicate rejection algorithm.
4. **`test_agent_workflow.py`**:
   - Tests end-to-end execution of the 5-Agent pipeline and ReportLab PDF binary generation with university exam layout.
