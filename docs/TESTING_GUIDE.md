# Testing Guide - Course & Syllabus Management

## ✅ Test Suite Complete!

Comprehensive test suite has been created covering all aspects of the Course & Syllabus Management module.

## 📁 Test Files Created

1. **`tests/test_models.py`** - Unit tests for database models
2. **`tests/test_courses_api.py`** - API integration tests for courses endpoints
3. **`tests/test_syllabus_api.py`** - API integration tests for syllabus endpoints
4. **`tests/README_TESTS.md`** - Detailed test documentation

## 🚀 Quick Start

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Test Suites
```bash
# Unit tests (models)
pytest tests/test_models.py -v

# Courses API tests
pytest tests/test_courses_api.py -v

# Syllabus API tests
pytest tests/test_syllabus_api.py -v
```

### Run with Coverage
```bash
pytest tests/ --cov=app --cov-report=html
```

## 📊 Test Coverage

### ✅ Unit Tests (test_models.py)
- Course model creation and validation
- Syllabus model creation and validation
- Database constraints (unique codes, week validation)
- Relationship integrity
- Cascade delete operations
- Version control logic

### ✅ Courses API Tests (test_courses_api.py)
- ✅ Create course (lecturer/super admin only)
- ✅ List courses (public, with search/filter)
- ✅ Get course by ID
- ✅ Update course (own courses only for lecturers)
- ✅ Delete course (super admin only)
- ✅ Duplicate course code prevention
- ✅ Authorization checks (student/lecturer/super admin)

### ✅ Syllabus API Tests (test_syllabus_api.py)
- ✅ Create syllabus (lecturer/super admin only)
- ✅ List syllabus (students see only active)
- ✅ Bulk create (14 weeks at once)
- ✅ Update syllabus (creates new version)
- ✅ Version history retrieval
- ✅ Soft delete (deactivate)
- ✅ Week number validation (1-14)
- ✅ Duplicate active syllabus prevention
- ✅ Authorization checks

## 🔐 Authorization Tests Included

### Student Role
- ✅ Can view courses
- ✅ Can view active syllabus only
- ✅ Cannot create/update/delete courses
- ✅ Cannot create/update/delete syllabus

### Lecturer Role
- ✅ Can create courses
- ✅ Can create syllabus for own courses
- ✅ Can update own courses/syllabus
- ✅ Cannot update other lecturers' courses/syllabus
- ✅ Cannot delete courses

### Super Admin Role
- ✅ Can create/update/delete any course
- ✅ Can create/update/delete any syllabus
- ✅ Full access to all operations

## 📝 Version Control Tests

- ✅ Version increment on syllabus update
- ✅ Old versions marked inactive
- ✅ Version history retrieval
- ✅ Only one active version per week
- ✅ Cannot update inactive versions

## 🧪 Testing the API Manually

### Using FastAPI Docs
1. Start the server:
   ```bash
   uvicorn app.main:app --reload
   ```

2. Open browser: `http://localhost:8000/docs`

3. Test endpoints:
   - **POST** `/api/v1/courses/` - Create course
   - **GET** `/api/v1/courses/` - List courses
   - **GET** `/api/v1/courses/{id}` - Get course
   - **PUT** `/api/v1/courses/{id}` - Update course
   - **DELETE** `/api/v1/courses/{id}` - Delete course
   - **POST** `/api/v1/syllabus/` - Create syllabus
   - **POST** `/api/v1/syllabus/bulk` - Bulk create
   - **GET** `/api/v1/syllabus/?course_id={id}` - List syllabus
   - **PUT** `/api/v1/syllabus/{id}` - Update syllabus
   - **GET** `/api/v1/syllabus/{id}/versions` - Version history

### Test Authorization
1. Create users with different roles
2. Login to get tokens
3. Try accessing endpoints with different roles
4. Verify permissions are enforced

## 📈 Test Statistics

- **Total Test Files**: 3
- **Total Test Cases**: ~30+
- **Coverage**: Models, API endpoints, Authorization, Version control

## 🎯 Next Steps

1. **Run the test suite** to verify everything works
2. **Test manually** using FastAPI docs
3. **Add more tests** as needed for edge cases
4. **Set up CI/CD** to run tests automatically

