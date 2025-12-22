#!/bin/bash
# Simple test to verify material upload works

# Login as lecturer
echo "Logging in as lecturer..."
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=dr.smith@lms.edu&password=lecturer123" | jq -r '.access_token')

if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
  echo "❌ Login failed"
  exit 1
fi

echo "✓ Logged in successfully"
echo ""

# Upload a material
echo "Uploading material..."
curl -v -X POST "http://localhost:8000/api/v1/courses/1/materials/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "title=Python Lecture Notes" \
  -F "description=Introduction to Python programming" \
  -F "file=@/tmp/test_course_material.pdf;type=application/pdf"

echo ""
echo "Done"
