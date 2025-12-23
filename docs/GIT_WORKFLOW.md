# SECTION 8 — GIT & VERSION CONTROL

## 8.1 Strategy & Conventions

### **What is my branching strategy?**
We use a simplified **Feature Branch Workflow**:
1.  **Main Branch (`main`):** Always deployable. Contains stable, reviewed code.
2.  **Feature Branches (`feature/name`):** Created for every new task (e.g., `feature/ai-tutor-api`). Only merged into `main` via Pull Request.
3.  **Fix Branches (`fix/bug-name`):** For hotfixes or bug repairs.

### **How often do I commit?**
*   **Atomic Commits:** Commit whenever a single logical unit of work is complete (e.g., "Add Login Form UI" is one commit; "Connect Login to API" is another).
*   **Frequency:** At least once per hour of active coding. Never leave a day's work uncommitted.

### **What makes a good commit message?**
We follow the **Conventional Commits** specification:
*   `feat: add new AI tutor endpoint`
*   `fix: resolve null pointer in user dashboard`
*   `docs: update API documentation`
*   `refactor: simplify auth middleware logic`
*   **Why?** This allows automatic changelog generation and easy history scanning.

---

## 8.2 Operations & Safety

### **How do I recover from a bad commit?**
*   **Local (Not pushed):** `git reset --soft HEAD~1` (Undoes the commit but keeps changes in your files).
*   **Public (Pushed):** `git revert <commit-hash>` (Creates a *new* commit that is the exact opposite of the bad one). **NEVER** force push (`git push -f`) to shared branches like `main`.

### **What files must never be tracked?**
Defined in `.gitignore`:
*   **Secrets:** `.env`, `.env.local`, `*.pem`, `*.key`.
*   **Dependencies:** `node_modules/`, `venv/`, `.venv/`.
*   **Build Artifacts:** `.next/`, `dist/`, `build/`, `__pycache__/`, `*.pyc`.
*   **System Files:** `.DS_Store`, `Thumbs.db`.

### **How do I review changes before merging?**
1.  **Self-Review:** Run `git diff` or use the VS Code Source Control view to see exactly what lines changed.
2.  **Automated Checks:** Ensure local tests pass (`pytest` / `npm run build`).
3.  **Pull Request (PR):** Compare `feature-branch` vs `main` on GitHub/GitLab. Check for logic errors, clean code style, and security risks.

### **How would I onboard a contributor?**
1.  **Clone:** `git clone <repo-url>`
2.  **Branch:** `git checkout -b feature/my-first-contribution`
3.  **Code & Commit:** Following the conventions above.
4.  **Push:** `git push -u origin feature/my-first-contribution`
5.  **PR:** Open a Pull Request for review.
