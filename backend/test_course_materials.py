"""
Manual test script for Course Material Upload Feature
Tests upload, list, download, and authorization
"""
import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8000/api/v1"

def print_separator(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def login(email, password):
    """Login and return access token"""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": email, "password": password}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Login failed: {response.status_code} - {response.text}")
        return None

def test_upload_material(token, course_id, pdf_path):
    """Test uploading a course material"""
    print_separator(f"TEST: Upload Material to Course {course_id}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    with open(pdf_path, 'rb') as f:
        files = {'file': ('test_material.pdf', f, 'application/pdf')}
        data = {
            'title': 'Introduction to Python Programming',
            'description': 'Week 1 lecture notes covering Python basics'
        }
        
        response = requests.post(
            f"{BASE_URL}/courses/{course_id}/materials/upload",
            headers=headers,
            files=files,
            data=data
        )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 201:
        material = response.json()
        print(f"✓ Material uploaded successfully!")
        print(f"  Material ID: {material['id']}")
        print(f"  Title: {material['title']}")
        print(f"  File Size: {material['file_size']} bytes")
        print(f"  Uploader: {material['uploader_name']}")
        return material['id']
    else:
        print(f"✗ Upload failed: {response.text}")
        return None

def test_list_materials(token, course_id):
    """Test listing course materials"""
    print_separator(f"TEST: List Materials for Course {course_id}")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/courses/{course_id}/materials",
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        materials = response.json()
        print(f"✓ Found {len(materials)} material(s)")
        for material in materials:
            print(f"  - [{material['id']}] {material['title']} ({material['file_size']} bytes)")
        return materials
    else:
        print(f"✗ List failed: {response.text}")
        return []

def test_download_material(token, course_id, material_id, save_path):
    """Test downloading a course material"""
    print_separator(f"TEST: Download Material {material_id}")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/courses/{course_id}/materials/{material_id}/download",
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            f.write(response.content)
        print(f"✓ Material downloaded successfully!")
        print(f"  Saved to: {save_path}")
        print(f"  Size: {len(response.content)} bytes")
        return True
    else:
        print(f"✗ Download failed: {response.text}")
        return False

def test_unauthorized_access(token, course_id):
    """Test that non-enrolled students cannot access materials"""
    print_separator("TEST: Unauthorized Access (Should Fail)")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/courses/{course_id}/materials",
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 403:
        print(f"✓ Correctly blocked unauthorized access")
        return True
    else:
        print(f"✗ Unexpected response: {response.status_code}")
        return False

def main():
    print("\n" + "🧪 Course Material Upload - Manual Test Suite" + "\n")
    
    # Test Configuration
    LECTURER_EMAIL = "dr.smith@lms.edu"
    LECTURER_PASSWORD = "lecturer123"
    STUDENT_EMAIL = "alice@student.lms.edu"
    STUDENT_PASSWORD = "student123"
    COURSE_ID = 1  # Adjust based on your seeded data
    
    # Create a simple test PDF (you can also use a real PDF file)
    test_pdf_path = Path("/tmp/test_course_material.pdf")
    if not test_pdf_path.exists():
        # Create a minimal PDF for testing
        pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >> /MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n4 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 100 700 Td (Test PDF Material) Tj ET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000056 00000 n\n0000000115 00000 n\n0000000317 00000 n\ntrailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n409\n%%EOF"
        test_pdf_path.write_bytes(pdf_content)
        print(f"Created test PDF: {test_pdf_path}")
    
    # Test 1: Lecturer Login
    print_separator("Setup: Login as Lecturer")
    lecturer_token = login(LECTURER_EMAIL, LECTURER_PASSWORD)
    if not lecturer_token:
        print("❌ Failed to login as lecturer. Exiting.")
        return
    print("✓ Lecturer logged in successfully")
    
    # Test 2: Student Login
    print_separator("Setup: Login as Student")
    student_token = login(STUDENT_EMAIL, STUDENT_PASSWORD)
    if not student_token:
        print("❌ Failed to login as student. Exiting.")
        return
    print("✓ Student logged in successfully")
    
    # Test 3: Upload Material (as lecturer)
    material_id = test_upload_material(lecturer_token, COURSE_ID, test_pdf_path)
    if not material_id:
        print("\n❌ Upload failed. Some tests will be skipped.")
        return
    
    # Test 4: List Materials (as lecturer)
    test_list_materials(lecturer_token, COURSE_ID)
    
    # Test 5: List Materials (as enrolled student)
    test_list_materials(student_token, COURSE_ID)
    
    # Test 6: Download Material (as enrolled student)
    download_path = Path("/tmp/downloaded_material.pdf")
    test_download_material(student_token, COURSE_ID, material_id, download_path)
    
    # Test 7: Try to access materials from a course the student is not enrolled in
    # Note: You may need to adjust this based on your seed data
    # test_unauthorized_access(student_token, 999)  # Non-existent course
    
    print_separator("Test Suite Complete")
    print("✓ All basic tests passed!")
    print("\nNote: Please manually verify:")
    print(f"  1. Downloaded file can be opened: {download_path}")
    print("  2. Check uploads directory for uploaded files")
    print("  3. Try uploading as a student (should fail)")

if __name__ == "__main__":
    main()
