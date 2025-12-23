# AI-Powered Learning Management System (LMS)

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11-blue)
![Next.js](https://img.shields.io/badge/next.js-13-black)
![Docker](https://img.shields.io/badge/docker-ready-green)

A Final Year Project (FYP) implementing an intelligent LMS with personalized AI Tutoring, RAG-based recommendations, and automated content generation.

## 🚀 Quick Start

**Prerequisites:** Docker & Docker Compose.

```bash
# 1. Clone the repository
git clone <repo-url>
cd fyp_antigravity_5Dec_py

# 2. Configure Environment
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local

# 3. Start the Application
docker-compose up --build
```

Access the application:
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

*   **Frontend:** Next.js (React) for a responsive, interactive UI.
*   **Backend:** FastAPI (Python) for high-performance API and AI orchestration.
*   **Database:** PostgreSQL/SQLite for relational data persistence.
*   **AI Engine:** OpenAI (GPT-4) integration for the AI Tutor and Content Generator.

## 🤝 Contributing

Please read [GIT_WORKFLOW.md](docs/GIT_WORKFLOW.md) before submitting a Pull Request.

1.  Create a feature branch: `git checkout -b feature/amazing-feature`
2.  Commit changes: `git commit -m 'feat: add amazing feature'`
3.  Push to branch: `git push origin feature/amazing-feature`
4.  Open a Pull Request.

## 📄 License

This project is for educational purposes (Final Year Project).
