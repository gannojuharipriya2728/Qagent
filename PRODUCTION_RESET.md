# QAgent — Safe Production Data Reset & Deployment Guide

This guide details the procedure for safely clearing development/demo data and preparing a clean, fresh instance of **QAgent** for university or institutional production deployment.

---

## 1. Scope: What Gets Reset vs. What is Preserved

### ❌ What Gets Cleared During Reset
* **Database Records**: `data/academic_rag.db` (clears all development courses, demo users, test generation sessions, and sample questions).
* **Vector Index**: `data/vector_store/index.json` (removes all development document embeddings).
* **Uploaded Files**: `data/uploads/*` (removes any test PDFs, syllabi, or notes uploaded during development).
* **Exported Documents**: `data/exports/*` (removes temporary test examination paper PDFs).
* **Test Artifacts**: `data/test_vector_store.json` (removes test scratch files).

###  What is Strictly Preserved
* **All Source Code**: Backend multi-agent engine, RAG pipeline, FastAPI routes, and React frontend.
* **All AI Architecture & LLM Gateway**: OpenRouter (`nvidia/nemotron-3.5-lightning:free`) integration and prompt engineering templates.
* **Database Schema Definitions**: All 10 SQLAlchemy model table schemas (`Base.metadata.create_all`).
* **Configuration & Environment**: `.env` and `.env.example` remain completely untouched.
* **Frontend Production Build**: `dist/` production assets.

---

## 2. Safe Execution Steps

### Step 1: Pre-Reset Inspection (Dry-Run)
Inspect what files and database records exist without modifying or deleting anything:
```bash
py backend/scripts/reset_production_data.py --dry-run
```

### Step 2: Backup (Recommended Before Production Reset)
If you have existing academic data you wish to archive:
```bash
# Example backup to a timestamped directory
mkdir -p data/backups
cp -r data/academic_rag.db data/backups/academic_rag_backup.db
cp -r data/uploads data/backups/uploads_backup
cp -r data/vector_store data/backups/vector_store_backup
```

### Step 3: Execute Production Reset (Requires Strict Confirmation)
Execution requires **both** the environment variable `RESET_PRODUCTION_DATA=YES` and the `--confirm` flag to prevent accidental data loss:

#### On Windows (Command Prompt / PowerShell):
```cmd
set RESET_PRODUCTION_DATA=YES
py backend/scripts/reset_production_data.py --confirm
```
*In PowerShell:*
```powershell
$env:RESET_PRODUCTION_DATA="YES"
py backend/scripts/reset_production_data.py --confirm
```

#### On Linux / macOS:
```bash
RESET_PRODUCTION_DATA=YES py backend/scripts/reset_production_data.py --confirm
```

---

## 3. Creating the First Production Administrator

After reset, no demo accounts (`faculty@academic.edu`, `admin@academic.edu`) exist. You can securely create your initial administrator account using either method:

### Method A: Direct CLI Provisioning Tool
```bash
py backend/scripts/create_initial_admin.py \
  --email "admin@youruniversity.edu" \
  --password "YourStrongSecurePassword123!" \
  --name "Dean of Examinations" \
  --department "Examination Control Branch"
```

### Method B: Single-Step Reset & Admin Creation
```bash
set RESET_PRODUCTION_DATA=YES
py backend/scripts/reset_production_data.py --confirm \
  --admin-email "admin@youruniversity.edu" \
  --admin-password "YourStrongSecurePassword123!" \
  --admin-name "Dean of Examinations"
```

---

## 4. Production Environment Configuration (`.env`)

For a production deployment, ensure your `.env` contains:
```ini
# Environment Mode (Disables automatic demo data seeding)
ENVIRONMENT=production
SEED_DEMO_DATA=false

# OpenRouter AI Gateway (NVIDIA Nemotron 3.5 Lightning)
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_live_openrouter_api_key
OPENROUTER_MODEL=nvidia/nemotron-3.5-lightning:free
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_SITE_URL=https://youruniversity.edu
OPENROUTER_APP_NAME=QAgent

# Security (Change to a unique random 64-character secret)
SECRET_KEY=your-production-cryptographic-secret-key-at-least-32-chars

# Database & Storage
DATABASE_URL=sqlite+aiosqlite:///./data/academic_rag.db
STORAGE_DIR=./data/uploads
VECTOR_STORAGE_DIR=./data/vector_store
```

---

## 5. Post-Reset Clean-State Verification

Verify that all tables have 0 rows (or 1 if you created the admin), the vector store is clean, and upload folders are empty:
```bash
py backend/scripts/reset_production_data.py --verify-only
```

Expected Clean Output:
```
=================================================================
  QAGENT PRODUCTION CLEAN-STATE VERIFICATION
=================================================================
  Database File:        C:\New folder\data\academic_rag.db (EXISTS)
  Vector Index:         C:\New folder\data\vector_store\index.json (NOT FOUND)
  Test Vector File:     C:\New folder\data\test_vector_store.json (NOT FOUND)
  Uploads Directory:    0 files
  Exports Directory:    0 files

  Database Table Row Counts:
    - users                 : 1 (or 0)
    - courses               : 0
    - units                 : 0
    - course_outcomes       : 0
    - resources             : 0
    - resource_chunks       : 0
    - question_papers       : 0
    - questions             : 0
    - generation_sessions   : 0
    - validation_results    : 0
=================================================================

[VERIFICATION RESULT] State is CLEAN for production deployment.
```
