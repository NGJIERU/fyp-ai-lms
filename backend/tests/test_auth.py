from fastapi.testclient import TestClient
from app.core.config import settings

def test_create_user(client: TestClient):
    response = client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={
            "email": "test@example.com",
            "password": "password123",
            "full_name": "Test User",
            "role": "student"
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data

def test_login_user(client: TestClient):
    # First create user
    client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={
            "email": "login@example.com",
            "password": "password123",
            "full_name": "Login User",
            "role": "student"
        },
    )
    
    # Then login
    response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={
            "username": "login@example.com",
            "password": "password123"
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
