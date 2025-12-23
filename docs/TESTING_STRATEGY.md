# SECTION 12 — TESTING STRATEGY

## 12.1 Testing Levels

### **What types of tests exist?**
1.  **Unit Tests (`backend/tests/services/`):** Test individual functions (e.g., "Does `calculate_score` return 100?"). Isolated from DB.
2.  **Integration Tests (`backend/tests/test_api_*.py`):** Test API Endpoints using `TestClient`. Verifies `Route -> Controller -> Service -> DB` flow.
3.  **End-to-End (E2E) Tests:** (Manual for FYP) Clicking through the frontend to verify the Full Stack works together.

### **What logic is unit tested?**
*   **Services:** `AITutor` prompt generation (Mocking OpenAI).
*   **Models:** Property methods (e.g., `user.is_lecturer`).
*   **Utilities:** Formatters, Date parsers.

### **What endpoints are tested?**
Priority is given to **Critical Paths**:
*   `/auth/login`: Essential for entry.
*   `/courses/*`: Core CRUD logic.
*   `/tutor/*`: Complex AI logic.

---

## 12.2 Methodology

### **How do tests improve confidence?**
*   **Regression Prevention:** If I refactor the "User Model", running `pytest` immediately tells me if I broke the Login flow.
*   **Documentation:** Tests serve as "Live Documentation" showing exactly how an API is expected to be called.

### **What happens when tests fail?**
*   **CI/CD:** The deployment pipeline stops.
*   **Local:** The developer cannot merge until `pytest` returns **GREEN**.
*   **Action:** Read the traceback -> Reproduce locally -> Fix -> Add a new test case for that edge case.

### **How would I test edge cases?**
We actively write tests for "Unhappy Paths":
*   **Empty Inputs:** Sending `{}` to Create Course.
*   **Invalid IDs:** requesting `GET /courses/999999` (Expect 404).
*   **Unauthorized:** Student trying to delete a course (Expect 403).

## 12.3 Test Stack
*   **Runner:** `pytest`
*   **Client:** `fastapi.testclient.TestClient`
*   **Database:** `SQLite` (In-memory/File) for speed during tests, reset via `conftest.py` fixtures.
