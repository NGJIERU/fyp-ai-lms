"""
Integration tests for all API endpoints
Tests the complete flow from authentication to all module endpoints
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.core.security import get_password_hash
from app.models import User, UserRole, Course, Syllabus, Material

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module")
def client():
    """Create test client with fresh database."""
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def db_session():
    """Get database session for setup."""
    db = TestingSessionLocal()
    yield db
    db.close()


@pytest.fixture(scope="module")
def setup_test_data(db_session):
    """Setup test users, courses, and materials."""
    # Create admin user
    admin = User(
        email="admin@test.com",
        hashed_password=get_password_hash("admin123"),
        full_name="Test Admin",
        role=UserRole.SUPER_ADMIN,
        is_active=True
    )
    db_session.add(admin)
    
    # Create lecturer
    lecturer = User(
        email="lecturer@test.com",
        hashed_password=get_password_hash("lecturer123"),
        full_name="Test Lecturer",
        role=UserRole.LECTURER,
        is_active=True
    )
    db_session.add(lecturer)
    
    # Create student
    student = User(
        email="student@test.com",
        hashed_password=get_password_hash("student123"),
        full_name="Test Student",
        role=UserRole.STUDENT,
        is_active=True
    )
    db_session.add(student)
    db_session.commit()
    
    # Create course
    course = Course(
        code="TEST101",
        name="Test Course",
        description="A test course",
        lecturer_id=lecturer.id
    )
    db_session.add(course)
    db_session.commit()
    
    # Create syllabus
    syllabus = Syllabus(
        course_id=course.id,
        week_number=1,
        topic="Introduction to Testing",
        content="Learn about unit testing and integration testing.",
        version=1,
        is_active=True,
        created_by=lecturer.id
    )
    db_session.add(syllabus)
    db_session.commit()
    
    # Create material
    material = Material(
        title="Test Material",
        url="https://example.com/test",
        source="Test Source",
        type="article",
        description="A test material",
        quality_score=0.8,
        content_hash="test_hash_123"
    )
    db_session.add(material)
    db_session.commit()
    
    return {
        "admin": admin,
        "lecturer": lecturer,
        "student": student,
        "course": course,
        "syllabus": syllabus,
        "material": material
    }


class TestAuthentication:
    """Test authentication endpoints."""
    
    def test_login_success(self, client, setup_test_data):
        """Test successful login."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "admin@test.com", "password": "admin123"}
        )
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"
    
    def test_login_wrong_password(self, client, setup_test_data):
        """Test login with wrong password."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "admin@test.com", "password": "wrongpassword"}
        )
        assert response.status_code == 400
    
    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "nobody@test.com", "password": "password"}
        )
        assert response.status_code == 400


class TestUserEndpoints:
    """Test user management endpoints."""
    
    @pytest.fixture
    def admin_token(self, client, setup_test_data):
        """Get admin authentication token."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "admin@test.com", "password": "admin123"}
        )
        return response.json()["access_token"]
    
    @pytest.fixture
    def student_token(self, client, setup_test_data):
        """Get student authentication token."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "student@test.com", "password": "student123"}
        )
        return response.json()["access_token"]
    
    def test_get_current_user(self, client, admin_token):
        """Test getting current user info."""
        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert response.json()["email"] == "admin@test.com"
    
    def test_list_users_admin_only(self, client, student_token):
        """Test that only admins can list users."""
        response = client.get(
            "/api/v1/users/",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == 400  # Not enough privileges


class TestCourseEndpoints:
    """Test course management endpoints."""
    
    @pytest.fixture
    def lecturer_token(self, client, setup_test_data):
        """Get lecturer authentication token."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "lecturer@test.com", "password": "lecturer123"}
        )
        return response.json()["access_token"]
    
    def test_list_courses(self, client, lecturer_token):
        """Test listing courses."""
        response = client.get(
            "/api/v1/courses/",
            headers={"Authorization": f"Bearer {lecturer_token}"}
        )
        assert response.status_code == 200
        assert len(response.json()) >= 1
    
    def test_get_course(self, client, lecturer_token, setup_test_data):
        """Test getting a specific course."""
        course_id = setup_test_data["course"].id
        response = client.get(
            f"/api/v1/courses/{course_id}",
            headers={"Authorization": f"Bearer {lecturer_token}"}
        )
        assert response.status_code == 200
        assert response.json()["code"] == "TEST101"


