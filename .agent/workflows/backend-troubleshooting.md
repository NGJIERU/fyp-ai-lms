---
description: Backend deployment and troubleshooting checklist
---

# Backend Troubleshooting Workflow

## Common Issues & Solutions

### 1. "Failed to fetch" / CORS Errors
**Symptom:** Frontend shows "Failed to fetch" or CORS policy errors

**Checklist:**
// turbo
1. Check if backend is running: `curl http://localhost:8000/`
2. Check for Python errors in terminal where uvicorn runs
3. If port in use: `lsof -ti:8000 | xargs kill -9`
// turbo
4. Restart backend: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`

---

### 2. "ModuleNotFoundError"
**Symptom:** Server crashes with `ModuleNotFoundError: No module named 'xxx'`

**Fix:**
// turbo
1. Install missing module: `pip install <module_name>`
2. Common ones needed:
   - `pip install PyGithub` (for GitHub crawler)
   - `pip install arxiv` (for Arxiv crawler)
3. Restart server after installing

---

### 3. "no such column" Database Errors
**Symptom:** `sqlalchemy.exc.OperationalError: no such column: xxx`

**Cause:** Model was updated but database schema wasn't migrated

**Fix (SQLite):**
// turbo
1. Find your database: `ls *.db`
2. Check which one is active (likely `demo.db`)
// turbo
3. Add column manually: `sqlite3 demo.db "ALTER TABLE <table_name> ADD COLUMN <column_name> <TYPE>;"`
4. Restart server

**Alternative (full migration):**
```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

---

### 4. "Address already in use"
**Symptom:** `ERROR: [Errno 48] Address already in use`

**Fix:**
// turbo
1. Kill existing process: `lsof -ti:8000 | xargs kill -9`
// turbo
2. Restart: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`

---

## Pre-Deployment Checklist

Before testing frontend changes:

- [ ] Backend server is running (check terminal for errors)
- [ ] Database schema matches models (run migrations if needed)
- [ ] All Python dependencies installed (`pip install -r requirements.txt`)
- [ ] Environment variables set (`.env` file exists)

---

## Quick Commands Reference

```bash
# Start backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Kill stuck process
lsof -ti:8000 | xargs kill -9

# Check database tables
sqlite3 demo.db ".tables"

# Add missing column
sqlite3 demo.db "ALTER TABLE table_name ADD COLUMN column_name TYPE;"

# Check server health
curl http://localhost:8000/
```
