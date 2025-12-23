# SECTION 14 — MAINTAINABILITY & SCALABILITY

## 14.1 Maintainability

### **What parts are hardest to maintain?**
1.  **AI RAG Pipeline (`app/services/tutor/rag_pipeline.py`):**
    *   *Why?* It depends on external volatile factors (OpenAI Model versions, Prompt Engineering quality).
    *   *Mitigation:* Keep prompts in separate configuration files or database tables, not hardcoded in Python.
2.  **Crawlers (`app/services/crawler`):**
    *   *Why?* External sites (YouTube, GitHub) change their DOM/API structure frequently, breaking scrapers.
    *   *Mitigation:* Scheduled "Health Check" jobs that run daily to verify crawlers still work.

### **Where is technical debt?**
*   **Testing Coverage:** While we have Integration tests, the Unit test coverage for edge cases in the AI service is likely low due to the non-deterministic nature of LLMs.
*   **Frontend Types:** Some `any` types might exist in the TypeScript codebase during rapid prototyping phases.

### **How do I refactor safely?**
1.  **Guardrails:** Never refactor without a passing test suite (`pytest`).
2.  **Atomic Changes:** Refactor one module at a time (e.g., "Refactor Auth" separate from "Refactor Courses").
3.  **Deprecation:** If changing an API signature, support both the Old and New parameter for one release cycle (Mark old as `@deprecated`).

---

## 14.2 Scalability & Health

### **How does architecture support growth?**
*   **Stateless Backend:** The FastAPI server holds no state (User sessions are in JWTs). This means we can scale from 1 server to 10 servers behind a Load Balancer instantly.
*   **Database Decoupling:** The DB is a separate container. We can upgrade the DB hardware independently of the App Server.
*   **Async Workers:** Heavy AI tasks run in background threads (or Celery in future), ensuring the Web API remains snappy (low latency).

### **How do I monitor system health?**
For this FYP scope:
*   **Liveness Probe:** `GET /` (Root endpoint) -> Returns 200 OK.
*   **Readiness Probe:** `GET /api/v1/health/db` -> Checks if SQL query succeeds.

### **What metrics matter most?**
1.  **Latency (p95):** "95% of requests finish in <200ms". Critical for UX.
2.  **Error Rate:** "Percentage of 500 Errors". Should be <0.1%.
3.  **AI Token Usage:** Cost tracking (OpenAI Bill correlates to Usage).
