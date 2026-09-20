# Database Schema Specification

The application uses SQLAlchemy 2.0 with asynchronous SQLite (`aiosqlite`).

## Entity-Relationship Models

```
┌─────────────┐       ┌─────────────┐       ┌─────────────────┐
│    User     │       │   Course    │◄──────┤      Unit       │
├─────────────┤       ├─────────────┤       ├─────────────────┤
│ id          │       │ id          │       │ id              │
│ email       │       │ code        │       │ course_id (FK)  │
│ full_name   │       │ name        │       │ unit_number     │
│ role        │       │ department  │       │ title           │
│ is_active   │       │ semester    │       │ topics          │
└──────┬──────┘       └──────┬──────┘       └─────────────────┘
       │                     │
       │              ┌──────┴──────┐       ┌─────────────────┐
       │              │  Resource   │◄──────┤  ResourceChunk  │
       │              ├─────────────┤       ├─────────────────┤
       │              │ id          │       │ id              │
       │              │ course_id   │       │ resource_id(FK) │
       │              │ file_name   │       │ content         │
       │              │ doc_type    │       │ page_number     │
       │              │ chunk_count │       │ topic           │
       │              │ status      │       │ token_count     │
       │              └─────────────┘       └─────────────────┘
       │                     │
       ▼                     ▼
┌───────────────────────────────────┐
│           QuestionPaper           │
├───────────────────────────────────┤
│ id                                │
│ course_id (FK)                    │
│ created_by (FK)                   │
│ title, exam_name, institution     │
│ total_marks, duration_minutes     │
│ difficulty_dist, bloom_dist       │
│ syllabus_coverage_score           │
└─────────────────┬─────────────────┘
                  │
                  ▼
┌───────────────────────────────────┐       ┌─────────────────┐
│             Question              │◄──────┤ ValidationResult│
├───────────────────────────────────┤       ├─────────────────┤
│ id                                │       │ id              │
│ paper_id (FK)                     │       │ question_id(FK) │
│ section_name                      │       │ is_valid        │
│ question_number                   │       │ syllabus_score  │
│ question_text                     │       │ bloom_score     │
│ marks, unit_number                │       │ co_score        │
│ bloom_level, course_outcome       │       │ is_duplicate    │
│ difficulty, source_documents (JSON│       │ feedback_notes  │
│ generation_reasoning              │       └─────────────────┘
└───────────────────────────────────┘
```
