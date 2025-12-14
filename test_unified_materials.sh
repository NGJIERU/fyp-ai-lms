#!/bin/bash
# Quick test of unified material upload

# Login
echo "Testing unified material upload..."
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -d "username=dr.smith@lms.edu&password=lecturer123" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))")

if [ -z "$TOKEN" ]; then
  echo "❌ Login failed"
  exit 1
fi

echo "✅ Logged in successfully"

# Upload test
echo "Testing upload with unified Material table..."
RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/courses/1/materials/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "title=Test Unified Material" \
  -F "description=Testing the refactored material system" \
  -F "file=@/tmp/test_course_material.pdf")

echo "$RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'id' in data:
        print(f'✅ Upload successful!')
        print(f'   Material ID: {data[\"id\"]}')
        print(f'   Title: {data[\"title\"]}')
        print(f'   Type: {data.get(\"type\", \"N/A\")}')
        print(f'   Source: {data.get(\"source\", \"N/A\")}')
        print(f'   Material Type: {data.get(\"material_type\", \"N/A\")}')
    else:
        print('❌ Upload failed:', data)
except Exception as e:
    print('❌ Error:', str(e))
    print('Response:', sys.stdin.read())
"

# List materials
echo ""
echo "Testing list endpoint..."
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/courses/1/materials" | \
  python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'✅ Found {len(data)} total material(s) for course')
for m in data[:5]:  # Show first 5
    mtype = m.get('material_type', m.get('source', 'unknown'))
    print(f'  - {m[\"title\"][:50]} (type: {mtype})')
"

echo ""
echo "✅ Refactored system test complete!"
