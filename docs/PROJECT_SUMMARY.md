# AI-Powered LMS - Project Summary

## Overview

This is a comprehensive AI-powered Learning Management System (LMS) built with FastAPI, PostgreSQL, and a hybrid AI stack (local embeddings + cloud LLM). The system supports university-level courses with features including material crawling, AI recommendations, personal tutoring, and auto-grading.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Backend                          │
├─────────────────────────────────────────────────────────────────┤
│  API Layer (v1)                                                 │
│  ├── auth/        - JWT authentication                          │
│  ├── users/       - User management                             │
│  ├── courses/     - Course CRUD                                 │
│  ├── syllabus/    - 14-week syllabus management                 │
│  ├── materials/   - Material repository & crawling              │
│  ├── recommendations/ - AI material recommendations             │
│  ├── tutor/       - AI personal tutoring                        │
│  ├── dashboard/   - Student & Lecturer dashboards               │
│  └── admin/       - Super admin management                      │
├─────────────────────────────────────────────────────────────────┤
│  Services Layer                                                 │
│  ├── crawler/     - YouTube, GitHub, arXiv, OER crawlers        │
│  ├── processing/  - Embeddings & quality scoring                │
│  ├── recommendation/ - Semantic matching engine                 │
│  └── tutor/       - RAG pipeline & auto-grading                 │
├─────────────────────────────────────────────────────────────────┤
│  Data Layer                                                     │
│  ├── PostgreSQL   - Relational data                             │
│  └── Embeddings   - Vector storage (JSON/pgVector)              │
└─────────────────────────────────────────────────────────────────┘
```

## Implemented Modules

### 1. User & Access Management ✅
- **Roles**: Super Admin, Lecturer, Student
- **Features**: JWT authentication, password hashing, role-based permissions
- **Files**: `app/models/user.py`, `app/api/v1/endpoints/auth.py`, `app/api/v1/endpoints/users.py`

### 2. Course & Syllabus Management ✅
- **Features**: CRUD for 6 courses, 14-week syllabus, version control
- **Files**: `app/models/course.py`, `app/models/syllabus.py`, `app/api/v1/endpoints/courses.py`, `app/api/v1/endpoints/syllabus.py`

### 3. Material Crawling & Repository ✅
- **Crawlers**: YouTube, GitHub, arXiv, MIT OCW, NPTEL
- **Features**: Metadata extraction, quality scoring, deduplication
- **Files**: `app/services/crawler/`

### 4. AI Recommendation System ✅
- **Features**: Semantic matching, quality-based ranking, lecturer approval workflow
- **Files**: `app/services/recommendation/`, `app/api/v1/endpoints/recommendations.py`

### 5. AI Personal Tutoring ✅
- **Features**: Concept explanation, answer checking, hints, question generation
- **Auto-grading**: MCQ, short text, Python code, step-by-step
- **Files**: `app/services/tutor/`, `app/api/v1/endpoints/tutor.py`

### 6. Student Dashboard ✅
- **Features**: Enrolled courses, progress tracking, weak topics, materials access
- **Files**: `app/api/v1/endpoints/dashboard.py`

### 7. Lecturer Dashboard ✅
- **Features**: Course management, student performance, material approval
- **Files**: `app/api/v1/endpoints/dashboard.py`

### 8. Super Admin ✅
- **Features**: User management, system stats, crawl logs, activity monitoring
- **Files**: `app/api/v1/endpoints/admin.py`

### 9. Performance Tracking ✅
- **Features**: Quiz attempts, topic performance, learning sessions, activity logs
- **Files**: `app/models/performance.py`

## API Endpoints Summary

| Prefix | Description | Auth Required |
|--------|-------------|---------------|
| `/api/v1/auth` | Login, Register | No |
| `/api/v1/users` | User management | Yes |
| `/api/v1/courses` | Course CRUD | Yes |
| `/api/v1/syllabus` | Syllabus management | Yes |
| `/api/v1/materials` | Material repository | Yes |
| `/api/v1/recommendations` | AI recommendations | Lecturer+ |
| `/api/v1/tutor` | AI tutoring | Yes |
| `/api/v1/dashboard` | Dashboards | Yes |
| `/api/v1/admin` | Admin functions | Super Admin |

## Database Schema

### Core Tables
- `users` - User accounts with roles
- `courses` - Course definitions
- `syllabus` - Weekly syllabus entries with versioning
- `materials` - Crawled learning materials
- `material_topics` - Material-to-syllabus mappings

### Performance Tables
- `student_enrollments` - Course enrollments
- `quiz_attempts` - Individual quiz submissions
- `topic_performance` - Aggregated performance per topic
- `learning_sessions` - Tutor interaction sessions
- `tutor_interactions` - Individual tutor exchanges
- `activity_logs` - System-wide activity tracking

### System Tables
- `crawl_logs` - Crawler execution logs

## Technology Stack

| Component | Technology |
|-----------|------------|
| Frontend | Next.js 16 (React) |
| Backend | FastAPI 0.109.0 |
| Database | PostgreSQL 15 (Supabase) + SQLAlchemy 2.0 |
| Auth | JWT (python-jose) |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| LLM | HuggingFace (Qwen2.5-72B-Instruct) |
| Crawling | BeautifulSoup, PyGithub, arxiv, youtube-transcript-api |
| Testing | pytest, httpx |
| **Deployment** | |
| Frontend Hosting | Vercel |
| Backend Hosting | Fly.io |
| Database Hosting | Supabase |

## Live Demo

| Service | URL |
|---------|-----|
| **Frontend** | https://fyp-ai-lms.vercel.app |
| **Backend API** | https://fyp-ai-lms-backend.fly.dev |
| **API Docs** | https://fyp-ai-lms-backend.fly.dev/docs |

**Demo Credentials:**
- Admin: `admin@lms.edu` / `admin123`
- Lecturer: `smith@lms.edu` / `lecturer123`
- Student: `alice@lms.edu` / `student123`

## Quick Start (Local Development)

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment
Create `backend/.env` file:
```env
POSTGRES_SERVER=localhost
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=lms_db
SECRET_KEY=your-secret-key-change-in-production
HUGGINGFACE_API_TOKEN=hf_xxx  # For AI Tutor
YOUTUBE_API_KEY=your-youtube-key   # Optional
GITHUB_ACCESS_TOKEN=your-token     # Optional
```

### 3. Run Migrations
```bash
alembic upgrade head
```

### 4. Seed Initial Data
```bash
python seed_courses_syllabus.py
```

### 5. Start Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Access API Docs
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_tutor_service.py -v
```

