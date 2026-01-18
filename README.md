# AI-Powered Learning Management System (LMS)

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11-blue)
![Next.js](https://img.shields.io/badge/next.js-16-black)
![PostgreSQL](https://img.shields.io/badge/postgresql-15-blue)

A Final Year Project (FYP) implementing an intelligent LMS with personalized AI Tutoring, RAG-based recommendations, and automated content generation.

## 🌐 Live Demo

| Service | URL |
|---------|-----|
| **Frontend** | https://fyp-ai-lms.vercel.app |
| **Backend API** | https://fyp-ai-lms-backend.fly.dev |
| **API Docs** | https://fyp-ai-lms-backend.fly.dev/docs |

**Demo Credentials:**
- **Admin:** `admin@lms.edu` / `admin123`
- **Lecturer:** `smith@lms.edu` / `lecturer123`
- **Student:** `alice@lms.edu` / `student123`

## 🚀 Quick Start (Local Development)

**Prerequisites:** Python 3.11, Node.js 18+, PostgreSQL 15+

```bash
# 1. Clone the repository
git clone https://github.com/NGJIERU/fyp-ai-lms.git
cd fyp-ai-lms

# 2. Backend Setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # Edit with your credentials
uvicorn app.main:app --reload --port 8000

# 3. Frontend Setup (new terminal)
cd frontend
npm install
cp .env.example .env.local  # Edit NEXT_PUBLIC_API_BASE_URL
npm run dev
```

Access locally:
*   **Frontend:** [http://localhost:3000](http://localhost:3000)
*   **Backend API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 📚 Documentation Suite

We have comprehensive documentation available in the `docs/` directory:

| Section | Document | Description |
| :--- | :--- | :--- |
| **1. Application** | [Scope & Definition](docs/SCOPE_AND_DEFINITION.md) | Problem statement, user roles, and boundaries. |
| **2. Requirements** | [Requirements Spec](docs/REQUIREMENTS_SPECIFICATION.md) | Functional (Use Cases) and Non-Functional requirements. |
| **3. Architecture** | [Values & System Arch](docs/SYSTEM_ARCHITECTURE.md) | High-level design, component diagrams, and tech stack. |
| **4. Frontend** | [Frontend Design](docs/FRONTEND_DESIGN.md) | Next.js structure, UI components, and state management. |
| **5. Backend** | [Backend Design](docs/BACKEND_DESIGN.md) | FastAPI services, API structure, and business logic. |
| **6. Data** | [Database Design](docs/DATABASE_DESIGN.md) | PostgreSQL schema, ERD, and data integrity. |
| **7. Config** | [Environment Config](docs/ENVIRONMENT_CONFIGURATION.md) | Env variables, secrets, and setup guide. |
| **8. Workflow** | [Git Workflow](docs/GIT_WORKFLOW.md) | Branching strategy, commit conventions, and version control. |
| **9. Ops** | [Docker Deployment](docs/DOCKER_DEPLOYMENT.md) | Container strategy, networking, and production deployment. |
| **10. Reliability** | [Error Handling](docs/ERROR_HANDLING_LOGGING.md) | Exception management, logging standards, and debugging. |
| **11. Security** | [Security Strategy](docs/SECURITY.md) | Authentication (JWT), Authorization (RBAC), and protection. |
| **12. QA** | [Testing Strategy](docs/TESTING_STRATEGY.md) | Unit, Integration, and E2E testing methodologies. |
| **13. Meta** | [Documentation Guide](docs/DOCUMENTATION_GUIDE.md) | How to read and maintain this documentation. |

---

## 🏗️ Architecture Overview

The system follows a **Modular Monolith** architecture:

*   **Frontend:** Next.js 16 (React) deployed on **Vercel**
*   **Backend:** FastAPI (Python) deployed on **Fly.io**
*   **Database:** PostgreSQL on **Supabase** (cloud)
*   **AI Engine:** HuggingFace (Qwen2.5-72B) + local embeddings (sentence-transformers)

### Deployment Architecture
```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Vercel        │────▶│   Fly.io         │────▶│   Supabase      │
│   (Frontend)    │     │   (Backend)      │     │   (PostgreSQL)  │
│   Next.js 16    │     │   FastAPI        │     │   Database      │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

## 🛠️ Commands Reference

### Local Development

| Action | Command |
|--------|---------|
| **Start Backend** | `cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8000` |
| **Start Frontend** | `cd frontend && npm run dev` |
| **Seed Database** | `cd backend && python scripts/seeds/setup_demo.py` |

### Production (Fly.io)

| Action | Command |
|--------|---------|
| **Start Backend** | `fly scale count 1 --app fyp-ai-lms-backend` |
| **Stop Backend** | `fly scale count 0 --app fyp-ai-lms-backend` |
| **View Logs** | `fly logs --app fyp-ai-lms-backend --no-tail` |
| **SSH into Server** | `fly ssh console --app fyp-ai-lms-backend` |
| **Deploy Changes** | `cd backend && fly deploy` |

> **Note:** Frontend on Vercel auto-deploys on `git push`. Fly.io backend needs manual start/stop to save costs.

---

## 🤝 Contributing

Please read [GIT_WORKFLOW.md](docs/GIT_WORKFLOW.md) before submitting a Pull Request.

1.  Create a feature branch: `git checkout -b feature/amazing-feature`
2.  Commit changes: `git commit -m 'feat: add amazing feature'`
3.  Push to branch: `git push origin feature/amazing-feature`
4.  Open a Pull Request.

## 📄 License

This project is for educational purposes (Final Year Project).
