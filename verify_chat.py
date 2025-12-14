
import requests
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"

# Login as student to get token
def login():
    try:
        resp = requests.post(f"http://localhost:8000/api/v1/auth/login", data={
            "username": "student@example.com", 
            "password": "password123"
        })
        if resp.status_code != 200:
            print("Login failed")
            # Try creating a test student if login fails
            return None
        return resp.json()["access_token"]
    except Exception as e:
        print(f"Connection failed: {e}")
        return None

def verify_chat():
    token = login()
    if not token:
        print("Skipping verification: Could not login (server might be down or no user)")
        return

    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Get a course ID (assuming course 1 exists)
    course_id = 1
    
    # 2. Send first message
    print("\n--- Sending Message 1 ---")
    payload1 = {
        "message": "What is this course about?",
        "week_number": 1
    }
    resp1 = requests.post(
        f"{BASE_URL}/tutor/chat?course_id={course_id}", 
        json=payload1, 
        headers=headers
    )
    
    if resp1.status_code == 200:
        data = resp1.json()
        print("Response 1:", data["response"][:100] + "...")
        
        # 3. Send follow-up with history
        print("\n--- Sending Message 2 (with history) ---")
        payload2 = {
            "message": "Tell me more.",
            "week_number": 1,
            "conversation_history": [
                {"role": "user", "content": "What is this course about?"},
                {"role": "assistant", "content": data["response"]}
            ]
        }
        resp2 = requests.post(
            f"{BASE_URL}/tutor/chat?course_id={course_id}", 
            json=payload2, 
            headers=headers
        )
        if resp2.status_code == 200:
            print("Response 2:", resp2.json()["response"][:100] + "...")
            print("\n✅ Chat verification successful!")
        else:
            print(f"❌ Message 2 failed: {resp2.status_code} {resp2.text}")
            
    else:
        print(f"❌ Message 1 failed: {resp1.status_code} {resp1.text}")

if __name__ == "__main__":
    verify_chat()
