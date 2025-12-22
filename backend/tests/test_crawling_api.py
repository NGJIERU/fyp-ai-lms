"""
API integration tests for material crawling trigger endpoint
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import User
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


class TestCrawlingAPI:
    """API integration tests for /materials/crawl endpoint"""

    def test_trigger_crawl_as_lecturer(self, client: TestClient, db: Session):
        """Lecturer should be able to trigger a crawl for a specific crawler_type"""
        lecturer = create_test_user(db, "lect_crawl@test.com", "pass123", UserRole.LECTURER, "Lecturer")
        token = get_auth_token(client, "lect_crawl@test.com", "pass123")
        headers = {"Authorization": f"Bearer {token}"}

        payload = {"crawler_type": "youtube", "max_items": 50}
        response = client.post(
            f"{settings.API_V1_STR}/materials/crawl",
            json=payload,
            headers=headers,
        )

        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "accepted"
        assert data["crawler_type"] == "youtube"
        assert data["items_fetched"] == 0
        assert "Started crawl for youtube" in data["message"]

    def test_trigger_crawl_as_super_admin(self, client: TestClient, db: Session):
        """Super admin should also be able to trigger a crawl"""
        admin = create_test_user(db, "admin_crawl@test.com", "pass123", UserRole.SUPER_ADMIN, "Admin")
        token = get_auth_token(client, "admin_crawl@test.com", "pass123")
        headers = {"Authorization": f"Bearer {token}"}

        payload = {"crawler_type": None, "max_items": 20}
        response = client.post(
            f"{settings.API_V1_STR}/materials/crawl",
            json=payload,
            headers=headers,
        )

        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "accepted"
        assert data["crawler_type"] == "all"
        assert "Started crawl for" in data["message"]

    def test_student_cannot_trigger_crawl(self, client: TestClient, db: Session):
        """Student should be forbidden from triggering crawling"""
        student = create_test_user(db, "stud_crawl@test.com", "pass123", UserRole.STUDENT, "Student")
        token = get_auth_token(client, "stud_crawl@test.com", "pass123")
        headers = {"Authorization": f"Bearer {token}"}

        payload = {"crawler_type": "youtube", "max_items": 10}
        response = client.post(
            f"{settings.API_V1_STR}/materials/crawl",
            json=payload,
            headers=headers,
        )

        assert response.status_code == 403

    def test_trigger_crawl_requires_auth(self, client: TestClient, db: Session):
        """Unauthenticated users cannot trigger crawling"""
        payload = {"crawler_type": "youtube", "max_items": 10}
        response = client.post(
            f"{settings.API_V1_STR}/materials/crawl",
            json=payload,
        )

        # get_current_active_user should enforce auth
        assert response.status_code in (401, 403)

    def test_trigger_crawl_validation_max_items(self, client: TestClient, db: Session):
        """Test that max_items must respect Pydantic validation (>=1, <=1000)"""
        lecturer = create_test_user(db, "lect_crawl_val@test.com", "pass123", UserRole.LECTURER, "Lecturer")
        token = get_auth_token(client, "lect_crawl_val@test.com", "pass123")
        headers = {"Authorization": f"Bearer {token}"}

        # Invalid: max_items < 1
        payload = {"crawler_type": "youtube", "max_items": 0}
        response = client.post(
            f"{settings.API_V1_STR}/materials/crawl",
            json=payload,
            headers=headers,
        )
        assert response.status_code == 422

        # Invalid: max_items > 1000
        payload = {"crawler_type": "youtube", "max_items": 2000}
        response = client.post(
            f"{settings.API_V1_STR}/materials/crawl",
            json=payload,
            headers=headers,
        )
        assert response.status_code == 422
