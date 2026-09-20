# System Architecture Specification

## 1. High-Level Architecture Overview

The **Agentic AI-Based Question Generator** is organized as a modular, decoupled full-stack application comprising:

1. **Presentation Layer (Frontend)**: React 19, TypeScript, Tailwind CSS, Recharts for analytics, and Lucide React icons.
2. **Application & API Layer (Backend)**: FastAPI asynchronous REST API handling authentication, document uploads, agent orchestration, and PDF generation.
3. **Knowledge & RAG Engine**: Semantic document extractor (PDF/DOCX/TXT), sliding window chunker, embedding engine, and persistent vector database with cosine distance ranking.
4. **Agentic Workflow Engine**: 5 autonomous specialized agents operating sequentially with validation feedback and auto-revision loops.
5. **Persistence Layer**: Async SQLite with SQLAlchemy ORM schemas and JSON-backed vector indexing.

```
┌────────────────────────────────────────────────────────┐
│                   React 19 Frontend                    │
│   (Wizard, Live Agent Tracker, Explainability Drawer)  │
└──────────────────────────┬─────────────────────────────┘
                           │ HTTP / JSON
┌──────────────────────────▼─────────────────────────────┐
│                 FastAPI Backend Server                 │
│  ├── /api/auth       ├── /api/courses                  │
│  ├── /api/resources  ├── /api/generate                 │
│  ├── /api/papers     └── /api/admin                    │
└──────┬──────────────────────┬───────────────────┬──────┘
       │                      │                   │
┌──────▼──────┐        ┌──────▼──────┐     ┌──────▼──────┐
│  SQLAlchemy │        │  RAG Engine │     │ Multi-Agent │
│ SQLite DB   │        │ VectorStore │     │ Orchestrator│
└─────────────┘        └─────────────┘     └─────────────┘
```

## 2. LLM Abstraction Layer
The application implements an extensible `BaseLLMProvider` interface with drop-in implementations:
- `OpenRouterProvider`: Calls OpenRouter API routing to NVIDIA Nemotron 3.5 Lightning (`nvidia/nemotron-3.5-lightning:free`).
- `OllamaProvider`: Connects to local Ollama daemon (`mistral`, `llama3`, `openchat`).
- `DeterministicAcademicProvider`: Offline academic knowledge synthesizer for unit tests.
