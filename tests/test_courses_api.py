"""
API integration tests for Courses endpoints
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import User, Course
from app.models.user import UserRole
from app.core import security
from app.core.config import settings


def get_auth_token(client: TestClient, email: str, password: str) -> str:
    """Helper to get auth token"""
    response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": email, "password": password}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def create_test_user(db: Session, email: str, password: str, role: UserRole, full_name: str) -> User:
    """Helper to create test user"""
    user = User(
        email=email,
        hashed_password=security.get_password_hash(password),
        full_name=full_name,
        role=role,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


class TestCoursesAPI:
    """API integration tests for courses endpoints"""
    
    def test_create_course_as_lecturer(self, client: TestClient, db: Session):
        """Test lecturer can create a course"""
        lecturer = create_test_user(db, "lecturer1@test.com", "pass123", UserRole.LECTURER, "Lecturer 1")
        token = get_auth_token(client, "lecturer1@test.com", "pass123")
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.post(
            f"{settings.API_V1_STR}/courses/",
            json={
                "code": "TEST101",
                "name": "Test Course",
                "description": "Test description",
                "lecturer_id": lecturer.id
            },
            headers=headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["code"] == "TEST101"
        assert data["name"] == "Test Course"
        assert data["lecturer_id"] == lecturer.id
        assert "id" in data
        assert "created_at" in data
    
    def test_create_course_as_student_forbidden(self, client: TestClient, db: Session):
        """Test student cannot create a course"""
        lecturer = create_test_user(db, "lecturer2@test.com", "pass123", UserRole.LECTURER, "Lecturer 2")
        student = create_test_user(db, "student1@test.com", "pass123", UserRole.STUDENT, "Student 1")
        token = get_auth_token(client, "student1@test.com", "pass123")
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.post(
            f"{settings.API_V1_STR}/courses/",
            json={
                "code": "TEST102",
                "name": "Test Course",
                "lecturer_id": lecturer.id
            },
            headers=headers
        )
        
        assert response.status_code == 403
    
    def test_list_courses_public(self, client: TestClient, db: Session):
        """Test anyone can list courses"""
        lecturer = create_test_user(db, "lecturer3@test.com", "pass123", UserRole.LECTURER, "Lecturer 3")
        token = get_auth_token(client, "lecturer3@test.com", "pass123")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create a course
        client.post(
            f"{settings.API_V1_STR}/courses/",
            json={
                "code": "TEST103",
                "name": "Test Course",
                "lecturer_id": lecturer.id
            },
            headers=headers
        )
        
        # List courses (no auth required, but we'll use auth for consistency)
        response = client.get(f"{settings.API_V1_STR}/courses/", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    def test_get_course_by_id(self, client: TestClient, db: Session):
        """Test getting a specific course"""
        lecturer = create_test_user(db, "lecturer4@test.com", "pass123", UserRole.LECTURER, "Lecturer 4")
        token = get_auth_token(client, "lecturer4@test.com", "pass123")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create course
        create_response = client.post(
            f"{settings.API_V1_STR}/courses/",
            json={
                "code": "TEST104",
                "name": "Test Course",
                "lecturer_id": lecturer.id
            },
            headers=headers
        )
        course_id = create_response.json()["id"]
        
        # Get course
        response = client.get(f"{settings.API_V1_STR}/courses/{course_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == course_id
        assert data["code"] == "TEST104"
    
    def test_update_course_as_lecturer(self, client: TestClient, db: Session):
        """Test lecturer can update their own course"""
        lecturer = create_test_user(db, "lecturer5@test.com", "pass123", UserRole.LECTURER, "Lecturer 5")
        token = get_auth_token(client, "lecturer5@test.com", "pass123")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create course
        create_response = client.post(
            f"{settings.API_V1_STR}/courses/",
            json={
                "code": "TEST105",
                "name": "Test Course",
                "lecturer_id": lecturer.id
            },
            headers=headers
        )
        course_id = create_response.json()["id"]
        
        # Update course
        response = client.put(
            f"{settings.API_V1_STR}/courses/{course_id}",
            json={"name": "Updated Course Name"},
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Course Name"
    
    def test_lecturer_cannot_update_other_lecturer_course(self, client: TestClient, db: Session):
        """Test lecturer cannot update another lecturer's course"""
        lecturer1 = create_test_user(db, "lecturer6@test.com", "pass123", UserRole.LECTURER, "Lecturer 6")
        lecturer2 = create_test_user(db, "lecturer7@test.com", "pass123", UserRole.LECTURER, "Lecturer 7")
        
        token1 = get_auth_token(client, "lecturer6@test.com", "pass123")
        token2 = get_auth_token(client, "lecturer7@test.com", "pass123")
        headers1 = {"Authorization": f"Bearer {token1}"}
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        # Lecturer1 creates course
        create_response = client.post(
            f"{settings.API_V1_STR}/courses/",
            json={
                "code": "TEST106",
                "name": "Test Course",
                "lecturer_id": lecturer1.id
            },
            headers=headers1
        )
        course_id = create_response.json()["id"]
        
        # Lecturer2 tries to update
        response = client.put(
            f"{settings.API_V1_STR}/courses/{course_id}",
            json={"name": "Hacked Course"},
            headers=headers2
        )
        assert response.status_code == 403
    
    def test_delete_course_as_super_admin(self, client: TestClient, db: Session):
        """Test super admin can delete any course"""
        lecturer = create_test_user(db, "lecturer8@test.com", "pass123", UserRole.LECTURER, "Lecturer 8")
        super_admin = create_test_user(db, "admin@test.com", "pass123", UserRole.SUPER_ADMIN, "Super Admin")
        
        token_lecturer = get_auth_token(client, "lecturer8@test.com", "pass123")
        token_admin = get_auth_token(client, "admin@test.com", "pass123")
        headers_lecturer = {"Authorization": f"Bearer {token_lecturer}"}
        headers_admin = {"Authorization": f"Bearer {token_admin}"}
        
        # Lecturer creates course
        create_response = client.post(
            f"{settings.API_V1_STR}/courses/",
            json={
                "code": "TEST107",
                "name": "Test Course",
                "lecturer_id": lecturer.id
            },
            headers=headers_lecturer
        )
        course_id = create_response.json()["id"]
        
        # Super admin deletes
        response = client.delete(
            f"{settings.API_V1_STR}/courses/{course_id}",
            headers=headers_admin
        )
        assert response.status_code == 204
        
        # Verify deleted
        get_response = client.get(f"{settings.API_V1_STR}/courses/{course_id}", headers=headers_admin)
        assert get_response.status_code == 404
    
    def test_lecturer_cannot_delete_course(self, client: TestClient, db: Session):
        """Test lecturer cannot delete courses (only super admin)"""
        lecturer = create_test_user(db, "lecturer9@test.com", "pass123", UserRole.LECTURER, "Lecturer 9")
        token = get_auth_token(client, "lecturer9@test.com", "pass123")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create course
        create_response = client.post(
            f"{settings.API_V1_STR}/courses/",
            json={
                "code": "TEST108",
                "name": "Test Course",
                "lecturer_id": lecturer.id
            },
            headers=headers
        )
        course_id = create_response.json()["id"]
        
        # Try to delete
        response = client.delete(
            f"{settings.API_V1_STR}/courses/{course_id}",
            headers=headers
        )
        assert response.status_code == 403
    
    def test_duplicate_course_code(self, client: TestClient, db: Session):
        """Test cannot create course with duplicate code"""
        lecturer = create_test_user(db, "lecturer10@test.com", "pass123", UserRole.LECTURER, "Lecturer 10")
        token = get_auth_token(client, "lecturer10@test.com", "pass123")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create first course
        client.post(
            f"{settings.API_V1_STR}/courses/",
            json={
                "code": "TEST109",
                "name": "Test Course 1",
                "lecturer_id": lecturer.id
            },
            headers=headers
        )
        
        # Try to create duplicate
        response = client.post(
            f"{settings.API_V1_STR}/courses/",
            json={
                "code": "TEST109",
                "name": "Test Course 2",
                "lecturer_id": lecturer.id
            },
            headers=headers
        )
        assert response.status_code == 409
    
    def test_search_courses(self, client: TestClient, db: Session):
        """Test searching courses by name or code"""
        lecturer = create_test_user(db, "lecturer11@test.com", "pass123", UserRole.LECTURER, "Lecturer 11")
        token = get_auth_token(client, "lecturer11@test.com", "pass123")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create courses
        client.post(
            f"{settings.API_V1_STR}/courses/",
            json={"code": "SEARCH101", "name": "Searchable Course", "lecturer_id": lecturer.id},
            headers=headers
        )
        
        # Search by name
        response = client.get(
            f"{settings.API_V1_STR}/courses/?search=Searchable",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(c["name"] == "Searchable Course" for c in data)
        
        # Search by code
        response = client.get(
            f"{settings.API_V1_STR}/courses/?search=SEARCH101",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(c["code"] == "SEARCH101" for c in data)

