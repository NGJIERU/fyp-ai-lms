# SECTION 5 — BACKEND DESIGN

## 5.1 API Design

### **What APIs exist?**
The backend exposes a RESTful API versioned at `/api/v1`. Key router modules include:
*   **Auth (`/auth`):** Login (OAuth2 Password flw), Registration, Token refreshing.
*   **Courses (`/courses`):** CRUD for Courses, Enrollment management.
*   **Materials (`/materials`):** Uploading files, crawling requests, approval workflows.
*   **Tutor (`/tutor`):** Chat endpoints for AI interaction (`/chat`, `/explain`).
*   **Analytics (`/dashboard`):** Aggregated data for student/lecturer dashboards.

### **What HTTP methods are used and why?**
We adhere to standard REST semantics:
*   **GET**: Retrieve data (Courses, Syllabus). Safe & Idempotent.
*   **POST**: Create resources (New Course, New Crawl Job) or complex actions (Chat).
*   **PUT**: Update existing resources (Edit Syllabus).
*   **DELETE**: Remove resources (Unenroll Student).

### **What request validation exists?**
*   **Pydantic Models:** Every endpoint uses Pydantic schemas (e.g., `CourseCreate`) to strictly validate JSON bodies.
    *   *Example:* If `email` is not a valid email format, Pydantic raises a 422 error automatically.
*   **Type Hints:** Python type hints ensure internal consistency.

### **What response format is returned?**
All responses are **JSON**.
*   **Success:** 200/201 status code with data object.
*   **Error:** standardized error object: `{"detail": "Error message"}`.

### **How are errors standardized?**
*   **HTTP Exceptions:** We use FastAPI's `HTTPException`.
*   **Common Codes:**
    *   `401 Unauthorized` (Missing/Invalid Token)
    *   `403 Forbidden` (Student trying to access Lecturer API)
    *   `404 Not Found` (Resource doesn't exist)
    *   `422 Validation Error` (Bad Input)

---

## 5.2 Business Logic

### **Where is business logic located?**
*   **Services Layer (`app/services`):** Complex logic (AI interaction, Crawling orchestration) resides here.
    *   *Example:* `AITutor` class in `app/services/tutor/ai_tutor.py` handles the prompt engineering and RAG retrieval, independent of the HTTP request.
*   **CRUD Utilities:** Simple database operations are handled directly in endpoints or helper CRUD functions.

### **Why is it separated from controllers?**
*   **Testability:** We can test `AITutor.explain_concept()` in a unit test without mocking an entire HTTP request context.
*   **Reusability:** The same logic (e.g., "Summarize this PDF") might be triggered by a REST API call OR a background Celery worker.

### **How do services interact with models?**
*   **SQLAlchemy ORM:** Services receive a `db: Session` object. They query and manipulate Database Models (`app/models`) directly.
*   **DTO Conversion:** proper separation ensures Services return internal objects or dictionaries, which the API layer then converts to Pydantic Schemas for the response.

### **How would I test logic without HTTP?**
*   Since logic is in pure Python classes (like `AITutor`), we can write standard `pytest` scripts that instantiate these classes with a mock Database session and call their methods directly.
