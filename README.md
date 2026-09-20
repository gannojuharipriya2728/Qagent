# QAgent — Agentic AI-Based Question Generator Using RAG

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.6-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19.2-61DAFB?logo=react)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-6.0-3178C6?logo=typescript)](https://www.typescriptlang.org)
[![Vector RAG](https://img.shields.io/badge/RAG-VectorStore%202.0-blue)](https://fastapi.tiangolo.com)
[![Tests](https://img.shields.io/badge/Pytest-Passing-success)](https://pytest.org)

An enterprise-grade, academic major project designed to autonomously formulate, validate, calibrate, and export structured descriptive university-level examination question papers.

---

## 📌 Problem Statement & Objectives

Traditional university examination question paper preparation is manual, time-consuming, and prone to:
1. **Uneven Syllabus Coverage**: Skewed question weightage ignoring critical curriculum units.
2. **Cognitive Imbalance**: Misalignment with **Bloom's Taxonomy** levels (over-reliance on lower-order rote memory).
3. **Course Outcome Disconnect**: Failure to map questions directly to target **Course Outcomes (CO1-CO5)** required for accreditation (NBA / NAAC).
4. **Repetitive & Duplicate Questions**: Recycled questions with identical semantic structure.
5. **Lack of Grounding**: Unverified questions testing concepts not present in designated textbooks or syllabi.

### System Solution
This system implements a **5-Agent Autonomous Workflow** powered by an explainable **Retrieval-Augmented Generation (RAG)** pipeline.

---

## 🏛️ System Architecture

```
Academic Resources (PDF, DOCX, TXT)
        │
        ▼
[Document Processing & Cleaning]
        │
        ▼
[Semantic Sliding Chunking + Metadata Enrichment]
        │
        ▼
[Vector Database & Embeddings Store]
        │
        ▼
User Exam Configuration (Course, Units, Marks, Bloom, COs, Difficulty)
        │
        ▼
┌────────────────────────────────────────────────────────┐
│               5-STEP AGENTIC AI WORKFLOW               │
│                                                        │
│  [Agent 1: Requirement Analyzer]                      │
│        │ (Deconstructs blueprint & section quotas)     │
│        ▼                                               │
│  [Agent 2: Retrieval Agent]                            │
│        │ (Metadata-filtered Top-K vector retrieval)    │
│        ▼                                               │
│  [Agent 3: Question Generation Agent]                  │
│        │ (Grounds generation in retrieved academic text)│
│        ▼                                               │
│  [Agent 4: Validation Agent]                          │
│        │ (Bloom, CO, Difficulty, Duplicate & Sum Check)│
│        ├─────────────────────────────┐                 │
│        │ Valid                       │ Invalid         │
│        ▼                             ▼                 │
│  [Accept Question]          [Agent 5: Revision Agent]  │
│                                      │ (Targeted fix)  │
│                                      └────────┘        │
└────────────────────────────────────────────────────────┘
        │
        ▼
[Structured Question Paper Assembly]
        │
        ├── Interactive UI Paper Viewer & Explainability Drawer ("Why this question?")
        ├── Inline Edit / Per-question & Per-section Regeneration
        ├── Visual Syllabus Coverage & CO/Bloom Analytics
        └── University Exam-Formatted PDF Export
```

---

## 🤖 5-Agent Architecture Workflow

| Agent | Name | Responsibility |
|---|---|---|
| **Agent 1** | **Requirement Analyzer** | Parses examination blueprint, section constraints (e.g. 10×2=20, 5×10=50), target Bloom levels, difficulty split, and creates slot schedule. |
| **Agent 2** | **RAG Retrieval Agent** | Performs metadata-filtered semantic search over uploaded textbooks, notes, and syllabus chunks to fetch top-k citations. |
| **Agent 3** | **Question Generation Agent** | Synthesizes descriptive university questions with cognitive action verbs strictly grounded in retrieved evidence. |
| **Agent 4** | **Validation Agent** | Verifies syllabus alignment, CO compliance, difficulty calibration, marks sum equality, and runs cosine duplicate detection. |
| **Agent 5** | **Revision Agent** | Autonomous self-repair loop: detects failures, retrieves targeted context, and regenerates weak or repetitive questions. |

---

## 🚀 Quick Start & Running Locally

### 1. Backend Setup
```bash
# Clone or navigate to the repository
cd backend

# Install dependencies
pip install -r requirements.txt

# Run FastAPI backend server (auto-seeds default courses & textbooks)
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Frontend Setup
```bash
# In a new terminal window
cd frontend

# Install dependencies (already initialized)
npm install

# Start Vite React development server
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 🔑 Pre-Seeded Demonstration Accounts

For immediate demonstration and viva presentation, the database comes pre-seeded with sample courses (**CS301 Data Structures**, **CS401 DBMS**) and accounts:

| Role | Email | Password | Access |
|---|---|---|---|
| **Faculty** | `faculty@academic.edu` | `FacultyPassword123!` | Question Paper Generation, RAG Uploads, PDF Export |
| **Administrator** | `admin@academic.edu` | `AdminPassword123!` | System Audit, User Management, Metrics Dashboard |

*(Instant one-click demo login buttons are also provided on the login page!)*

---

## ⚙️ Environment Variables (.env)

The application uses OpenRouter as the primary LLM gateway to NVIDIA Nemotron 3.5 Lightning:

```env
# Primary LLM Provider: "openrouter" (or "deterministic" for offline unit test mocks)
LLM_PROVIDER=openrouter

# OpenRouter Configuration:
OPENROUTER_API_KEY=your-openrouter-api-key-here
OPENROUTER_MODEL=nvidia/nemotron-3.5-lightning:free
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_SITE_URL=http://localhost:5173
OPENROUTER_APP_NAME=QAgent

# If using Ollama:
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral
```

---

## 🧪 Automated Testing

Execute the complete backend test suite covering chunking, vector indexing, validation algorithms, and multi-agent generation:

```bash
python -m pytest backend/tests -v
```

---

## 📄 University PDF Export Features
- Official Institution & Department Header
- Examination Name, Course Code, Duration, Max Marks
- Instructions & Section Structure
- Tabular Question Breakdown with **Marks**, **Course Outcome (CO)**, and **Bloom Level**
- Proper Margins, Wrap Boundaries, and Confidentiality Watermarks.
