# Test Suite Documentation

## Overview

Comprehensive test suite for Course & Syllabus Management module covering:
- Unit tests for models
- API integration tests
- Authorization tests
- Version control tests

## Test Files

### 1. `test_models.py` - Unit Tests
Tests for database models (Course, Syllabus):
- Model creation and relationships
- Database constraints (unique codes, week number validation)
- Cascade delete behavior
- Version control logic

**Key Tests:**
- ✅ Course creation and uniqueness
- ✅ Syllabus week number constraints (1-14)
- ✅ Unique active syllabus per week
- ✅ Syllabus versioning
- ✅ Cascade delete (course → syllabus)

### 2. `test_courses_api.py` - Courses API Tests
Tests for `/api/v1/courses/` endpoints:
- CRUD operations
- Authorization (student, lecturer, super admin)
- Search and filtering
- Duplicate prevention

**Key Tests:**
- ✅ Create course (lecturer only)
- ✅ List courses (public)
- ✅ Get course by ID
- ✅ Update course (own courses only for lecturers)
- ✅ Delete course (super admin only)
- ✅ Duplicate course code prevention
- ✅ Search functionality

### 3. `test_syllabus_api.py` - Syllabus API Tests
Tests for `/api/v1/syllabus/` endpoints:
- CRUD operations
- Bulk operations
- Version control
- Authorization

**Key Tests:**
- ✅ Create syllabus (lecturer only)
- ✅ List syllabus (students see only active)
- ✅ Update syllabus (creates new version)
- ✅ Version history
- ✅ Bulk create (14 weeks)
- ✅ Soft delete (deactivate)
- ✅ Week number validation (1-14)

## Running Tests

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Test File
```bash
pytest tests/test_models.py -v
pytest tests/test_courses_api.py -v
pytest tests/test_syllabus_api.py -v
```

### Run Specific Test Class
```bash
pytest tests/test_courses_api.py::TestCoursesAPI -v
```

### Run Specific Test
```bash
pytest tests/test_courses_api.py::TestCoursesAPI::test_create_course_as_lecturer -v
```

### Run with Coverage
```bash
pytest tests/ --cov=app --cov-report=html
```

## Test Coverage

### Models (Unit Tests)
- ✅ Course model creation and validation
- ✅ Syllabus model creation and validation
- ✅ Relationship integrity
- ✅ Constraint enforcement
- ✅ Cascade operations

### API Endpoints (Integration Tests)
- ✅ POST /courses/ - Create course
- ✅ GET /courses/ - List courses
- ✅ GET /courses/{id} - Get course
- ✅ PUT /courses/{id} - Update course
- ✅ DELETE /courses/{id} - Delete course
- ✅ POST /syllabus/ - Create syllabus
- ✅ GET /syllabus/ - List syllabus
- ✅ POST /syllabus/bulk - Bulk create
- ✅ PUT /syllabus/{id} - Update syllabus (versioning)
- ✅ GET /syllabus/{id}/versions - Version history
- ✅ DELETE /syllabus/{id} - Soft delete

### Authorization Tests
- ✅ Students: Read-only access
- ✅ Lecturers: Full CRUD for own courses
- ✅ Super Admin: Full CRUD for all courses
- ✅ Cross-lecturer access prevention

### Version Control Tests
- ✅ Version increment on update
- ✅ Old versions marked inactive
- ✅ Version history retrieval
- ✅ Only one active version per week

## Test Database

Tests use SQLite in-memory database (`test.db`) for fast execution.
- Database is created fresh for each test
- All tables are dropped after each test
- No data persists between tests

## Notes

- All tests are isolated (function scope)
- Each test creates its own test data
- Tests can run in any order
- No external dependencies required

