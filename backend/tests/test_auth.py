from app.core import security
from app.core.database import SessionLocal
from app.models import User

db = SessionLocal()
user = db.query(User).filter(User.email == 'dr.smith@lms.edu').first()

if user:
    print(f"User found: {user.email}")
    print(f"Role: {user.role}")
    print(f"Active: {user.is_active}")
    print(f"Hash starts with: {user.hashed_password[:30]}")
    
    # Test password verification
    is_valid = security.verify_password("lecturer123", user.hashed_password)
    print(f"Password 'lecturer123' valid: {is_valid}")
    
    # Test token creation
    from datetime import timedelta
    token = security.create_access_token(user.id, timedelta(minutes=30))
    print(f"Token created: {token[:50]}...")
else:
    print("User not found!")

db.close()
