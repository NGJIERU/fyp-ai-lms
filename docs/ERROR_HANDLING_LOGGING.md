# SECTION 10 — ERROR HANDLING & LOGGING

## 10.1 Error Strategy

### **What types of errors can occur?**
1.  **Client Errors (4xx):**
    *   `400 Bad Request`: Logic violation (e.g., "Cannot delete a course with active students").
    *   `401 Unauthorized`: Missing or invalid JWT.
    *   `403 Forbidden`: Valid user but insufficient permissions (Student trying to create a course).
    *   `404 Not Found`: Resource ID does not exist.
    *   `422 Validation Error`: Input data does not match the Pydantic schema (handled automatically by FastAPI).
2.  **Server Errors (5xx):**
    *   `500 Internal Server Error`: Unhandled exceptions (e.g., Database connection lost, Null Pointer).
    *   `503 Service Unavailable`: External dependency (OpenAI API) is down.

### **How are client vs server errors differentiated?**
*   **Client Errors:** Returned with a helpful `detail` message in JSON. The frontend displays this to the user (e.g., via a Toast notification).
*   **Server Errors:** The generic message "Internal Server Error" is returned to the user to avoid leaking stack traces. The detailed traceback is logged to the server console for developers.

---

## 10.2 Logging Standards

### **How are errors logged?**
We use the standard Python `logging` module.
*   **Format:** `TIMESTAMP | LEVEL | MODULE | MESSAGE`
    *   `2023-12-25 10:00:00 | INFO | app.main | Server started`
    *   `2023-12-25 10:05:00 | ERROR | app.services.ai_tutor | OpenAI API connection timed out`
*   **Levels:**
    *   `INFO`: Normal business events (User Login, Course Created).
    *   `WARNING`: Recoverable issues (Crawler found a broken link).
    *   `ERROR`: Operation failed (Database write error).

### **What information must never be logged?**
To protect security and privacy, the following are **strictly forbidden** in logs:
1.  **Passwords:** Plain text passwords.
2.  **API Keys:** OpenAI keys or AWS secrets.
3.  **PII:** Personally Identifiable Information (Full emails, home addresses) in unmasked form, unless necessary for debugging specific user issues (and even then, use IDs preferred).
4.  **JWT Tokens:** The full bearer token string.

### **How do logs help debugging?**
*   **Correlation:** Every request includes the User ID (if auth). We can filter logs by `user_id=123` to see their entire session history.
*   **Traceability:** If the AI Tutor fails, the log shows exactly which step failed (Retrieval vs Generation) and the raw error from OpenAI.

### **How would I trace a production bug?**
1.  **Report:** User reports "I get an error when asking the tutor."
2.  **Logs:** SSH into the server or view Docker logs: `docker-compose logs --tail=100 backend`.
3.  **Search:** Grep for `ERROR` and the timestamp.
4.  **Analyze:** Read the stack trace to identify the file and line number.
