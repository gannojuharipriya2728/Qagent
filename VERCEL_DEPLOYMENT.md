# QAgent — Vercel Serverless Backend Deployment Guide

This guide details the architecture, configuration, environment variables, storage policies, and deployment steps required to deploy the **QAgent FastAPI Backend** to **Vercel's Python Serverless Runtime** (`@vercel/python`).

---

## 1. System Architecture: Render vs. Vercel

```
                                  +-----------------------+
                                  |    React Frontend     |
                                  |   (Vite / Vercel/...) |
                                  +-----------+-----------+
                                              | HTTPS / REST
                                              v
+-----------------------------------------------------------------------------------------+
|                               Vercel Python Serverless Runtime                          |
|                                       (api/index.py)                                    |
|                                                                                         |
|  +---------------------+   +---------------------+   +-------------------------------+  |
|  |     Auth & RBAC     |   |   Academic Engine   |   |   5-Agent Generation Engine   |  |
|  |   (JWT / bcrypt)    |   |  (Courses / Units)  |   | (Requirement, Retrieval, ...) |  |
|  +----------+----------+   +----------+----------+   +---------------+---------------+  |
+-------------|-------------------------|------------------------------|------------------+
              |                         |                              |
              v                         v                              v
+-----------------------------+ +--------------------+ +----------------------------------+
|     PostgreSQL (asyncpg)    | |  S3 Object Storage | |     OpenRouter LLM Gateway       |
|  - Neon / Supabase / RDS    | |  - Uploaded Files  | |  - nvidia/nemotron-3.5-lightning |
|  - Persistent DB Records    | |  - PDF Exam Sheets | |  - Structured Generation         |
|  - Users, Courses, Papers   | |  - AWS S3 / R2     | |  - Function Timeout: 60s+        |
+-----------------------------+ +--------------------+ +----------------------------------+
```

### Key Architectural Differences

| Component | Render (Previous) | Vercel Serverless (Current) |
|---|---|---|
| **Execution Model** | Long-running container (`uvicorn --workers 2`) | Ephemeral serverless function invocation |
| **Lifecycle** | Always-on background process | Event-driven per HTTP request |
| **Filesystem** | Container disk (ephemeral per deploy) | Read-only container (`/tmp` writable for ephemeral scratch only) |
| **Timeout Limits** | Configurable up to minutes/hours | Configured via `maxDuration: 60` in `vercel.json` |
| **Storage Engine** | Local filesystem or S3 | S3 Object Storage (`STORAGE_PROVIDER=s3`) strongly required |
| **Database** | Managed PostgreSQL (`asyncpg`) | Managed PostgreSQL (`asyncpg`) |

---

## 2. Serverless & Storage Limitations Report

| Feature / Artifact | Persistence on Vercel | Status & Recommendation |
|---|---|---|
| **PostgreSQL Database** | Persistent | Fully compatible via managed PostgreSQL (`DATABASE_URL`). Uses `asyncpg`. |
| **Uploaded Files (Syllabus/Notes/PDFs)** | Ephemeral if local | Use `STORAGE_PROVIDER=s3` (AWS S3, Cloudflare R2, MinIO). Local uploads to `/tmp` do not persist across lambdas. |
| **Generated Question Papers (PDFs)** | Ephemeral if local | Generated on-the-fly and streamed directly over HTTP; saved to S3 when `STORAGE_PROVIDER=s3`. |
| **Vector Store Index** | Ephemeral if local JSON | Uses in-memory & `/tmp/qagent/vector_store` for ephemeral requests; use PostgreSQL / PGVector or S3 for persistent distributed vectors. |
| **Background Daemons / Cron Loops** | Not Supported | Serverless instances freeze between requests. Scheduled jobs must use Vercel Cron Jobs (`crons` in `vercel.json`). |
| **SQLite Databases** | Not Supported in Production | SQLite files in `/tmp` lose data across lambdas. PostgreSQL with `asyncpg` is enforced in production. |

---

## 3. Required Environment Variables (Vercel Project Settings)

Configure these variables in **Vercel Dashboard -> Project -> Settings -> Environment Variables**:

```ini
# =================================================================
# Application & Environment Mode
# =================================================================
ENVIRONMENT=production
SEED_DEMO_DATA=false
PROJECT_NAME="QAgent — Agentic AI Question Generator"
VERSION="1.0.0"

# =================================================================
# Production Database (PostgreSQL 14+ / Neon / Supabase / AWS RDS)
# =================================================================
DATABASE_URL=postgresql+asyncpg://<username>:<password>@<db-host>:5432/<db-name>
DB_SSL_MODE=require
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10

# =================================================================
# Production Object Storage (AWS S3 / Cloudflare R2 / MinIO)
# =================================================================
STORAGE_PROVIDER=s3
S3_ENDPOINT_URL=https://s3.us-east-1.amazonaws.com
S3_ACCESS_KEY_ID=YOUR_AWS_ACCESS_KEY_ID
S3_SECRET_ACCESS_KEY=YOUR_AWS_SECRET_ACCESS_KEY
S3_BUCKET=qagent-production-storage
S3_REGION=us-east-1

# =================================================================
# AI / LLM Provider (NVIDIA NIM or OpenRouter)
# =================================================================
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-your-openrouter-key
OPENROUTER_MODEL=nvidia/nemotron-3.5-lightning:free
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_APP_NAME=QAgent

# (Alternative NVIDIA Direct NIM Provider)
NVIDIA_API_KEY=nvapi-your-nvidia-key
NVIDIA_MODEL=nvidia/nemotron-3.5-lightning-30b-a3b
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1

# =================================================================
# Security & JWT Tokens
# =================================================================
SECRET_KEY=generate-a-64-character-random-hex-string-using-openssl-rand-hex-32
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# =================================================================
# CORS Allowed Origins
# =================================================================
CORS_ORIGINS=["https://qagent-production-1.onrender.com", "https://qagent-production.onrender.com"]
```