class TestSyllabusEndpoints:
    """Test syllabus management endpoints."""
    
    @pytest.fixture
    def lecturer_token(self, client, setup_test_data):
        """Get lecturer authentication token."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "lecturer@test.com", "password": "lecturer123"}
        )
        return response.json()["access_token"]
    
    def test_list_syllabus(self, client, lecturer_token, setup_test_data):
        """Test listing syllabus entries."""
        course_id = setup_test_data["course"].id
        response = client.get(
            f"/api/v1/syllabus/?course_id={course_id}",
            headers={"Authorization": f"Bearer {lecturer_token}"}
        )
        assert response.status_code == 200
        assert len(response.json()) >= 1
    
    def test_create_syllabus(self, client, lecturer_token, setup_test_data):
        """Test creating a syllabus entry."""
        course_id = setup_test_data["course"].id
        response = client.post(
            "/api/v1/syllabus/",
            headers={"Authorization": f"Bearer {lecturer_token}"},
            json={
                "course_id": course_id,
                "week_number": 2,
                "topic": "Advanced Testing",
                "content": "Learn about advanced testing techniques."
            }
        )
        assert response.status_code == 201
        assert response.json()["topic"] == "Advanced Testing"


class TestMaterialEndpoints:
    """Test material management endpoints."""
    
    @pytest.fixture
    def lecturer_token(self, client, setup_test_data):
        """Get lecturer authentication token."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "lecturer@test.com", "password": "lecturer123"}
        )
        return response.json()["access_token"]
    
    def test_list_materials(self, client, lecturer_token):
        """Test listing materials."""
        response = client.get(
            "/api/v1/materials/",
            headers={"Authorization": f"Bearer {lecturer_token}"}
        )
        assert response.status_code == 200
    
    def test_search_materials(self, client, lecturer_token):
        """Test searching materials."""
        response = client.get(
            "/api/v1/materials/search?query=test",
            headers={"Authorization": f"Bearer {lecturer_token}"}
        )
        assert response.status_code == 200


class TestTutorEndpoints:
    """Test AI tutor endpoints."""
    
    @pytest.fixture
    def student_token(self, client, setup_test_data):
        """Get student authentication token."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "student@test.com", "password": "student123"}
        )
        return response.json()["access_token"]
    
    def test_check_mcq_answer(self, client, student_token):
        """Test MCQ answer checking."""
        response = client.post(
            "/api/v1/tutor/check-answer",
            headers={"Authorization": f"Bearer {student_token}"},
            json={
                "question_type": "mcq",
                "question": {
                    "question": "What is 2+2?",
                    "options": ["A) 3", "B) 4", "C) 5"],
                    "correct_answer": "B",
                    "explanation": "Basic arithmetic"
                },
                "student_answer": "B",
                "mode": "practice"
            }
        )
        assert response.status_code == 200
        assert response.json()["is_correct"] == True
    
    def test_check_mcq_wrong_answer(self, client, student_token):
        """Test MCQ with wrong answer."""
        response = client.post(
            "/api/v1/tutor/check-answer",
            headers={"Authorization": f"Bearer {student_token}"},
            json={
                "question_type": "mcq",
                "question": {
                    "question": "What is 2+2?",
                    "options": ["A) 3", "B) 4", "C) 5"],
                    "correct_answer": "B"
                },
                "student_answer": "A",
                "mode": "practice"
            }
        )
        assert response.status_code == 200
        assert response.json()["is_correct"] == False
        assert "correct_answer" in response.json()  # Practice mode shows answer


class TestAdminEndpoints:
    """Test admin endpoints."""
    
    @pytest.fixture
    def admin_token(self, client, setup_test_data):
        """Get admin authentication token."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "admin@test.com", "password": "admin123"}
        )
        return response.json()["access_token"]
    
    @pytest.fixture
    def student_token(self, client, setup_test_data):
        """Get student authentication token."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "student@test.com", "password": "student123"}
        )
        return response.json()["access_token"]
    
    def test_get_system_stats(self, client, admin_token):
        """Test getting system statistics."""
        response = client.get(
            "/api/v1/admin/stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert "total_users" in response.json()
        assert "total_courses" in response.json()
    
    def test_admin_only_access(self, client, student_token):
        """Test that admin endpoints require admin role."""
        response = client.get(
            "/api/v1/admin/stats",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == 400  # Not enough privileges
    
    def test_list_users_as_admin(self, client, admin_token):
        """Test listing users as admin."""
        response = client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert len(response.json()) >= 3  # At least admin, lecturer, student


class TestDashboardEndpoints:
    """Test dashboard endpoints."""
    
    @pytest.fixture
    def student_token(self, client, setup_test_data):
        """Get student authentication token."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "student@test.com", "password": "student123"}
        )
        return response.json()["access_token"]
    
    @pytest.fixture
    def lecturer_token(self, client, setup_test_data):
        """Get lecturer authentication token."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "lecturer@test.com", "password": "lecturer123"}
        )
        return response.json()["access_token"]
    
    def test_student_dashboard(self, client, student_token):
        """Test student dashboard endpoint."""
        response = client.get(
            "/api/v1/dashboard/student",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == 200
        assert "student_id" in response.json()
        assert "enrolled_courses" in response.json()
    
    def test_lecturer_dashboard(self, client, lecturer_token):
        """Test lecturer dashboard endpoint."""
        response = client.get(
            "/api/v1/dashboard/lecturer",
            headers={"Authorization": f"Bearer {lecturer_token}"}
        )
        assert response.status_code == 200
        assert "lecturer_id" in response.json()
        assert "courses" in response.json()
