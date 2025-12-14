#!/bin/bash
# Complete test of the unified material system

echo "🧪 Testing Unified Material System with TailwindUI Components"
echo "=============================================================="
echo ""

# Login as lecturer
echo "1. Logging in as lecturer..."
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -d "username=dr.smith@lms.edu&password=lecturer123" | jq -r '.access_token')

if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
  echo "❌ Login failed"
  exit 1
fi

echo "✅ Login successful"
echo ""

# Upload a test file
echo "2. Uploading test material..."
UPLOAD_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/courses/1/materials/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "title=TailwindUI Test Material" \
  -F "description=Testing the refactored system with TailwindUI components" \
  -F "file=@/tmp/test_course_material.pdf")

echo "$UPLOAD_RESPONSE" | jq '.' 2>/dev/null || echo "$UPLOAD_RESPONSE"
echo ""

# List all materials (should show both uploaded and AI materials)
echo "3. Listing all materials for course 1..."
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/courses/1/materials" | jq -c '.[] | {id, title, material_type: .material_type, source: .source}' | head -10

echo ""
echo "✅ Backend tests complete!"
echo ""
echo "📱 To test the frontend:"
echo "  1. cd frontend"
echo "  2. npm run dev"
echo "  3. Open: http://localhost:3000/courses/1/materials"
