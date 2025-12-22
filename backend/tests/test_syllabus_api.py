"""
API integration tests for Syllabus endpoints
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import User, Course, Syllabus
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


def create_test_course(db: Session, lecturer_id: int, code: str = "TEST101", name: str = "Test Course") -> Course:
    """Helper to create test course"""
    course = Course(code=code, name=name, lecturer_id=lecturer_id)
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


class TestSyllabusAPI:
    """API integration tests for syllabus endpoints"""
    
    def test_create_syllabus_as_lecturer(self, client: TestClient, db: Session):
        """Test lecturer can create syllabus"""
        lecturer = create_test_user(db, "lecturer1@test.com", "pass123", UserRole.LECTURER, "Lecturer 1")
        course = create_test_course(db, lecturer.id, "SYL101", "Syllabus Course")
        token = get_auth_token(client, "lecturer1@test.com", "pass123")
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.post(
            f"{settings.API_V1_STR}/syllabus/",
            json={
                "course_id": course.id,
                "week_number": 1,
                "topic": "Introduction",
                "content": "Week 1 content"
            },
            headers=headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["week_number"] == 1
        assert data["topic"] == "Introduction"
        assert data["version"] == 1
        assert data["is_active"] is True
    
    def test_create_syllabus_as_student_forbidden(self, client: TestClient, db: Session):
        """Test student cannot create syllabus"""
        lecturer = create_test_user(db, "lecturer2@test.com", "pass123", UserRole.LECTURER, "Lecturer 2")
        student = create_test_user(db, "student1@test.com", "pass123", UserRole.STUDENT, "Student 1")
        course = create_test_course(db, lecturer.id, "SYL102", "Syllabus Course")
        token = get_auth_token(client, "student1@test.com", "pass123")
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.post(
            f"{settings.API_V1_STR}/syllabus/",
            json={
                "course_id": course.id,
                "week_number": 1,
                "topic": "Introduction"
            },
            headers=headers
        )
        
        assert response.status_code == 403
    
    def test_list_syllabus_student_sees_only_active(self, client: TestClient, db: Session):
        """Test students only see active syllabus entries"""
        lecturer = create_test_user(db, "lecturer3@test.com", "pass123", UserRole.LECTURER, "Lecturer 3")
        student = create_test_user(db, "student2@test.com", "pass123", UserRole.STUDENT, "Student 2")
        course = create_test_course(db, lecturer.id, "SYL103", "Syllabus Course")
        
        # Create active syllabus
        syllabus_active = Syllabus(
            course_id=course.id,
            week_number=1,
            topic="Active Topic",
            is_active=True,
            created_by=lecturer.id
        )
        db.add(syllabus_active)
        
        # Create inactive syllabus
        syllabus_inactive = Syllabus(
            course_id=course.id,
            week_number=2,
            topic="Inactive Topic",
            is_active=False,
            created_by=lecturer.id
        )
        db.add(syllabus_inactive)
        db.commit()
        
        token = get_auth_token(client, "student2@test.com", "pass123")
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get(
            f"{settings.API_V1_STR}/syllabus/?course_id={course.id}",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["week_number"] == 1
        assert data[0]["is_active"] is True
    
    def test_list_syllabus_lecturer_sees_all(self, client: TestClient, db: Session):
        """Test lecturers can see all syllabus entries including inactive"""
        lecturer = create_test_user(db, "lecturer4@test.com", "pass123", UserRole.LECTURER, "Lecturer 4")
        course = create_test_course(db, lecturer.id, "SYL104", "Syllabus Course")
        
        # Create active and inactive syllabus
        syllabus_active = Syllabus(
            course_id=course.id,
            week_number=1,
            topic="Active",
            is_active=True,
            created_by=lecturer.id
        )
        db.add(syllabus_active)
        
        syllabus_inactive = Syllabus(
            course_id=course.id,
            week_number=2,
            topic="Inactive",
            is_active=False,
            created_by=lecturer.id
        )
        db.add(syllabus_inactive)
        db.commit()
        
        token = get_auth_token(client, "lecturer4@test.com", "pass123")
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get(
            f"{settings.API_V1_STR}/syllabus/?course_id={course.id}&include_inactive=true",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
    
    def test_duplicate_active_syllabus_forbidden(self, client: TestClient, db: Session):
        """Test cannot create duplicate active syllabus for same week"""
        lecturer = create_test_user(db, "lecturer5@test.com", "pass123", UserRole.LECTURER, "Lecturer 5")
        course = create_test_course(db, lecturer.id, "SYL105", "Syllabus Course")
        token = get_auth_token(client, "lecturer5@test.com", "pass123")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create first syllabus
        client.post(
            f"{settings.API_V1_STR}/syllabus/",
            json={
                "course_id": course.id,
                "week_number": 1,
                "topic": "Week 1"
            },
            headers=headers
        )
        
        # Try to create duplicate
        response = client.post(
            f"{settings.API_V1_STR}/syllabus/",
            json={
                "course_id": course.id,
                "week_number": 1,
                "topic": "Week 1 Updated"
            },
            headers=headers
        )
        
        assert response.status_code == 409
    
    def test_update_syllabus_creates_new_version(self, client: TestClient, db: Session):
        """Test updating syllabus creates a new version"""
        lecturer = create_test_user(db, "lecturer6@test.com", "pass123", UserRole.LECTURER, "Lecturer 6")
        course = create_test_course(db, lecturer.id, "SYL106", "Syllabus Course")
        token = get_auth_token(client, "lecturer6@test.com", "pass123")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create syllabus
        create_response = client.post(
            f"{settings.API_V1_STR}/syllabus/",
            json={
                "course_id": course.id,
                "week_number": 1,
                "topic": "Week 1 v1"
            },
            headers=headers
        )
        syllabus_id = create_response.json()["id"]
        assert create_response.json()["version"] == 1
        
        # Update syllabus
        update_response = client.put(
            f"{settings.API_V1_STR}/syllabus/{syllabus_id}",
            json={"topic": "Week 1 v2"},
            headers=headers
        )
        
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["version"] == 2
        assert data["topic"] == "Week 1 v2"
        assert data["is_active"] is True
        
        # Check old version is inactive
        versions_response = client.get(
            f"{settings.API_V1_STR}/syllabus/{syllabus_id}/versions",
            headers=headers
        )
        versions = versions_response.json()
        assert len(versions) >= 2
        # Find version 1
        v1 = next((v for v in versions if v["version"] == 1), None)
        assert v1 is not None
        assert v1["is_active"] is False
    
    def test_get_syllabus_version_history(self, client: TestClient, db: Session):
        """Test getting version history for syllabus"""
        lecturer = create_test_user(db, "lecturer7@test.com", "pass123", UserRole.LECTURER, "Lecturer 7")
        course = create_test_course(db, lecturer.id, "SYL107", "Syllabus Course")
        token = get_auth_token(client, "lecturer7@test.com", "pass123")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create and update syllabus multiple times
        create_response = client.post(
            f"{settings.API_V1_STR}/syllabus/",
            json={
                "course_id": course.id,
                "week_number": 1,
                "topic": "v1"
            },
            headers=headers
        )
        syllabus_id = create_response.json()["id"]
        
        # Update to v2
        client.put(
            f"{settings.API_V1_STR}/syllabus/{syllabus_id}",
            json={"topic": "v2"},
            headers=headers
        )
        
        # Get version history
        response = client.get(
            f"{settings.API_V1_STR}/syllabus/{syllabus_id}/versions",
            headers=headers
        )
        
        assert response.status_code == 200
        versions = response.json()
        assert len(versions) >= 2
        # Versions should be ordered by version desc
        assert versions[0]["version"] >= versions[1]["version"]
    
    def test_bulk_create_syllabus(self, client: TestClient, db: Session):
        """Test bulk creating 14 weeks of syllabus"""
        lecturer = create_test_user(db, "lecturer8@test.com", "pass123", UserRole.LECTURER, "Lecturer 8")
        course = create_test_course(db, lecturer.id, "SYL108", "Syllabus Course")
        token = get_auth_token(client, "lecturer8@test.com", "pass123")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create 14 weeks
        weeks = [
            {"week_number": i, "topic": f"Week {i} Topic", "content": f"Week {i} content"}
            for i in range(1, 15)
        ]
        
        response = client.post(
            f"{settings.API_V1_STR}/syllabus/bulk",
            json={
                "course_id": course.id,
                "weeks": weeks,
                "change_reason": "Bulk creation"
            },
            headers=headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert len(data) == 14
        assert all(entry["version"] == 1 for entry in data)
        assert all(entry["is_active"] is True for entry in data)
    
    def test_bulk_create_duplicate_weeks_forbidden(self, client: TestClient, db: Session):
        """Test bulk create fails with duplicate week numbers"""
        lecturer = create_test_user(db, "lecturer9@test.com", "pass123", UserRole.LECTURER, "Lecturer 9")
        course = create_test_course(db, lecturer.id, "SYL109", "Syllabus Course")
        token = get_auth_token(client, "lecturer9@test.com", "pass123")
        headers = {"Authorization": f"Bearer {token}"}
        
        weeks = [
            {"week_number": 1, "topic": "Week 1"},
            {"week_number": 1, "topic": "Week 1 Duplicate"}  # Duplicate!
        ]
        
        response = client.post(
            f"{settings.API_V1_STR}/syllabus/bulk",
            json={
                "course_id": course.id,
                "weeks": weeks
            },
            headers=headers
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_lecturer_cannot_update_other_lecturer_syllabus(self, client: TestClient, db: Session):
        """Test lecturer cannot update another lecturer's syllabus"""
        lecturer1 = create_test_user(db, "lecturer10@test.com", "pass123", UserRole.LECTURER, "Lecturer 10")
        lecturer2 = create_test_user(db, "lecturer11@test.com", "pass123", UserRole.LECTURER, "Lecturer 11")
        course = create_test_course(db, lecturer1.id, "SYL110", "Syllabus Course")
        
        token1 = get_auth_token(client, "lecturer10@test.com", "pass123")
        token2 = get_auth_token(client, "lecturer11@test.com", "pass123")
        headers1 = {"Authorization": f"Bearer {token1}"}
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        # Lecturer1 creates syllabus
        create_response = client.post(
            f"{settings.API_V1_STR}/syllabus/",
            json={
                "course_id": course.id,
                "week_number": 1,
                "topic": "Week 1"
            },
            headers=headers1
        )
        syllabus_id = create_response.json()["id"]
        
        # Lecturer2 tries to update
        response = client.put(
            f"{settings.API_V1_STR}/syllabus/{syllabus_id}",
            json={"topic": "Hacked"},
            headers=headers2
        )
        assert response.status_code == 403
    
    def test_soft_delete_syllabus(self, client: TestClient, db: Session):
        """Test soft delete (deactivate) syllabus"""
        lecturer = create_test_user(db, "lecturer12@test.com", "pass123", UserRole.LECTURER, "Lecturer 12")
        course = create_test_course(db, lecturer.id, "SYL111", "Syllabus Course")
        token = get_auth_token(client, "lecturer12@test.com", "pass123")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create syllabus
        create_response = client.post(
            f"{settings.API_V1_STR}/syllabus/",
            json={
                "course_id": course.id,
                "week_number": 1,
                "topic": "Week 1"
            },
            headers=headers
        )
        syllabus_id = create_response.json()["id"]
        
        # Delete (soft delete)
        delete_response = client.delete(
            f"{settings.API_V1_STR}/syllabus/{syllabus_id}",
            headers=headers
        )
        assert delete_response.status_code == 204
        
        # Verify it's deactivated (students can't see it)
        student = create_test_user(db, "student3@test.com", "pass123", UserRole.STUDENT, "Student 3")
        student_token = get_auth_token(client, "student3@test.com", "pass123")
        student_headers = {"Authorization": f"Bearer {student_token}"}
        
        list_response = client.get(
            f"{settings.API_V1_STR}/syllabus/?course_id={course.id}",
            headers=student_headers
        )
        data = list_response.json()
        assert len(data) == 0  # Student can't see deactivated syllabus
    
    def test_week_number_validation(self, client: TestClient, db: Session):
        """Test week number must be between 1 and 14"""
        lecturer = create_test_user(db, "lecturer13@test.com", "pass123", UserRole.LECTURER, "Lecturer 13")
        course = create_test_course(db, lecturer.id, "SYL112", "Syllabus Course")
        token = get_auth_token(client, "lecturer13@test.com", "pass123")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Week 0 should fail
        response = client.post(
            f"{settings.API_V1_STR}/syllabus/",
            json={
                "course_id": course.id,
                "week_number": 0,
                "topic": "Invalid"
            },
            headers=headers
        )
        assert response.status_code == 422
        
        # Week 15 should fail
        response = client.post(
            f"{settings.API_V1_STR}/syllabus/",
            json={
                "course_id": course.id,
                "week_number": 15,
                "topic": "Invalid"
            },
            headers=headers
        )
        assert response.status_code == 422

