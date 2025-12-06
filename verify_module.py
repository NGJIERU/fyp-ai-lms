import requests
import sys

BASE_URL = "http://127.0.0.1:8001/api/v1"
EMAIL = "script_test@uni.edu"
PASSWORD = "password123"

def test_module():
    # 1. Register
    try:
        requests.post(f"{BASE_URL}/auth/register", json={
            "email": EMAIL, "password": PASSWORD, "full_name": "Script Test", "role": "student"
        })
    except:
        pass # Ignore if already exists

    # 2. Login
    login_res = requests.post(f"{BASE_URL}/auth/login", data={"username": EMAIL, "password": PASSWORD})
    if login_res.status_code != 200:
        print("Login failed")
        sys.exit(1)
    
    token = login_res.json()["access_token"]

    # 3. Verify Me
    me_res = requests.get(f"{BASE_URL}/users/me", headers={"Authorization": f"Bearer {token}"})
    
    if me_res.status_code == 200 and me_res.json()["email"] == EMAIL:
        print("All tests passed")
    else:
        print("Verification failed")

if __name__ == "__main__":
    test_module()