# SECTION 1 — PROBLEM DEFINITION & SCOPE

## 1.1 Problem Understanding

### **What exact problem does this system solve?**
The system solves the **"Static & Generic Learning Problem"** in traditional LMS platforms.
1.  **Static Content:** Course materials become outdated quickly, and lecturers lack the time to manually search for and curate the latest external resources (papers, videos, repos).
2.  **Generic Support:** Students receive generic feedback (e.g., "50/100") without personalized explanations or targeted resource recommendations to address their specific weak topics.

### **Who are the primary users? Secondary users?**
*   **Primary Users:**
    *   **Students:** Need personalized help, 24/7 tutoring, and relevant, up-to-date materials.
    *   **Lecturers:** Need automated help in curating materials and monitoring student progress without increasing their workload.
*   **Secondary Users:**
    *   **Super Admins:** Manage system health, users, and global configurations.

### **What pain points do users currently face without this system?**
*   **For Students (The "Fragmented Learning" Pain):**
    *   They have to leave the LMS to find better explanations on YouTube/Stack Overflow, losing context.
    *   They don't know *why* they are struggling (weak topics) or *what* to study next to fix it.
*   **For Lecturers (The "Bandwidth" Pain):**
    *   Cannot physically provide 1-on-1 tutoring for every student 24/7.
    *   Curating new materials from GitHub/ArXiv for every syllabus topic is too time-consuming.

### **Why is software the correct solution (not a manual or process fix)?**
*   **Scale:** A human cannot crawl thousands of GitHub repos and YouTube videos daily to find the best match for a syllabus topic.
*   **Availability:** A human tutor cannot be available 24/7 for instant Q&A.
*   **Personalization:** A manual process cannot easily track the "weak topics" of hundreds of students individually and map them to specific remedial content.

### **What assumptions am I making about users or data?**
*   **Data Availability:** We assume external platforms (YouTube, GitHub, ArXiv) remain accessible and crawlable.
*   **User Connectivity:** Users have stable internet access to consume streamed content and interact with the AI.
*   **Content Relevance:** We assume that "keyword + semantic search" is sufficient to find high-quality educational content (i.e., the content exists out there).

---

## 1.2 Scope Control

### **What features are in scope?**
*   **Core LMS:** User Auth (JWT), Course/Syllabus CRUD, Enrolment.
*   **Automated Curation:** Crawlers for YouTube, GitHub, ArXiv, OER with Quality Scoring.
*   **AI Intelligence:**
    *   **RAG Tutor:** Context-aware Q&A based on course materials.
    *   **Recommendation Engine:** Semantic matching of external materials to syllabus topics.
*   **Dashboards:** Student (Weakness tracking) and Lecturer (Approval workflow).

### **What features are explicitly out of scope?**
*   **Real-time Collaboration:** No live chat between students, no forums, no peer-review systems.
*   **Native Mobile App:** Web-interface only (responsive), no iOS/Android apps.
*   **Complex Assessment Types:** No file-upload grading (e.g., grading a PDF essay), no plagiarism detection on submissions.
*   **Payment/E-commerce:** No selling of courses or subscription handling.

### **What features could be added in the future but are intentionally excluded now?**
*   **WebSocket/Real-time Notifications:** Live updates when a task finishes (currently polling or refresh).
*   **Advanced Analytics:** Predictive modelling for dropout rates.
*   **Plagiarism Checkers:** Checking code submissions against peers.
*   **SSO Integration:** Google/Microsoft login (kept to basic Email/Password for FYP simplicity).

### **What happens if a stakeholder asks for a new feature late?**
*   **The Defense:** "This feature is valuable but falls under [Future Enhancement X]. To ensure the robustness of the Core AI features (Tutor/Crawler), which are the primary research objectives, this will be documented for V2."

### **What is the minimum viable system I can defend?**
*   A system that can:
    1.  Take a Syllabus Topic (e.g., "React Hooks").
    2.  Crawls **one** relevant video/repo automatically.
    3.  A student can ask the AI Tutor a question about it and get a correct answer.
    *   *Everything else (fancy dashboards, complex grading) is secondary to this core loop.*