---

## 4. Preserved Routes Parity

All backend API routes are mounted on the FastAPI `app` and exposed via `api/index.py`:

| Endpoint | Method | Description |
|---|---|---|
| `/` | `GET` | Root health and service metadata |
| `/health` | `GET` | Complete service health check (DB, Storage, LLM status) |
| `/health/db` | `GET` | Safe database diagnostic check (no credential leakage) |
| `/health/llm` | `GET` | Safe LLM provider reachability check |
| `/docs` | `GET` | Interactive Swagger API documentation |
| `/openapi.json` | `GET` | OpenAPI 3.0 specification |
| `/api/auth/register` | `POST` | User registration & JWT generation |
| `/api/auth/login` | `POST` | User login authentication |
| `/api/auth/me` | `GET` | Current authenticated user profile |
| `/api/courses` | `GET`, `POST` | List and create academic courses |
| `/api/courses/{id}` | `GET`, `DELETE` | Retrieve and delete course |
| `/api/resources` | `GET` | List academic uploaded resources |
| `/api/resources/upload` | `POST` | Multipart file upload and RAG vector indexing |
| `/api/resources/{id}` | `GET`, `DELETE` | Resource details and deletion |
| `/api/resources/{id}/download` | `GET` | Download raw resource document |
| `/api/generate` | `POST` | 5-agent question paper generation workflow |
| `/api/papers` | `GET` | List generated question papers |
| `/api/papers/{id}` | `GET`, `DELETE` | Get paper details or delete paper |
| `/api/papers/{id}/pdf` | `GET` | Export question paper to formatted PDF |
| `/api/papers/{id}/analytics` | `GET` | Paper bloom, CO, and difficulty distribution analytics |
| `/api/papers/{id}/questions/{qid}` | `PUT` | Edit question in paper |
| `/api/papers/{id}/questions/{qid}/regenerate` | `POST` | Regenerate specific question via AI agent |
| `/api/admin/stats` | `GET` | System overview statistics |
| `/api/admin/users` | `GET` | Admin user management |
| `/api/admin/users/{id}/toggle-status` | `PATCH` | Activate/Deactivate user |
| `/api/ai/health` | `GET` | AI provider connectivity diagnostics |

---

## 5. Deployment Instructions

### Option A: Deploy via Vercel CLI

1. Install Vercel CLI (if not installed):
   ```bash
   npm i -g vercel
   ```

2. Login to Vercel:
   ```bash
   vercel login
   ```

3. Deploy from repository root:
   ```bash
   vercel
   ```

4. Deploy to Production:
   ```bash
   vercel --prod
   ```

### Option B: Deploy via Vercel Git Integration (GitHub / GitLab)

1. Push your repository to GitHub.
2. In the Vercel Dashboard, click **Add New... -> Project** and import the repository.
3. Keep default settings (Framework Preset: **Other**, Root Directory: `./`).
4. Add all environment variables listed in Section 3.
5. Click **Deploy**.

---

## 6. Database Migrations (PostgreSQL)

Execute database migrations against your remote PostgreSQL instance prior to production traffic:

```bash
# Set remote DATABASE_URL in your shell or .env
export DATABASE_URL="postgresql+asyncpg://user:password@host:5432/dbname"

# Run migrations
alembic upgrade head
```

---

## 7. Post-Deployment Verification Suite

Run these tests against your Vercel deployment URL (e.g. `https://qagent-backend.vercel.app`):

### 1. Health Checks
```bash
# Root Endpoint
curl -s https://<your-vercel-domain>.vercel.app/

# Full Health Check
curl -s https://<your-vercel-domain>.vercel.app/health

# Database Diagnostic (PostgreSQL connectivity)
curl -s https://<your-vercel-domain>.vercel.app/health/db

# LLM Gateway Check
curl -s https://<your-vercel-domain>.vercel.app/health/llm
```

### 2. User Registration & Login
```bash
# Register User
curl -s -X POST https://<your-vercel-domain>.vercel.app/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "faculty@university.edu",
    "password": "SecurePassword123!",
    "full_name": "Prof. Alan Turing",
    "department": "Computer Science & Engineering",
    "role": "professor"
  }'

# Login
curl -s -X POST https://<your-vercel-domain>.vercel.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "faculty@university.edu",
    "password": "SecurePassword123!"
  }'
```

### 3. Course Management
```bash
curl -s -X GET https://<your-vercel-domain>.vercel.app/api/courses
```

### 4. Interactive API Documentation
Open `https://<your-vercel-domain>.vercel.app/docs` in any web browser.
