# SECTION 2 — REQUIREMENTS ENGINEERING

## 2.1 Functional Requirements

### **What are the core use cases? (Summary)**
1.  **Authentication:** Users (Student/Lecturer) login to access role-specific dashboards.
2.  **Course Management:** Lecturers create courses and define weekly syllabus topics.
3.  **Automated Crawling:** System searches external sources (YouTube/GitHub) for syllabus topics.
4.  **Material Review:** Lecturers approve/reject AI-crawled materials.
5.  **AI Tutoring:** Students ask questions about course content and receive context-aware answers.
6.  **Progress Tracking:** System tracks weak topics based on student quiz performance.

### **Detailed Use Cases**

| Use Case | Description | Inputs | Expected Outputs | Invalid Input Behavior |
| :--- | :--- | :--- | :--- | :--- |
| **Login** | User authenticates to gain access. | Email, Password | JWT Token, Redirect to Dashboard | Error: "Invalid credentials" (401) |
| **Crawl Topic** | System fetches external resources for a topic. | Topic keywords (e.g., "React Hooks") | List of metadata objects (Video/Repo links) | Log error, return empty list, retry later |
| **Ask Tutor** | Student queries the AI about a concept. | Question string, Course Context (ID) | Text answer, citations, follow-up hints | Error: "Content policy violation" or "Service unavailable" |
| **Approve Material** | Lecturer validates a crawled resource. | Material ID, Status (Approved/Rejected) | Updated Material status in DB | Error: "Material not found" or "Unauthorized" |
| **Take Quiz** | Student answers generated questions. | Quiz answers (MCQ selections) | Score %, Weak topics identified | Error: "Submission incomplete" |

### **What happens when input is invalid?**
*   **API Level:** deeply validated using Pydantic schemas. Returns **422 Unprocessable Entity** with specific field errors (e.g., "Email format invalid").
*   **Logic Level:** Returns **400 Bad Request** (e.g., "Cannot approve material that is already deleted").
*   **LLM Level:** If user input is nonsensical/malicious, the AI Agent refuses to answer (Safety Guardrails).

---

## 2.2 Non-Functional Requirements

### **What performance constraints exist?**
*   **API Latency:** Standard CRUD operations (Login, View Syllabus) must complete in **< 500ms**.
*   **AI Latency:** LLM responses (Tutor/Generation) are allowed **up to 15-30s** due to model inference time, but must show a "Thinking..." state.
*   **Throughput:** System should handle **50 concurrent users** (typical tutorial class size) without crashing.

### **What availability level is acceptable?**
*   **System Uptime:** **99%** during business hours (Lectures/Labs).
*   **External Dependency:** If OpenAI/YouTube API is down, core LMS features (Login, View Syllabus) **must still function**. Graceful degradation for AI features is required.

### **What security requirements exist?**
*   **Authentication:** Industry standard **JWT (JSON Web Tokens)** with expiration.
*   **Password Storage:** **Bcrypt** hashing (never store plain text).
*   **Access Control:** strict **Role-Based Access Control (RBAC)**. Students cannot access Lecturer administrative endpoints.
*   **API Keys:** Server-side secrets (OpenAI Key) must never be exposed to the frontend client.

### **What scalability assumptions am I making?**
*   **Database:** PostgreSQL is sufficient for < 10,000 users. No sharding required yet.
*   **Containerization:** The application is stateless (except for DB/Media), allowing it to run in Docker containers.
*   **Storage:** Local filesystem is used for uploads (for FYP simplicity), assuming disk space is not a limiting factor for the demo.

### **What usability constraints exist?**
*   **Responsiveness:** UI must be usable on **Desktop (1920x1080)** and **Laptop (1366x768)**. Mobile is secondary but functional.
*   **Clarity:** AI explanations must be formatted in **Markdown** (code blocks, bold text) for readability.
*   **Feedback:** Every action (Save, Delete, Submit) must provide a visual toast notification (Success/Error).