## Additional Resources

- See `tests/README_TESTS.md` for detailed test documentation
- FastAPI testing guide: https://fastapi.tiangolo.com/tutorial/testing/
- Pytest documentation: https://docs.pytest.org/

---

## AI Personalization & Bundles

### 1. Student Personalization & Study Bundles

**Pre‑requisites**

- Backend running on `http://127.0.0.1:8000`.
- Frontend running on the configured port.
- Seed data:
  - `seed_demo_data.py` and `seed_courses_syllabus.py` executed.
  - Optional: some approved materials for lecturer courses (via `/lecturer/materials` and/or `scripts/auto_map_materials.py`).

**Test accounts**

- Student: `student1@example.com` / `student123`
- Lecturer: `lecturer@example.com` / `drlecturer123`

> See `seed_demo_data.py` for the full list if these differ.

#### 1.1 Student Course Personalization

1. Log in as a **student**.
2. Go to `/student/dashboard` and click into a course card (navigates to `/student/course/[courseId]`).
3. Verify:
   - Top stats: Overall score, weeks completed, materials viewed, weak topics count.
   - **Weekly progress** shows each week, status, and practice/tutor buttons.
4. Scroll to **“AI picked for you”**:
   - If you haven’t done much activity yet, expect:
     > "No personalized recommendations yet—complete a few practice questions to get tailored suggestions."
   - After using **Practice quiz** and **Ask AI tutor** for a few weeks, refresh:
     - You should see cards with:
       - Material title, week number, topic.
       - Reasons text (weak topics, recency, etc.).
       - Score and similarity percentages.
5. Test rating:
   - Click **👍 Helpful** or **👎 Not for me** on one of the personalized cards.
   - This calls:
     - `POST /api/v1/materials/{material_id}/rate`
     - `GET /api/v1/materials/{material_id}/ratings/summary`
   - You should see counts below the buttons, e.g. `1↑ / 0↓`.
   - Click the opposite button and verify the summary updates.

#### 1.2 Student Study Bundles

1. On the same course page, find the **“Study bundles”** section.
   - If no bundles:
     > "No bundles yet. Approve materials and generate recommendations to see kits here."
2. After you have approved materials for that course/week (see lecturer flow below) and generated recommendations, refresh the page:
   - Each bundle shows:
     - `Week X: topic`
     - A short summary sentence.
     - A list of materials with titles, sources, and **Open ↗** links.
3. Click one of the resource links and verify it opens in a new tab.

### 2. Lecturer Bundles & Rating Insights

#### 2.1 Generate / Approve Recommendations

1. Log in as **lecturer** (`lecturer@example.com` / `drlecturer123`).
2. Go to `/lecturer/materials`:
   - Select a course and optionally a week.
   - Use auto‑map or your own process to create pending material mappings.
   - Approve several materials per week.
3. Optionally hit `/api/v1/recommendations/course/{course_id}/week/{week_number}` to confirm recommendations exist.
4. Ask students (or use multiple student accounts) to open and rate materials via the student "AI picked for you" panel.

#### 2.2 Lecturer Dashboard Bundles

1. As lecturer, open `/lecturer/dashboard`.
2. In the **summary cards**, verify existing values are still correct: courses, total students, average class score, pending approvals.
3. In the right column, verify the **Study bundles** panel:
   - For courses with approved materials and recommendations, you should see entries with:
     - Course code/name.
     - `Week X: topic`.
     - A short summary.
     - A list of resources with **Open ↗** links.
   - If there are no bundles:
     > "No bundles yet. Approve materials and generate recommendations to see kits here."

#### 2.3 Lecturer Rating Insights

1. On `/lecturer/dashboard`, in the right column, verify the **Low‑rated materials** section:
   - Items only show once enough ratings exist (≥ 3 per material).
2. For each entry, verify:
   - Title and course name match an actual material & course.
   - Counts reflect student behavior, e.g. `X↑ / Y↓ (N ratings)`.
   - "Avg rating" displays a value between −1 and +1.
3. Optionally compare with raw data:
   - Call `/api/v1/materials/{id}/ratings/summary` for one of the materials and verify the lecturer view matches.
