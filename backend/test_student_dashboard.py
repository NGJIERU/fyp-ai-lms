"""Test student dashboard endpoint directly"""
from app.core.database import SessionLocal
from app.models import User
from app.api.v1.endpoints.dashboard import get_student_course_detail

db = SessionLocal()

# Get student user
student = db.query(User).filter(User.email == 'alice@student.lms.edu').first()
print(f"Student found: {student.email}")
print(f"Student ID: {student.id}")

# Try to call the endpoint logic
try:
    result = get_student_course_detail(
        course_id=1,
        db=db,
        current_user=student
    )
    print("SUCCESS!")
    print(result)
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

db.close()
