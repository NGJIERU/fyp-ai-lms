import sys
import os

# Ensure app is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine, SessionLocal, Base
from app.models import User, UserRole

# Import all models to ensure they are registered with Base
from app.models import user, course, syllabus, material, performance

# Import seed functions
from seed_demo_data import create_demo_users, create_demo_materials, create_material_mappings, create_enrollments, create_sample_performance
from seed_courses_syllabus import seed_courses_and_syllabus

def main():
    print("🚀 Initializing Demo Database...")
    
    # Force create tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database schema created.")

    db = SessionLocal()
    try:
        # 1. Create Users
        print("👤 Creating Users...")
        created_users = create_demo_users(db)
        
        # Find a lecturer to assign courses to
        lecturer = db.query(User).filter(User.role == UserRole.LECTURER).first()
        if not lecturer:
            print("❌ No lecturer created. Aborting.")
            return

        print(f"👨‍🏫 Using Lecturer: {lecturer.full_name} (ID: {lecturer.id})")

        # 2. Seed Courses (using the found lecturer ID)
        print("📚 Seeding Courses...")
        seed_courses_and_syllabus(db, lecturer_id=lecturer.id)

        # 3. Create Materials and other mappings (from seed_demo_data)
        print("📦 Seeding Materials & Mappings...")
        materials = create_demo_materials(db)
        create_material_mappings(db, materials)
        create_enrollments(db, created_users)
        create_sample_performance(db, created_users)
        
        print("\n✨ Demo Setup Complete!")
        print("--------------------------------")
        print("Credentials:")
        print("Student: alice@lms.edu / student123")
        print("Lecturer: smith@lms.edu / lecturer123")
        print("Admin: admin@lms.edu / admin123")
        
    except Exception as e:
        print(f"❌ Error setting up demo: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
