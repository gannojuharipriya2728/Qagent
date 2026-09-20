# REST API Specification

Base URL: `http://localhost:8000/api`

## Authentication (`/api/auth`)
- `POST /api/auth/register` — Register new faculty user.
- `POST /api/auth/login` — Authenticate and retrieve JWT token.
- `GET /api/auth/me` — Retrieve current authenticated user profile.

## Academic Courses (`/api/courses`)
- `GET /api/courses` — List all courses with units and COs.
- `POST /api/courses` — Create a new course curriculum.
- `GET /api/courses/{id}` — Retrieve detailed course curriculum.
- `DELETE /api/courses/{id}` — Delete course and associated resources.

## Academic Resources & RAG (`/api/resources`)
- `GET /api/resources` — List uploaded resources with processing status.
- `POST /api/resources/upload` — Upload PDF/DOCX/TXT file, trigger chunking and vector indexing.
- `GET /api/resources/{id}` — Retrieve resource metadata and chunk breakdown.
- `DELETE /api/resources/{id}` — Delete resource and purge vectors.

## Agentic Generation (`/api/generate`)
- `POST /api/generate` — Execute the 5-Agent pipeline and return session logs.

## Question Papers (`/api/papers`)
- `GET /api/papers` — List generated question papers.
- `GET /api/papers/{id}` — Retrieve question paper with questions and explainability sources.
- `PUT /api/papers/{paper_id}/questions/{question_id}` — Inline update of question text, marks, or Bloom level.
- `POST /api/papers/{paper_id}/questions/{question_id}/regenerate` — Regenerate question using Agent 3.
- `GET /api/papers/{id}/pdf` — Export professional university question paper PDF.
- `GET /api/papers/{id}/analytics` — Get syllabus coverage, Bloom distribution, and CO breakdown.
- `DELETE /api/papers/{id}` — Delete question paper.

## Administration (`/api/admin`)
- `GET /api/admin/stats` — System health and vector store metrics.
- `GET /api/admin/users` — List registered evaluators.
- `PATCH /api/admin/users/{id}/toggle-status` — Toggle user activation status.
