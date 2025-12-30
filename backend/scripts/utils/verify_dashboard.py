
import urllib.request
import urllib.parse
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"

def login():
    url = f"{BASE_URL}/auth/login"
    # OAuth2 expects form data username/password
    data = urllib.parse.urlencode({
        "username": "student@example.com",
        "password": "password123"
    }).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, method="POST")
    # Content-Type is implicitly application/x-www-form-urlencoded when data is passed, 
    # but explicit header doesn't hurt.
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    
    try:
        with urllib.request.urlopen(req) as response:
            if response.status != 200:
                print(f"Login failed: {response.status}")
                return None
            return json.loads(response.read().decode())["access_token"]
    except urllib.error.HTTPError as e:
        print(f"Login connection failed: {e.code} {e.read().decode()}")
        return None
    except Exception as e:
        print(f"Login error: {e}")
        return None

def verify_dashboard():
    token = login()
    if not token:
        print("Skipping verification: Could not login")
        return

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    course_id = 1
    
    # 1. Verify Weak Topics
    print(f"\n--- Checking Weak Topics (Course {course_id}) ---")
    url = f"{BASE_URL}/tutor/weak-topics?course_id={course_id}"
    req = urllib.request.Request(url, headers=headers, method="GET")
    
    try:
        with urllib.request.urlopen(req) as response:
            print(f"✅ Weak Topics Status: {response.status}")
            data = json.loads(response.read().decode())
            print(f"Response keys: {list(data.keys())}")
    except urllib.error.HTTPError as e:
        print(f"❌ Weak Topics failed: {e.code} {e.read().decode()}")
    except Exception as e:
        print(f"❌ Weak Topics error: {e}")

    # 2. Verify Practice History
    print(f"\n--- Checking Practice History (Course {course_id}) ---")
    url = f"{BASE_URL}/tutor/practice/history?course_id={course_id}"
    req = urllib.request.Request(url, headers=headers, method="GET")
    
    try:
        with urllib.request.urlopen(req) as response:
            print(f"✅ History Status: {response.status}")
            data = json.loads(response.read().decode())
            print(f"Items count: {len(data)}")
    except urllib.error.HTTPError as e:
        print(f"❌ History failed: {e.code} {e.read().decode()}")
    except Exception as e:
         print(f"❌ History error: {e}")

if __name__ == "__main__":
    verify_dashboard()
