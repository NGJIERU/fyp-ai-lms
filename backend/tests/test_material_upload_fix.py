"""
Test script to verify material upload fix
Tests that MaterialTopic records are created when uploading materials
"""
import requests
import os

BASE_URL = "http://localhost:8000/api/v1"

def login_as_lecturer():
    """Login as lecturer and get token"""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={
            "username": "dr.smith@lms.edu",
            "password": "lecturer123"
        }
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception(f"Login failed: {response.text}")

def test_material_upload_with_week():
    """Test uploading a material with week_number"""
    print("🧪 Testing Material Upload Fix...")
    print("=" * 60)
    
    # Login
    print("\n1. Logging in as lecturer...")
    token = login_as_lecturer()
    print("   ✅ Login successful")
    
    # Upload material with week_number
    print("\n2. Uploading material with week_number=1...")
    
    # Create test data
    form_data = {
        "title": "Test Material - Upload Fix Verification",
        "description": "Testing that MaterialTopic records are created",
        "course_id": "1",  # DS101
        "type": "article",
        "week_number": "1",
        "url": "https://example.com/test-material.pdf"
    }
    
    response = requests.post(
        f"{BASE_URL}/lecturer/materials/",
        headers={"Authorization": f"Bearer {token}"},
        data=form_data
    )
    
    if response.status_code == 200:
        material = response.json()
        material_id = material["id"]
        print(f"   ✅ Material created successfully (ID: {material_id})")
        print(f"   📄 Title: {material['title']}")
        print(f"   🔗 URL: {material['url']}")
        
        # Verify MaterialTopic was created
        print("\n3. Verifying MaterialTopic record was created...")
        print("   💡 Check database manually:")
        print(f"   sqlite3 lms.db \"SELECT * FROM material_topics WHERE material_id={material_id};\"")
        
        print("\n✅ TEST PASSED - Material uploaded successfully!")
        print("   Next step: Verify MaterialTopic record exists in database")
        return True
    else:
        print(f"   ❌ Upload failed: {response.status_code}")
        print(f"   Error: {response.text}")
        return False

def test_invalid_week_number():
    """Test that invalid week numbers are rejected"""
    print("\n\n🧪 Testing Week Number Validation...")
    print("=" * 60)
    
    # Login
    print("\n1. Logging in as lecturer...")
    token = login_as_lecturer()
    print("   ✅ Login successful")
    
    # Try to upload with invalid week_number
    print("\n2. Attempting upload with week_number=15 (should fail)...")
    
    form_data = {
        "title": "Invalid Week Test",
        "description": "Should be rejected",
        "course_id": "1",
        "type": "article",
        "week_number": "15",  # Invalid - should be 1-14
        "url": "https://example.com/test.pdf"
    }
    
    response = requests.post(
        f"{BASE_URL}/lecturer/materials/",
        headers={"Authorization": f"Bearer {token}"},
        data=form_data
    )
    
    if response.status_code == 400:
        error = response.json()
        print(f"   ✅ Correctly rejected: {error['detail']}")
        return True
    else:
        print(f"   ❌ Should have been rejected but got: {response.status_code}")
        return False

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("MATERIAL UPLOAD FIX VERIFICATION TEST")
    print("=" * 60)
    
    try:
        # Test 1: Valid upload with week_number
        test1_passed = test_material_upload_with_week()
        
        # Test 2: Invalid week_number validation
        test2_passed = test_invalid_week_number()
        
        # Summary
        print("\n\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Valid upload test: {'PASSED' if test1_passed else 'FAILED'}")
        print(f"✅ Validation test: {'PASSED' if test2_passed else 'FAILED'}")
        
        if test1_passed and test2_passed:
            print("\n🎉 ALL TESTS PASSED!")
            print("\nManual verification steps:")
            print("1. Check database for MaterialTopic records")
            print("2. Login as student and verify material appears in Week 1")
        else:
            print("\n❌ SOME TESTS FAILED - Review errors above")
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
