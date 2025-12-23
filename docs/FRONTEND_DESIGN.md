# SECTION 4 — FRONTEND DESIGN

## 4.1 High-Level Structure

### **What pages or views exist?**
The application uses the **Next.js App Router** structure:

*   **Public Views:**
    *   `/login` - User authentication.
    *   `/register` - New user signup.
*   **Student Views (`/student`):**
    *   `/student/dashboard` - Overview of enrolled courses, progress, and weak topics.
    *   `/student/course/[id]` - Course details, syllabus, and materials.
    *   `/student/course/[id]/tutor` - Chat interface for AI Tutoring.
*   **Lecturer Views (`/lecturer`):**
    *   `/lecturer/dashboard` - Course management and student supervision.
    *   `/lecturer/course/[id]/edit` - Syllabus editor and material approval.

### **What is the user flow from start to finish?**
1.  **Entry:** User lands on `/login`.
2.  **Auth:** Enters credentials -> specific API call `/api/v1/auth/login` -> receives JWT.
3.  **Routing:** Token stored in `localStorage`. User redirected based on role (`student` -> `/student/dashboard`).
4.  **Interaction:** User views Dashboard -> Clicks Course -> Views Material -> Asks AI Tutor.
5.  **Exit:** User clicks "Sign Out" -> Token cleared -> Redirect to `/login`.

---

## 4.2 State & Communication

### **How is state managed?**
*   **Local State:** We use React's `useState` for page-level data (e.g., `data`, `isLoading`, `error` in `StudentDashboardPage`).
*   **Derived State:** `useMemo` is used for expensive calculations (e.g., summing up weak topics counts).
*   **Global State:** Explicitly avoided (no Redux/Zustand) to keep complexity low. Authentication state is effectively managed via `localStorage` presence.

### **How does frontend handle loading and error states?**
*   **Loading:** Pages initialize with `const [isLoading, setIsLoading] = useState(true)`. UI renders a Skeleton or "Loading..." spinner until data arrival.
*   **Errors:** `try-catch` blocks around API calls set `setError(message)`. The UI conditionally renders a red error alert box if `error` is present.

### **How does frontend communicate with backend?**
*   **Pattern:** A unified wrapper function `apiFetch` in `@/lib/api.ts`.
*   **Mechanism:** Uses standard `fetch`.
*   **Auth Injection:** Automatically injects `Authorization: Bearer <token>` from `localStorage` into every request.
*   **Error Handling:** centralized in `apiFetch`. If API returns 401, it throws an error (page handles redirection).

### **What happens if backend is slow or down?**
*   **Slow:** The "Loading..." state persists. The user sees a spinner.
*   **Down (500/503):** `apiFetch` throws an error. The Page catches it and displays "Unable to load dashboard" to the user, rather than crashing the whole app.

---

## 4.3 Scalability & Usability

### **How is frontend structured for scalability?**
*   **Feature-First Folders:** Code is grouped by domain (`app/student`, `app/lecturer`) rather than file type. This makes "deleting a feature" safe (just delete the folder).
*   **Shared Components:** Reusable UI (Buttons, Cards, Inputs) live in `src/components`, separating "purity" (UI) from "business logic" (Pages).

### **What UI decisions improve usability?**
*   **Immediate Feedback:** Interactive elements (buttons) show active/hover states.
*   **Optimistic UI:** (Planned) UI updates immediately before the server responds (e.g., ticking a checkbox).
*   **Progress Bars:** Visual indicators for course completion.
*   **Role-Specific Design:** Student view focuses on *consumption* (reading/chatting), Lecturer view focuses on *management* (tables/lists).

### **How are reusable components identified?**
*   **Rule of Three:** If a UI pattern (e.g., a "Card" with a title and shadow) appears in 3 places, it is extracted to `src/components/Card.tsx`.
*   **Props Interface:** Components define strict TypeScript interfaces `interface CardProps { ... }` to enforce usage contracts.

### **How would another developer understand this codebase?**
*   **Entry Point:** Start at `app/layout.tsx` (Global wrapper).
*   **Routing:** File system is the router (`app/folder/page.tsx` -> `/folder`).
*   **Data Fetching:** Search for `useEffect` in any `page.tsx`.
*   **Authentication:** Check `lib/api.ts` to see how requests are signed.
