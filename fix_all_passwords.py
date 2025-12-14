"""Fix passwords for all demo users"""
from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models import User

db = SessionLocal()

# Fix passwords
password_map = {
    "admin@lms.edu": "admin123",
    "dr.smith@lms.edu": "lecturer123",
    "dr.chen@lms.edu": "lecturer123",
    "alice@student.lms.edu": "student123",
    "bob@student.lms.edu": "student123",
    "charlie@student.lms.edu": "student123"
}

for email, password in password_map.items():
    user = db.query(User).filter(User.email == email).first()
    if user:
        user.hashed_password = get_password_hash(password)
        print(f"Updated password for {email}")

db.commit()
print("\nAll passwords updated!")
db.close()
