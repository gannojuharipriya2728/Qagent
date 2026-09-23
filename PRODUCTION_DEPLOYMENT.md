# QAgent — Production Deployment & Storage Architecture Guide

This document describes how to deploy **QAgent** into a production environment with PostgreSQL, S3-compatible Object Storage, Alembic database migrations, and OpenRouter AI Gateway (`nvidia/nemotron-3.5-lightning:free`).

---

## 1. System Architecture

```
                                  +-----------------------+
                                  |    React Frontend     |
                                  |     (Vite Bundle)     |
                                  +-----------+-----------+
                                              | HTTPS / REST
                                              v
+-----------------------------------------------------------------------------------------+
|                                    FastAPI Backend                                      |
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
|  - Users & Roles            | |  - Uploaded Syllabi| |  - nvidia/nemotron-3.5-lightning |
|  - Curricula & Outcomes     | |  - Notes/Textbooks | |  - Structured JSON Output        |
|  - Questions & Blueprints   | |  - PDF Exam Sheets | |  - Pedagogical Prompt Pipeline   |
|  - Audit & Analytics Logs   | |  - RAG Backups     | |                                  |
+-----------------------------+ +--------------------+ +----------------------------------+
```

---

## 2. Environment Variables Specification

Set the following environment variables in your production environment (or `.env` file):

```ini
# =================================================================
# Application & Environment Mode
# =================================================================
ENVIRONMENT=production
SEED_DEMO_DATA=false
PROJECT_NAME="QAgent — Agentic AI Question Generator"
VERSION="1.0.0"

# =================================================================
# Production Database (PostgreSQL 14+)
# =================================================================
DATABASE_URL=postgresql+asyncpg://qagent_user:StrongPasswordHere@postgres-host:5432/qagent_production

# =================================================================
# Production Object Storage (AWS S3 / MinIO / Cloudflare R2)
# =================================================================
STORAGE_PROVIDER=s3
S3_ENDPOINT_URL=https://s3.us-east-1.amazonaws.com # (or MinIO/R2 endpoint)
S3_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
S3_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
S3_BUCKET=qagent-production-storage
S3_REGION=us-east-1

# Vector Store Engine
VECTOR_STORE_PROVIDER=local
VECTOR_STORAGE_DIR=./data/vector_store

# =================================================================
# AI / LLM Gateway — OpenRouter (Primary Provider)
# =================================================================
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-your-live-production-key
OPENROUTER_MODEL=nvidia/nemotron-3.5-lightning-30b-a3b
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_SITE_URL=https://qagent.vercel.app
OPENROUTER_APP_NAME=QAgent

# Alternative Direct NVIDIA NIM Provider (Optional)
NVIDIA_API_KEY=nvapi-your-live-production-key
NVIDIA_MODEL=nvidia/nemotron-3.5-lightning-30b-a3b
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1

# =================================================================
# Security & JWT Tokens
# =================================================================
SECRET_KEY=generate-a-64-character-random-hex-string-using-openssl-rand-hex-32
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# CORS Allowed Origins
CORS_ORIGINS=["https://qagent-frontend-iota.vercel.app", "https://qagent.vercel.app"]
```

---

## 3. Database Setup (PostgreSQL)

1. Create a dedicated PostgreSQL database and user:
   ```sql
   CREATE USER qagent_user WITH PASSWORD 'StrongPasswordHere';
   CREATE DATABASE qagent_production OWNER qagent_user;
   GRANT ALL PRIVILEGES ON DATABASE qagent_production TO qagent_user;
   ```
2. Run Alembic database migrations:
   ```bash
   alembic upgrade head
   ```

---

## 4. Object Storage Setup (S3 / MinIO / Cloudflare R2)

1. Create a private bucket named `qagent-production-storage`.
2. Configure IAM credentials with `PutObject`, `GetObject`, `DeleteObject`, `HeadObject` permissions.
3. Verify bucket access using the health check endpoint `/api/health`.

---

## 5. First Production Administrator Provisioning

Run the secure CLI provisioning tool to create your initial administrator:
```bash
py backend/scripts/create_initial_admin.py \
  --email "admin@youruniversity.edu" \
  --password "YourStrongPassword123!" \
  --name "Dean of Examinations" \
  --department "Examination Control Branch"
```

---

## 6. Running the Production Server

### Render Web Service Settings

`render.yaml` in the repository root is the authoritative blueprint. The live
service was created from the dashboard, so its settings must match:

| Setting | Value |
|---|---|
| Root Directory | *(blank — repository root)* |
| Build Command | `pip install --upgrade pip && pip install -r requirements.txt` |
| Start Command | `uvicorn asgi:app --host 0.0.0.0 --port $PORT --workers 1` |
| Health Check Path | `/health` |
| Python Version | `3.11` (`PYTHON_VERSION` env var) |

The application package lives in `backend/` and imports itself absolutely
(`from app.core.config import ...`), so `backend/` must be on `sys.path`.
`uvicorn backend.app.main:app` from the repository root therefore fails with
`ModuleNotFoundError: app`. Two start commands are valid:

```bash
# Root Directory blank — asgi.py puts backend/ on sys.path.
uvicorn asgi:app --host 0.0.0.0 --port $PORT --workers 1

# Root Directory = backend
uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1
```

Prefer the first: running from the repository root also makes `alembic.ini` and
`alembic/` reachable for migrations.

**Use a single worker.** The local vector store is an in-process singleton that
persists to a JSON file. Additional workers each keep their own copy and write
to the same path, which wastes memory and races on that file. Retrieval still
returns correct results — `similarity_search` re-hydrates a course's chunks from
PostgreSQL when they are not in memory — but there is nothing to gain. Scale out
only after moving the index to `VECTOR_STORE_PROVIDER=pgvector`.

### Bind to Render's port

Render injects `$PORT`; never hardcode 8000 in the start command. Binding to
`0.0.0.0` is required for the health check to reach the process.

### Health Check Endpoint:
```bash
curl -X GET https://qagent.youruniversity.edu/api/health
```
Response:
```json
{
  "status": "healthy",
  "service": "QAgent — Agentic AI Question Generator",
  "version": "1.0.0",
  "environment": "production",
  "database": "connected",
  "storage_provider": "s3",
  "storage": "connected",
  "llm_provider": "nvidia",
  "llm_model": "nvidia/nemotron-3.5-lightning-30b-a3b"
}
```

---

## 7. Backup & Restore Procedures

### Database Backup (PostgreSQL):
```bash
pg_dump -U qagent_user -h postgres-host -Fc qagent_production > backup_$(date +%Y%m%d_%H%M%S).dump
```

### Database Restore:
```bash
pg_restore -U qagent_user -h postgres-host -d qagent_production -c backup_filename.dump
```

### S3 Storage Backup:
```bash
aws s3 sync s3://qagent-production-storage s3://qagent-backup-storage/$(date +%Y%m%d)/
```

---

## 8. Security Checklist

- [x] **No hardcoded secrets**: All API keys, database credentials, and S3 credentials load strictly from environment variables.
- [x] **JWT Secret Key**: Uses a 64-character cryptographically random string.
- [x] **Password Hashing**: Passwords stored using `bcrypt` with unique salts.
- [x] **CORS restricted**: Allowed origins configured strictly to institutional domains.
- [x] **Course Isolation**: Vector retrieval strictly enforces `course_id` and `unit_number` boundaries to prevent cross-course data leakage.
- [x] **Path Traversal Protection**: Storage service sanitizes paths to prevent unauthorized directory traversal.
