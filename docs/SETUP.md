# Setup & Deployment Guide

## Prerequisites
- **Python 3.10+** (tested on Python 3.13)
- **Node.js 18+** and **npm**

## Installation Steps

### 1. Backend Setup
```bash
# In project root
cd backend
pip install -r requirements.txt

# Start backend
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
The backend initializes the SQLite database at `./data/academic_rag.db` and auto-seeds demonstration accounts and sample courses on first startup.

### 2. Frontend Setup
```bash
# In a separate terminal
cd frontend
npm install
npm run dev
```

The frontend application will be accessible at: `http://localhost:5173`

---

## Production Deployment
To build the frontend bundle:
```bash
cd frontend
npm run build
```
The compiled assets will be in `frontend/dist`.
