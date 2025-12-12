"""
API integration tests for Materials endpoints
"""
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import User, Course, Material, MaterialTopic
from app.models.user import UserRole
from app.core import security
from app.core.config import settings


def get_auth_token(client: TestClient, email: str, password: str) -> str:
    """Helper to get auth token"""
    response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": email, "password": password},
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
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_test_course(db: Session, lecturer_id: int, code: str = "MAT101", name: str = "Materials Course") -> Course:
    """Helper to create test course"""
    course = Course(code=code, name=name, lecturer_id=lecturer_id)
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


class TestMaterialsAPI:
    """API integration tests for materials repository endpoints"""

    def test_list_materials_basic(self, client: TestClient, db: Session):
        """Test listing materials with default pagination"""
        user = create_test_user(db, "user_materials@test.com", "pass123", UserRole.STUDENT, "Student")
        token = get_auth_token(client, "user_materials@test.com", "pass123")
        headers = {"Authorization": f"Bearer {token}"}

        # Seed some materials
        m1 = Material(title="Video 1", url="https://example.com/v1", source="YouTube", type="video", quality_score=0.9, content_hash="hash_v1")
        m2 = Material(title="Article 1", url="https://example.com/a1", source="Blog", type="article", quality_score=0.7, content_hash="hash_a1")
        db.add_all([m1, m2])
        db.commit()

        response = client.get(f"{settings.API_V1_STR}/materials/", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2

    def test_list_materials_filters(self, client: TestClient, db: Session):
        """Test filtering materials by type, source, and min_quality"""
        user = create_test_user(db, "user_materials_filter@test.com", "pass123", UserRole.STUDENT, "Student")
        token = get_auth_token(client, "user_materials_filter@test.com", "pass123")
        headers = {"Authorization": f"Bearer {token}"}

        # Seed materials
        m1 = Material(title="High Quality Video", url="https://example.com/v2", source="YouTube", type="video", quality_score=0.9, content_hash="hash_v2")
        m2 = Material(title="Low Quality Video", url="https://example.com/v3", source="YouTube", type="video", quality_score=0.2, content_hash="hash_v3")
        m3 = Material(title="Blog Post", url="https://example.com/b1", source="Blog", type="article", quality_score=0.8, content_hash="hash_b1")
        db.add_all([m1, m2, m3])
        db.commit()

        # Filter by type and source
        response = client.get(
            f"{settings.API_V1_STR}/materials/?type=video&source=YouTube",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(item["type"] == "video" for item in data)
        assert all(item["source"] == "YouTube" for item in data)

        # Filter by min_quality
        response = client.get(
            f"{settings.API_V1_STR}/materials/?min_quality=0.8",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert all(item["quality_score"] >= 0.8 for item in data)

    def test_search_materials(self, client: TestClient, db: Session):
        """Test simple text search for materials"""
        user = create_test_user(db, "user_search@test.com", "pass123", UserRole.STUDENT, "Student")
        token = get_auth_token(client, "user_search@test.com", "pass123")
        headers = {"Authorization": f"Bearer {token}"}

        # Seed materials
        m1 = Material(title="Deep Learning Tutorial", url="https://example.com/dl", source="Blog", type="article", description="Deep learning basics", content_hash="hash_dl")
        m2 = Material(title="Intro to Databases", url="https://example.com/db", source="OER", type="pdf", description="Relational databases", content_hash="hash_db")
        db.add_all([m1, m2])
        db.commit()

        response = client.get(
            f"{settings.API_V1_STR}/materials/search?query=deep",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        # Each result is a MaterialSearchResult
        assert "material" in data[0]
        assert "similarity_score" in data[0]

    def test_get_course_week_materials(self, client: TestClient, db: Session):
        """Test retrieving materials mapped to a specific course week"""
        lecturer = create_test_user(db, "lect_mat_week@test.com", "pass123", UserRole.LECTURER, "Lecturer")
        student = create_test_user(db, "stud_mat_week@test.com", "pass123", UserRole.STUDENT, "Student")
        course = create_test_course(db, lecturer.id, code="MAT201", name="Materials Mapping")

        # Create material and mapping
        material = Material(
            title="Week 1 Resource",
            url="https://example.com/w1",
            source="YouTube",
            type="video",
            content_hash="hash_w1"
        )
        db.add(material)
        db.commit()
        db.refresh(material)

        topic = MaterialTopic(
            material_id=material.id,
            course_id=course.id,
            week_number=1,
            relevance_score=0.9,
            approved_by_lecturer=True,
            approved_by=lecturer.id,
        )
        db.add(topic)
        db.commit()

        token = get_auth_token(client, "stud_mat_week@test.com", "pass123")
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get(
            f"{settings.API_V1_STR}/materials/course/{course.id}/week/1",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        entry = data[0]
        assert entry["course_id"] == course.id
        assert entry["week_number"] == 1
        assert entry["material"]["id"] == material.id
        assert entry["course_name"] == course.name

    def test_approve_material_as_lecturer(self, client: TestClient, db: Session):
        """Test lecturer can approve/map material to course week"""
        lecturer = create_test_user(db, "lect_approve@test.com", "pass123", UserRole.LECTURER, "Lecturer")
        course = create_test_course(db, lecturer.id, code="MAT301", name="Approval Course")

        # Create material
        material = Material(
            title="Approval Resource",
            url="https://example.com/app",
            source="OER",
            type="article",
            content_hash="hash_app"
        )
        db.add(material)
        db.commit()
        db.refresh(material)

        token = get_auth_token(client, "lect_approve@test.com", "pass123")
        headers = {"Authorization": f"Bearer {token}"}

        payload = {
            "material_id": material.id,
            "course_id": course.id,
            "week_number": 2,
            "relevance_score": 0.95,
        }
        response = client.post(
            f"{settings.API_V1_STR}/materials/{material.id}/approve",
            json=payload,
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["course_id"] == course.id
        assert data["week_number"] == 2
        assert data["approved_by_lecturer"] is True
        assert data["material"]["id"] == material.id

    def test_approve_material_duplicate_updates_existing(self, client: TestClient, db: Session):
        """Test approving same material-week-course updates existing mapping instead of creating duplicate"""
        lecturer = create_test_user(db, "lect_approve_dup@test.com", "pass123", UserRole.LECTURER, "Lecturer")
        course = create_test_course(db, lecturer.id, code="MAT302", name="Approval Course Dup")

        material = Material(
            title="Duplicate Map Resource",
            url="https://example.com/dup",
            source="Blog",
            type="article",
            content_hash="hash_dup"
        )
        db.add(material)
        db.commit()
        db.refresh(material)

        # Existing mapping
        topic = MaterialTopic(
            material_id=material.id,
            course_id=course.id,
            week_number=3,
            relevance_score=0.5,
            approved_by_lecturer=True,
            approved_by=lecturer.id,
        )
        db.add(topic)
        db.commit()
        db.refresh(topic)

        token = get_auth_token(client, "lect_approve_dup@test.com", "pass123")
        headers = {"Authorization": f"Bearer {token}"}

        payload = {
            "material_id": material.id,
            "course_id": course.id,
            "week_number": 3,
            "relevance_score": 0.9,
        }
        response = client.post(
            f"{settings.API_V1_STR}/materials/{material.id}/approve",
            json=payload,
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["relevance_score"] == 0.9
        assert data["id"] == topic.id

    def test_approve_material_not_found(self, client: TestClient, db: Session):
        """Test approving non-existent material returns 404"""
        lecturer = create_test_user(db, "lect_approve_nf@test.com", "pass123", UserRole.LECTURER, "Lecturer")
        course = create_test_course(db, lecturer.id, code="MAT303", name="Approval Course NF")

        token = get_auth_token(client, "lect_approve_nf@test.com", "pass123")
        headers = {"Authorization": f"Bearer {token}"}

        payload = {
            "material_id": 9999,
            "course_id": course.id,
            "week_number": 1,
            "relevance_score": 0.8,
        }
        response = client.post(
            f"{settings.API_V1_STR}/materials/9999/approve",
            json=payload,
            headers=headers,
        )
        assert response.status_code == 404

    def test_student_cannot_approve_material(self, client: TestClient, db: Session):
        """Test students are forbidden from approving materials"""
        lecturer = create_test_user(db, "lect_approve_forbid@test.com", "pass123", UserRole.LECTURER, "Lecturer")
        student = create_test_user(db, "stud_approve_forbid@test.com", "pass123", UserRole.STUDENT, "Student")
        course = create_test_course(db, lecturer.id, code="MAT304", name="Approval Course Forbid")

        material = Material(
            title="Forbidden Resource",
            url="https://example.com/forbid",
            source="OER",
            type="pdf",
            content_hash="hash_forbid"
        )
        db.add(material)
        db.commit()
        db.refresh(material)

        token = get_auth_token(client, "stud_approve_forbid@test.com", "pass123")
        headers = {"Authorization": f"Bearer {token}"}

        payload = {
            "material_id": material.id,
            "course_id": course.id,
            "week_number": 1,
            "relevance_score": 0.7,
        }
        response = client.post(
            f"{settings.API_V1_STR}/materials/{material.id}/approve",
            json=payload,
            headers=headers,
        )
        # get_current_lecturer dependency should block
        assert response.status_code in (401, 403)

    def test_student_can_rate_material(self, client: TestClient, db: Session):
        """Test student can rate and update rating for a material."""
        student = create_test_user(db, "stud_rate@test.com", "pass123", UserRole.STUDENT, "Student")
        token = get_auth_token(client, "stud_rate@test.com", "pass123")
        headers = {"Authorization": f"Bearer {token}"}

        material = Material(
            title="Rateable Resource",
            url="https://example.com/rate",
            source="OER",
            type="pdf",
            content_hash="hash_rate"
        )
        db.add(material)
        db.commit()
        db.refresh(material)

        payload = {"rating": 1, "note": "Great resource"}
        response = client.post(
            f"{settings.API_V1_STR}/materials/{material.id}/rate",
            json=payload,
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["rating"] == 1
        assert data["note"] == "Great resource"

        payload_update = {"rating": -1, "note": "Actually not helpful"}
        response = client.post(
            f"{settings.API_V1_STR}/materials/{material.id}/rate",
            json=payload_update,
            headers=headers,
        )
        assert response.status_code == 200
        updated = response.json()
        assert updated["rating"] == -1
        assert updated["note"] == "Actually not helpful"
        assert updated["id"] == data["id"]

    def test_lecturer_cannot_rate_material(self, client: TestClient, db: Session):
        """Ensure lecturers cannot rate materials."""
        lecturer = create_test_user(db, "lect_rate_forbid@test.com", "pass123", UserRole.LECTURER, "Lecturer")
        token = get_auth_token(client, "lect_rate_forbid@test.com", "pass123")
        headers = {"Authorization": f"Bearer {token}"}

        material = Material(
            title="Lecturer Resource",
            url="https://example.com/lect_rate",
            source="Blog",
            type="article",
            content_hash="hash_lect_rate"
        )
        db.add(material)
        db.commit()
        db.refresh(material)

        payload = {"rating": 1, "note": "Nice"}
        response = client.post(
            f"{settings.API_V1_STR}/materials/{material.id}/rate",
            json=payload,
            headers=headers,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_material_rating_summary(self, client: TestClient, db: Session):
        """Test rating summary aggregates upvotes/downvotes."""
        student1 = create_test_user(db, "stud_summary1@test.com", "pass123", UserRole.STUDENT, "Student One")
        student2 = create_test_user(db, "stud_summary2@test.com", "pass123", UserRole.STUDENT, "Student Two")
        token1 = get_auth_token(client, "stud_summary1@test.com", "pass123")
        token2 = get_auth_token(client, "stud_summary2@test.com", "pass123")
        headers1 = {"Authorization": f"Bearer {token1}"}
        headers2 = {"Authorization": f"Bearer {token2}"}

        material = Material(
            title="Summary Resource",
            url="https://example.com/summary",
            source="YouTube",
            type="video",
            content_hash="hash_summary"
        )
        db.add(material)
        db.commit()
        db.refresh(material)

        client.post(
            f"{settings.API_V1_STR}/materials/{material.id}/rate",
            json={"rating": 1, "note": "Helpful"},
            headers=headers1,
        )
        client.post(
            f"{settings.API_V1_STR}/materials/{material.id}/rate",
            json={"rating": -1, "note": "Not helpful"},
            headers=headers2,
        )

        summary_response = client.get(
            f"{settings.API_V1_STR}/materials/{material.id}/ratings/summary",
            headers=headers1,
        )
        assert summary_response.status_code == 200
        summary = summary_response.json()
        assert summary["material_id"] == material.id
        assert summary["total_ratings"] == 2
        assert summary["upvotes"] == 1
        assert summary["downvotes"] == 1
        assert summary["average_rating"] == pytest.approx(0.0)
