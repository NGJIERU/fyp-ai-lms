# SECTION 3 — SYSTEM ARCHITECTURE

## 3.1 High-Level Design

### **What are the main system components?**
1.  **Frontend Clients (The "Face"):** Next.js (React) application serving both Student and Lecturer interfaces.
2.  **API Gateway / Backend (The "Brain"):** FastAPI application handling all business logic, authentication, and orchestration of services.
3.  **Database (The "Memory"):** PostgreSQL storing relational data (Users, Courses, Quiz Results).
4.  **AI Services (The "Intelligence"):**
    *   **Embedding Engine:** Local (Sentence-Transformers) or Cloud (OpenAI) to convert text to vectors.
    *   **LLM Interface:** Connects to OpenAI GPT-4 for Tutoring and Generation.
5.  **Crawlers (The "Arms"):** Background services that fetch data from YouTube, GitHub, and ArXiv.

### **How do these components communicate?**
*   **Frontend ↔ Backend:** Strictly via **RESTful API** (HTTP/1.1) using JSON payloads.
*   **Backend ↔ Database:** Synchronous connection using **SQLAlchemy ORM**.
*   **Backend ↔ AI/Crawlers:** Internal service calls. Heavy crawling jobs run in background threads to avoid blocking the main API.

### **Why is this architecture suitable for the problem?**
*   **Decoupled:** The separation allows the Frontend to be rewritten (e.g., into a Mobile App) without touching the complex AI Backend.
*   **Python Ecosystem:** Python is the native language of AI. Using FastAPI allows seamless integration of PyTorch/TensorFlow libraries within the same process if needed.
*   **Next.js:** Provides Server-Side Rendering (SSR) for initial load speed and SEO, which is important for a content-heavy LMS.

### **What alternatives did I consider and reject?**
*   **Alternative 1: Monolithic Django App:** rejected because decoupling the UI (React) allows for a more dynamic, "app-like" experience than server-side templates.
*   **Alternative 2: Microservices (Separate services for Auth, Crawling, Tutor):** Rejected as "Pre-mature Optimization". For an FYP scale, the complexity of managing multiple containers/networks outweighs the benefits. A Modular Monolith (separate folders, one process) is sufficient.

### **What would break if one component fails?**
*   **Database Down:** Global failure. No login, no content.
*   **OpenAI API Down:** "Graceful Degradation". Core LMS features (viewing courses, manual quizzes) work, but "AI Tutor" and "Generate Questions" features will return error messages.
*   **Crawler Down:** Stale content. Existing materials work, but no new updates until fixed.

---

## 3.2 Responsibility Separation

### **What logic belongs to frontend only?**
*   **View State:** Is the sidebar open? Which tab is active?
*   **Form Validation (Visual):** Is the email format correct? (Immediate feedback).
*   **Data Formatting:** Converting "2023-12-25T12:00:00Z" to "Dec 25, 12:00 PM" for user display.
*   **Route Protection:** Redirecting unauthenticated users to Login (though Backend enforces the actual security).

### **What logic belongs to frontend only?**
*   **Business Rules:** "Cannot delete a course if students are enrolled."
*   **Data Integrity:** Saving to DB, Foreign Key constraints.
*   **Secrets:** API Keys (OpenAI), Database Passwords, JWT Signing Keys.
*   **AI orchestration:** Constructing prompts, managing context window size.

### **What logic must never be on frontend?**
*   **Grading Logic:** Calculating the final score (User could manipulate JavaScript variables).
*   **Access Control Decisions:** "Is this user an Admin?" (Must be verified by Token on server, not just a flag in LocalStorage).
*   **Direct DB Access:** SQL queries.

### **How do I prevent tight coupling?**
*   **DTOs (Data Transfer Objects):** The API returns a strict Schema (Pydantic). If the DB schema changes (column rename), the Pydantic model masks this change, so the Frontend doesn't break.
*   **Environment Config:** API URLs are not hardcoded. They are loaded from `.env` files.

### **Can frontend be replaced without backend changes?**
*   **Yes.** Because the Backend exposes a standard OpenAPI (Swagger) interface. You could build a Flutter Mobile App or a CLI tool that consumes the exact same API endpoints.
