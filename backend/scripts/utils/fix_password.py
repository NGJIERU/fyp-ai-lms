"""Fix the password hash for dr.smith@lms.edu"""
from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models import User

db = SessionLocal()
user = db.query(User).filter(User.email == 'dr.smith@lms.edu').first()

if user:
    print(f"Updating password for {user.email}")
    # Set the correct password hash
    user.hashed_password = get_password_hash("lecturer123")
    db.commit()
    print("Password updated!")
else:
    print("User not found!")

db.close()
