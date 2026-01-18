# SECTION 6 — DATABASE & DATA DESIGN

## 6.1 Schema & Entities

### **Database Infrastructure**

| Environment | Database | Host |
|-------------|----------|------|
| **Local Development** | PostgreSQL 15 | `localhost:5432` |
| **Production** | PostgreSQL 15 | Supabase (Singapore region) |

### **Why did I choose this database type?**
*   **Database:** **PostgreSQL** (both local and production via Supabase).
*   **Reasoning:**
    *   **Relational Integrity:** We need strict relationships (Lecturer -> Course -> Student).
    *   **JSONB Support:** Postgres handles semi-structured data (like Quiz Questions or User Settings) effectively using JSONB columns, offering the best of SQL and NoSQL.
    *   **Vector Search (Future Proof):** Postgres has `pgvector` extension support, which is critical for future RAG optimization if we move vector storage to the DB.
    *   **Supabase:** Provides managed PostgreSQL with automatic backups, connection pooling, and a web dashboard.

### **What are the main entities?**
1.  **User:** Stores authentication info and Roles (`student`, `lecturer`, `super_admin`).
2.  **Course:** The central entity. Links to `User` (Lecturer).
3.  **Syllabus:** Standardizes weekly topics.
4.  **Material:** Crawled or uploaded content (PDFs, Videos).
5.  **QuizAttempt:** Stores student performance metrics (Score, Feedback).
6.  **TopicPerformance:** Aggregated mastery levels (`mastered`, `remedial`) for analytics.

### **How are relationships represented?**
*   **One-to-Many:** `Lecturer` -> `Courses`.
*   **One-to-Many:** `Course` -> `Syllabus`.
*   **Many-to-Many:** `Students` <-> `Courses` (managed via `student_enrollments` association table).
*   **Foreign Keys:** Strictly enforced (e.g., `lecturer_id REFERENCES users(id)`). `ON DELETE` Policies are set (e.g., `CASCADE` for Syllabus when Course is deleted).

---

## 6.2 Performance & Reliability

### **What fields are indexed and why?**
*   **Primary Keys (`id`):** Automatically indexed.
*   **Searchable Fields:** `Course.code` and `User.email` are unique and indexed for fast lookups (O(log n)).
*   **Foreign Keys:** `lecturer_id`, `student_id` are indexed to speed up Joins (e.g., "Find all courses for this lecturer").
*   **Performance:** `TopicPerformance` has a composite index on `(student_id, course_id, week_number)` for fast dashboard loading.

### **How do I ensure data consistency?**
*   **Transactions:** All writes (e.g., "Enroll student and Send Email") happen within an atomic transaction. If one fails, the DB rolls back.
*   **Constraints:**
    *   `UNIQUE(email)` prevents duplicate users.
    *   `NOT NULL` ensures critical data (Password Hash) is never missing.
    *   `Enum(UserRole)` restricts roles to valid values only.

### **What happens when data grows 10×?**
*   **Vertical Scaling:** Postgres handles millions of rows easily on a single standard node.
*   **Pagination:** All "List" APIs (like `GET /courses`) strictly enforce `limit` and `offset` to prevent memory overflows.
*   **Archiving:** Old term data can be moved to an "Archive" table or cold storage (S3) if the DB grows too large.

### **How is schema evolution handled?**
*   **Tool:** **Alembic**.
*   **Process:**
    1.  Modify Python `models/*.py`.
    2.  Run `alembic revision --autogenerate -m "Add column"`.
    3.  Review the generated script.
    4.  Apply with `alembic upgrade head`.
*   *Why?* This provides a version-controlled history of all DB changes, allowing rollbacks (`alembic downgrade`).

---

## 6.3 Data Operations

### **How do I seed test data?**
*   Script: `scripts/seeds/setup_demo.py`
*   Logic: Creates demo users (Admin, Lecturers, Students), courses, syllabus, and sample materials.
*   **Local:** `python scripts/seeds/setup_demo.py`
*   **Production (Fly.io):** `fly ssh console --app fyp-ai-lms-backend -C "python /app/scripts/seeds/setup_demo.py"`

### **What constraints prevent invalid data?**
*   **Database Level:** SQL Constraints (`CHECK score >= 0`).
*   **Application Level Pydantic:** Validates formats (Email, URL) before hitting the DB.

### **How do I back up data?**
*   **Local:** `pg_dump -U jieru_0901 -d lms_db > backup.sql`
*   **Production (Supabase):** Automatic daily backups via Supabase dashboard. Manual export available in Settings → Database → Backups.
*   **Migration Script:** `scripts/migrate_to_supabase_v2.py` can sync local data to production.
