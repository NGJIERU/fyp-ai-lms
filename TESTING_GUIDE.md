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

## 📚 Additional Resources

- See `tests/README_TESTS.md` for detailed test documentation
- FastAPI testing guide: https://fastapi.tiangolo.com/tutorial/testing/
- Pytest documentation: https://docs.pytest.org/

