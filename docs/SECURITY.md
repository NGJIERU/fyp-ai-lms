# SECTION 11 — SECURITY

## 11.1 Authentication & Authorization

### **How is authentication handled?**
*   **Mechanism:** **Stateless JWT (JSON Web Tokens)**.
*   **Flow:**
    1.  User POSTs credentials to `/api/v1/auth/login` (OAuth2 Password Flow).
    2.  Server verifies hash (Bcrypt).
    3.  Server signs a JWT (`sub=user_id`, `exp=30days`) using `HS256`.
    4.  Client stores JWT in `localStorage` and sends it via `Authorization: Bearer <token>` header.

### **How is authorization enforced?**
*   **RBAC (Role-Based Access Control):**
    *   **Dependency Injection:** We use FastAPI `Depends()` to inject permission checks.
    *   `get_current_user`: Verifies Token validity.
    *   `get_current_lecturer`: Checks if `user.role == 'lecturer'`.
    *   `get_current_active_superuser`: Checks if `user.role == 'super_admin'`.
*   **Rule:** Every protected endpoint **must** include one of these dependencies.

---

## 11.2 Application Security

### **How do I protect APIs?**
*   **CORS (Cross-Origin Resource Sharing):** Configured in `app/main.py`. Only allow requests from trusted domains (e.g., `localhost:3000` in dev).
*   **Rate Limiting:** (Planned) Middleware to block IPs making >100 req/min.
*   **Validation:** Pydantic schemas reject extra fields / invalid types before code execution.

### **How do I validate input?**
*   **Strict Schemas:** We define `class UserCreate(BaseModel): email: EmailStr`.
*   **Sanitization:** The ORM (SQLAlchemy) automatically escapes strings, preventing **SQL Injection**.
*   **HTML Escaping:** React automatically escapes unsafe HTML in the frontend to prevent **XSS**.

### **What common vulnerabilities exist (and mitigation)?**
1.  **SQL Injection:** Mitigated by SQLAlchemy ORM parameters.
2.  **XSS (Cross-Site Scripting):** Mitigated by React's default output encoding.
3.  **CSRF (Cross-Site Request Forgery):** Mitigated because we use **Authorization Headers** (Bearer Token) instead of Cookies for API access. Browsers do not automatically send Headers.

---

## 11.3 Data Security

### **How do I secure secrets?**
*   **Environment Variables:** Passwords/Keys are injected via `.env`.
*   **Code Scanning:** `.gitignore` ensures they are never pushed to GitHub.
*   **Action:** If a secret is committed, it is considered **compromised** and must be rotated immediately.

### **What happens if a token is leaked?**
1.  **Expiration:** Tokens expire automatically after the set duration (30 days currently).
2.  **Revocation:** Since JWTs are stateless, instant revocation is hard.
    *   *Mitigation:* We can implement a "Token Blocklist" in Redis (future work) or simply **change the user's password**, which invalidates the "signing key" concept logic if we encoded password-version in the token (advanced).
    *   *Current Architecture:* Changing password does not invalidate individual JWTs immediately, but prevents new logins.
