import requests
import sys

# Using port 8001 to avoid conflict with Docker on port 8000
BASE = "http://127.0.0.1:8001/api/v1"

def run_test():
    print(f"Testing against {BASE}...")
    
    # 1. Register super admin
    print("\n1. Registering Super Admin...")
    try:
        r = requests.post(f"{BASE}/auth/register", json={
            "email": "admin@uni.edu",
            "password": "admin123",
            "full_name": "Super Admin",
            "role": "super_admin"
        })
        if r.status_code == 200:
            print("✅ Register Success:", r.json()["email"])
        else:
            print(f"❌ Register Failed ({r.status_code}):", r.text)
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Is the server running on port 8001?")
        return

    # 2. Login
    print("\n2. Logging in...")
    r = requests.post(f"{BASE}/auth/login", data={
        "username": "admin@uni.edu",
        "password": "admin123"
    })
    
    if r.status_code != 200:
        print(f"❌ Login Failed ({r.status_code}):", r.text)
        return

    token = r.json()["access_token"]
    print("✅ Login Success, token received")

    # 3. Test protected route
    print("\n3. Testing Protected Endpoint (/users/me)...")
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{BASE}/users/me", headers=headers)
    
    if r.status_code == 200:
        print("✅ Me Endpoint Success:", r.json()["email"])
    else:
        print(f"❌ Me Endpoint Failed ({r.status_code}):", r.text)

if __name__ == "__main__":
    run_test()