## Project Structure

```
fyp_antigravity_5Dec_py/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   │           ├── auth.py
│   │           ├── users.py
│   │           ├── courses.py
│   │           ├── syllabus.py
│   │           ├── materials.py
│   │           ├── recommendations.py
│   │           ├── tutor.py
│   │           ├── dashboard.py
│   │           └── admin.py
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   └── security.py
│   ├── models/
│   │   ├── user.py
│   │   ├── course.py
│   │   ├── syllabus.py
│   │   ├── material.py
│   │   └── performance.py
│   ├── schemas/
│   │   ├── user.py
│   │   ├── course.py
│   │   ├── syllabus.py
│   │   └── material.py
│   ├── services/
│   │   ├── crawler/
│   │   │   ├── base.py
│   │   │   ├── manager.py
│   │   │   ├── youtube_crawler.py
│   │   │   ├── github_crawler.py
│   │   │   ├── arxiv_crawler.py
│   │   │   └── oer_crawler.py
│   │   ├── processing/
│   │   │   ├── embedding_service.py
│   │   │   └── quality_scorer.py
│   │   ├── recommendation/
│   │   │   └── recommendation_engine.py
│   │   └── tutor/
│   │       ├── ai_tutor.py
│   │       ├── rag_pipeline.py
│   │       └── answer_checker.py
│   └── main.py
├── alembic/
│   └── versions/
├── tests/
│   ├── test_auth.py
│   ├── test_courses_api.py
│   ├── test_syllabus_api.py
│   ├── test_materials_api.py
│   ├── test_recommendation_service.py
│   └── test_tutor_service.py
├── requirements.txt
└── PROJECT_SUMMARY.md
```

## Key Features by Role

### Student
- View enrolled courses and syllabus
- Access approved learning materials
- Interact with AI tutor for explanations
- Practice with auto-graded questions
- Track weak topics and get revision suggestions

### Lecturer
- Manage course syllabus
- Review AI-recommended materials
- Approve/reject material mappings
- Monitor student performance
- Toggle solution visibility for assignments

### Super Admin
- Manage all users (CRUD)
- Manage all courses
- View system statistics
- Monitor crawling performance
- Access activity logs

## Grading Modes

| Mode | MCQ | Short Text | Code | Step-by-Step |
|------|-----|------------|------|--------------|
| Practice | Shows correct answer + explanation | Shows model answer + missing concepts | Shows all test results + solution | Shows all steps + expected answers |
| Graded | Only hints | Only hints about missing concepts | Only failing input (no expected) | Only first wrong step hint |

## Future Enhancements

1. **pgVector Integration** - Native PostgreSQL vector search
2. **Real-time Notifications** - WebSocket for live updates
3. **Advanced Analytics** - Learning analytics dashboard
4. **Plagiarism Detection** - Code similarity checking
5. **Collaborative Features** - Discussion forums, peer review
6. **Mobile API** - Optimized endpoints for mobile apps

## License

This project is developed as a Final Year Project (FYP) for educational purposes.
