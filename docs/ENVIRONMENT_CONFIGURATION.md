# SECTION 7 — ENVIRONMENT & CONFIGURATION

## 7.1 Environment Variables

### **What environment variables exist?**
The project is configured via `.env` files. Below is the reference table:

#### **Backend (`backend/.env`)**
| Variable | Description | Default / Example | Required? |
| :--- | :--- | :--- | :--- |
| `POSTGRES_SERVER` | Database Service Hostname | `db` (Docker) or `localhost` (Local) | Yes |
| `POSTGRES_USER` | Database Username | `postgres` | Yes |
| `POSTGRES_PASSWORD` | Database Password | `securepassword` | Yes |
| `POSTGRES_DB` | Database Name | `lms_db` | Yes |
| `SECRET_KEY` | Cryptographic Key for JWT | `random_string_here` | Yes |
| `OPENAI_API_KEY` | Key for GPT-4 features | `sk-...` | Optional (if `USE_OPENAI_TUTOR=true`) |
| `USE_OPENAI_TUTOR` | Toggle AI Tutor Feature | `true` / `false` | No (Defaults to `false`) |
| `AI_TUTOR_MODEL` | Specific LLM to use | `gpt-4-turbo` | No |
| `BACKEND_CORS_ORIGINS` | Allowed Frontend URLs | `["http://localhost:3000"]` | Yes |

#### **Frontend (`frontend/.env.local`)**
| Variable | Description | Default / Example | Required? |
| :--- | :--- | :--- | :--- |
| `NEXT_PUBLIC_API_BASE_URL` | URL of the Backend API | `http://localhost:8000` | Yes |

---

## 7.2 Configuration Management

### **Which values differ across environments?**
| Env | `DATABASE_URL` / `POSTGRES_SERVER` | `SECRET_KEY` | `NEXT_PUBLIC_API_BASE_URL` |
| :--- | :--- | :--- | :--- |
| **Local** | `localhost` (PostgreSQL) | `dev-key` | `http://localhost:8000` |
| **Docker** | `db` (Service Name) | `dev-key` | `http://localhost:8000` |
| **Production (Fly.io)** | `postgresql://...@db.xxx.supabase.co` | **Fly.io Secret** | `https://fyp-ai-lms-backend.fly.dev` |

### **What happens if an env variable is missing?**
*   **Startup Failure:** The Backend uses Pydantic Settings (`app/core/config.py`). If a required field (like `SECRET_KEY`) is missing, the application **refuses to start** and prints a validation error.
*   **Graceful fallback:** Optional fields (like `OPENAI_API_KEY`) default to `None`. The app starts, but the "Ask Tutor" feature will return a "Service unavailable" error if accessed.

### **Why must secrets never be committed?**
*   **Security Risk:** Examples like `POSTGRES_PASSWORD` or `OPENAI_API_KEY` give full access to your data and billing.
*   **Git History:** Once committed, a secret is forever in the git history unless rewritten. We use `.gitignore` to prevent files like `.env` and `.env.local` from being tracked.

### **How can a new developer configure this project?**
1.  **Clone** the repo: `git clone https://github.com/NGJIERU/fyp-ai-lms.git`
2.  **Copy Templates:**
    *   `cp backend/.env.example backend/.env`
    *   `cp frontend/.env.example frontend/.env.local`
3.  **Fill Values:** Update the `.env` files with local PostgreSQL credentials.
4.  **Run Backend:** `cd backend && uvicorn app.main:app --reload`
5.  **Run Frontend:** `cd frontend && npm run dev`

### **Production Environment Variables (Fly.io)**
Secrets are set via Fly.io CLI:
```bash
fly secrets set DATABASE_URL="postgresql://postgres:PASSWORD@db.xxx.supabase.co:5432/postgres"
fly secrets set SECRET_KEY="your-secure-key"
fly secrets set HUGGINGFACE_API_TOKEN="hf_xxx"
```

### **How do I separate dev vs prod behavior?**
*   **Docker Compose Overrides:** We use `docker-compose.yml` for base config and `docker-compose.prod.yml` for production overrides (like restarting policies and volume bindings).
*   **Debug Mode:** `DEBUG=True` (in Django/FastAPI) is enabled in Dev but **MUST** be `False` in Prod to avoid leaking stack traces.
