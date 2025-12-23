# SECTION 9 — DOCKER & DEPLOYMENT

## 9.1 Container Strategy

### **Why is Docker used in this project?**
*   **Consistency:** "It works on my machine" is eliminated. The environment (Python 3.11, Node 18) is identical for all developers.
*   **Isolation:** The Backend dependencies won't clash with your system Python.
*   **Ease of Start:** `docker-compose up` is the only command needed to boot the entire stack.

### **What does each container do?**
1.  **Backend (`python:3.11-slim`):** Runs FastAPI via Uvicorn. Handles API requests, database ORM, and background AI tasks.
2.  **Frontend (`node:18-alpine`):** Runs the Next.js development server. Serves the UI pages.
3.  **Database (Optional/Planned):** Currently using SQLite/Local Postgres, but in production, a `postgres:15` container would be added here.

### **How do containers communicate?**
*   **Internal Network:** Docker creates a virtual network `fyp_antigravity_default`.
*   **Service Discovery:** Containers can reach each other by name. The frontend container *could* reach the backend at `http://backend:8000`.
*   **Client Access:** However, since Next.js runs in the *Browser*, the actual API calls go to `localhost:8000` (mapped to host).

---

## 9.2 Configuration & Operations

### **What ports are exposed and why?**
*   **3000 (Frontend):** Standard Next.js port. Accessed by User.
*   **8000 (Backend):** Standard FastAPI port. Accessed by User (Frontend fetches) and Swagger UI.

### **How is data persisted across restarts?**
*   **Code:** We use **Bind Mounts** (`./backend:/app`). Changes you make in VS Code are immediately reflected inside the container (Hot Reload).
*   **Database:**
    *   *SQLite:* The file `demo.db` is in the bind mount, so it persists.
    *   *Postgres:* We would use a named volume `postgres_data` to survive container deletion.

### **What breaks if Docker is removed?**
*   **Dependency Hell:** You must manually install `python 3.11`, `node 18`, `pip install -r requirements.txt`, and `npm install`.
*   **Environment Drift:** Your version of `pydantic` might differ from production, causing subtle bugs.

---

## 9.3 Deployment Process

### **How do I scale services?**
*   **Command:** `docker-compose up --scale backend=3`
*   **Requirement:** Would need a Load Balancer (Nginx) in front to distribute traffic, which is currently out of scope for this FYP.

### **What is the deployment process?**
For this FYP (Local Deployment):
1.  **Build:** `docker-compose build`
2.  **Run:** `docker-compose up -d`
3.  **Seed:** `docker-compose exec backend python scripts/seed_db.py`

For Production (Cloud/VPS):
1.  **Repo:** Pull latest code on the server.
2.  **Env:** Set `PROJECT_ENV=production` in `.env`.
3.  **SSL:** Run a reverse proxy (Caddy/Nginx) to terminate HTTPS and forward to localhost:3000.

### **How do I redeploy after changes?**
1.  `git pull`
2.  `docker-compose build` (if dependencies changed)
3.  `docker-compose up -d` (recreates only changed containers)
