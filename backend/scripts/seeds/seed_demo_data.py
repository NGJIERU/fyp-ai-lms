"""
Seed script for demonstration data
Creates sample users, materials, and enrollments for testing
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.core.security import get_password_hash
from app.models import (
    User, UserRole, Course, Syllabus, Material, MaterialTopic,
    StudentEnrollment, QuizAttempt, TopicPerformance
)


def create_demo_users(db: Session):
    """Create demo users for each role."""
    users = [
        # Super Admin
        {
            "email": "admin@lms.edu",
            "password": "admin123",
            "full_name": "System Administrator",
            "role": UserRole.SUPER_ADMIN
        },
        # Lecturers
        {
            "email": "dr.smith@lms.edu",
            "password": "lecturer123",
            "full_name": "Dr. John Smith",
            "role": UserRole.LECTURER
        },
        {
            "email": "dr.chen@lms.edu",
            "password": "lecturer123",
            "full_name": "Dr. Emily Chen",
            "role": UserRole.LECTURER
        },
        # Students
        {
            "email": "alice@student.lms.edu",
            "password": "student123",
            "full_name": "Alice Johnson",
            "role": UserRole.STUDENT
        },
        {
            "email": "bob@student.lms.edu",
            "password": "student123",
            "full_name": "Bob Williams",
            "role": UserRole.STUDENT
        },
        {
            "email": "charlie@student.lms.edu",
            "password": "student123",
            "full_name": "Charlie Brown",
            "role": UserRole.STUDENT
        },
    ]
    
    created_users = {}
    for user_data in users:
        existing = db.query(User).filter(User.email == user_data["email"]).first()
        if existing:
            print(f"  User {user_data['email']} already exists")
            created_users[user_data["email"]] = existing
            continue
        
        user = User(
            email=user_data["email"],
            hashed_password=get_password_hash(user_data["password"]),
            full_name=user_data["full_name"],
            role=user_data["role"],
            is_active=True
        )
        db.add(user)
        db.flush()
        created_users[user_data["email"]] = user
        print(f"  Created user: {user_data['email']} ({user_data['role'].value})")
    
    db.commit()
    return created_users


def create_demo_materials(db: Session):
    """Create sample learning materials."""
    materials = [
        # Python/Data Science materials
        {
            "title": "Python for Data Science - Complete Tutorial",
            "url": "https://www.youtube.com/watch?v=LHBE6Q9XlzI",
            "source": "YouTube",
            "type": "video",
            "author": "freeCodeCamp.org",
            "description": "Learn Python for data science in this comprehensive tutorial covering pandas, numpy, matplotlib and more.",
            "snippet": "A complete guide to Python for data science beginners.",
            "quality_score": 0.85,
            "content_hash": "hash_python_ds_1"
        },
        {
            "title": "Introduction to Machine Learning",
            "url": "https://ocw.mit.edu/courses/6-036-introduction-to-machine-learning/",
            "source": "MIT OCW",
            "type": "course",
            "author": "MIT",
            "description": "This course introduces principles, algorithms, and applications of machine learning from the point of view of modeling and prediction.",
            "snippet": "MIT's comprehensive introduction to machine learning.",
            "quality_score": 0.95,
            "content_hash": "hash_mit_ml_1"
        },
        {
            "title": "Deep Learning Specialization",
            "url": "https://www.coursera.org/specializations/deep-learning",
            "source": "Coursera",
            "type": "course",
            "author": "Andrew Ng",
            "description": "Master Deep Learning, and Break into AI. Learn the foundations of Deep Learning, understand how to build neural networks.",
            "snippet": "Andrew Ng's famous deep learning course.",
            "quality_score": 0.92,
            "content_hash": "hash_dl_spec_1"
        },
        {
            "title": "Attention Is All You Need",
            "url": "https://arxiv.org/abs/1706.03762",
            "source": "arXiv",
            "type": "article",
            "author": "Vaswani et al.",
            "description": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks. We propose a new simple network architecture, the Transformer.",
            "snippet": "The seminal paper introducing the Transformer architecture.",
            "quality_score": 0.98,
            "content_hash": "hash_attention_1"
        },
        {
            "title": "Python Machine Learning Repository",
            "url": "https://github.com/rasbt/python-machine-learning-book",
            "source": "GitHub",
            "type": "repository",
            "author": "Sebastian Raschka",
            "description": "The Python Machine Learning book code repository with example code and notebooks.",
            "snippet": "Code examples for Python Machine Learning book.",
            "quality_score": 0.88,
            "content_hash": "hash_github_ml_1"
        },
        # Software Engineering materials
        {
            "title": "Clean Code: A Handbook of Agile Software Craftsmanship",
            "url": "https://www.oreilly.com/library/view/clean-code/9780136083238/",
            "source": "O'Reilly",
            "type": "article",
            "author": "Robert C. Martin",
            "description": "Even bad code can function. But if code isn't clean, it can bring a development organization to its knees.",
            "snippet": "Essential reading for writing maintainable code.",
            "quality_score": 0.90,
            "content_hash": "hash_clean_code_1"
        },
        {
            "title": "Design Patterns in Python",
            "url": "https://refactoring.guru/design-patterns/python",
            "source": "Refactoring Guru",
            "type": "article",
            "author": "Refactoring Guru",
            "description": "Design patterns are typical solutions to common problems in software design. Each pattern is like a blueprint.",
            "snippet": "Comprehensive guide to design patterns with Python examples.",
            "quality_score": 0.87,
            "content_hash": "hash_design_patterns_1"
        },
        # AI materials
        {
            "title": "Neural Networks and Deep Learning",
            "url": "http://neuralnetworksanddeeplearning.com/",
            "source": "Online Book",
            "type": "article",
            "author": "Michael Nielsen",
            "description": "A free online book explaining the core ideas behind neural networks and deep learning.",
            "snippet": "Free online book on neural networks fundamentals.",
            "quality_score": 0.89,
            "content_hash": "hash_nn_book_1"
        },
    ]
    
    created_materials = []
    for mat_data in materials:
        existing = db.query(Material).filter(Material.url == mat_data["url"]).first()
        if existing:
            print(f"  Material '{mat_data['title'][:40]}...' already exists")
            created_materials.append(existing)
            continue
        
        material = Material(
            title=mat_data["title"],
            url=mat_data["url"],
            source=mat_data["source"],
            type=mat_data["type"],
            author=mat_data["author"],
            description=mat_data["description"],
            snippet=mat_data["snippet"],
            quality_score=mat_data["quality_score"],
            content_hash=mat_data["content_hash"]
        )
        db.add(material)
        db.flush()
        created_materials.append(material)
        print(f"  Created material: {mat_data['title'][:50]}...")
    
    db.commit()
    return created_materials


def create_material_mappings(db: Session, materials: list):
    """Map materials to course weeks."""
    # Get courses
    ds_course = db.query(Course).filter(Course.code == "DS101").first()
    ai_course = db.query(Course).filter(Course.code == "AI201").first()
    se_course = db.query(Course).filter(Course.code == "SE301").first()
    
    if not ds_course or not ai_course:
        print("  Courses not found. Run seed_courses_syllabus.py first.")
        return
    
    # Get a lecturer for approval
    lecturer = db.query(User).filter(User.role == UserRole.LECTURER).first()
    
    mappings = [
        # Data Science course mappings
        {"material_title": "Python for Data Science", "course": ds_course, "week": 1, "relevance": 0.95},
        {"material_title": "Introduction to Machine Learning", "course": ds_course, "week": 5, "relevance": 0.90},
        {"material_title": "Python Machine Learning Repository", "course": ds_course, "week": 6, "relevance": 0.85},
        
        # AI course mappings
        {"material_title": "Introduction to Machine Learning", "course": ai_course, "week": 1, "relevance": 0.92},
        {"material_title": "Deep Learning Specialization", "course": ai_course, "week": 4, "relevance": 0.95},
        {"material_title": "Attention Is All You Need", "course": ai_course, "week": 8, "relevance": 0.98},
        {"material_title": "Neural Networks and Deep Learning", "course": ai_course, "week": 3, "relevance": 0.90},
    ]
    
    # Add SE mappings if course exists
    if se_course:
        mappings.extend([
            {"material_title": "Clean Code", "course": se_course, "week": 2, "relevance": 0.92},
            {"material_title": "Design Patterns in Python", "course": se_course, "week": 5, "relevance": 0.88},
        ])
    
    for mapping in mappings:
        material = next((m for m in materials if mapping["material_title"] in m.title), None)
        if not material:
            continue
        
        existing = db.query(MaterialTopic).filter(
            MaterialTopic.material_id == material.id,
            MaterialTopic.course_id == mapping["course"].id,
            MaterialTopic.week_number == mapping["week"]
        ).first()
        
        if existing:
            continue
        
        topic = MaterialTopic(
            material_id=material.id,
            course_id=mapping["course"].id,
            week_number=mapping["week"],
            relevance_score=mapping["relevance"],
            approved_by_lecturer=True,
            approved_by=lecturer.id if lecturer else None,
            approved_at=datetime.utcnow()
        )
        db.add(topic)
        print(f"  Mapped '{material.title[:30]}...' to {mapping['course'].code} Week {mapping['week']}")
    
    db.commit()


def create_enrollments(db: Session, users: dict):
    """Enroll students in courses."""
    # Get courses
    courses = db.query(Course).all()
    
    # Get student users
    students = [u for email, u in users.items() if u.role == UserRole.STUDENT]
    
    for student in students:
        for course in courses[:3]:  # Enroll in first 3 courses
            existing = db.query(StudentEnrollment).filter(
                StudentEnrollment.student_id == student.id,
                StudentEnrollment.course_id == course.id
            ).first()
            
            if existing:
                continue
            
            enrollment = StudentEnrollment(
                student_id=student.id,
                course_id=course.id,
                is_active=True
            )
            db.add(enrollment)
            print(f"  Enrolled {student.full_name} in {course.code}")
    
    db.commit()


def create_sample_performance(db: Session, users: dict):
    """Create sample quiz attempts and performance data with distinct student personas."""
    import random
    
    # Define student personas with score ranges
    # Alice = Excellent (85-98%), Bob = Normal (55-75%), Charlie = Struggling (25-45%)
    student_profiles = {
        "alice@student.lms.edu": {
            "type": "excellent",
            "score_range": (0.85, 0.98),
            "correct_ratio": 0.9,
            "mastery": "proficient",
            "attempts_range": (3, 5),
        },
        "bob@student.lms.edu": {
            "type": "normal", 
            "score_range": (0.55, 0.75),
            "correct_ratio": 0.6,
            "mastery": "learning",
            "attempts_range": (2, 4),
        },
        "charlie@student.lms.edu": {
            "type": "struggling",
            "score_range": (0.25, 0.45),
            "correct_ratio": 0.3,
            "mastery": "needs_improvement",
            "attempts_range": (1, 3),
        },
    }
    
    courses = db.query(Course).limit(3).all()
    
    for email, user in users.items():
        if user.role != UserRole.STUDENT:
            continue
            
        profile = student_profiles.get(email)
        if not profile:
            continue
        
        print(f"  Creating {profile['type']} student data for {user.full_name}...")
        
        for course in courses:
            # Create performance for first 3 weeks
            for week in range(1, 4):
                # TopicPerformance
                existing_perf = db.query(TopicPerformance).filter(
                    TopicPerformance.student_id == user.id,
                    TopicPerformance.course_id == course.id,
                    TopicPerformance.week_number == week
                ).first()
                
                if not existing_perf:
                    score = random.uniform(*profile["score_range"])
                    total_attempts = random.randint(*profile["attempts_range"])
                    correct_attempts = int(total_attempts * profile["correct_ratio"])
                    
                    performance = TopicPerformance(
                        student_id=user.id,
                        course_id=course.id,
                        week_number=week,
                        total_attempts=total_attempts,
                        correct_attempts=correct_attempts,
                        average_score=score,
                        is_weak_topic=score < 0.6,
                        mastery_level=profile["mastery"],
                        last_attempt_at=datetime.utcnow() - timedelta(days=random.randint(1, 7))
                    )
                    db.add(performance)
                
                # QuizAttempts - create 3-5 quiz attempts per week
                num_attempts = random.randint(3, 5)
                for attempt_idx in range(num_attempts):
                    # Check if quiz attempt already exists
                    is_correct = random.random() < profile["correct_ratio"]
                    score_val = 1.0 if is_correct else 0.0
                    
                    quiz_attempt = QuizAttempt(
                        student_id=user.id,
                        course_id=course.id,
                        week_number=week,
                        question_type="mcq",
                        question_data={"question": f"Sample question {attempt_idx + 1} for week {week}"},
                        student_answer="Sample answer",
                        score=score_val,
                        max_score=1.0,
                        is_correct=is_correct,
                        feedback="Correct!" if is_correct else "Review this topic.",
                        mode="practice",
                        attempted_at=datetime.utcnow() - timedelta(
                            days=random.randint(0, 5),
                            hours=random.randint(0, 23),
                            minutes=random.randint(0, 59)
                        ),
                        time_spent_seconds=random.randint(30, 180)
                    )
                    db.add(quiz_attempt)
    
    db.commit()
    print("  Created distinct student performance profiles")


def main():
    """Main function to seed demo data."""
    print("\n" + "="*60)
    print("Seeding Demo Data for AI-Powered LMS")
    print("="*60 + "\n")
    
    db = SessionLocal()
    
    try:
        print("1. Creating demo users...")
        users = create_demo_users(db)
        
        print("\n2. Creating demo materials...")
        materials = create_demo_materials(db)
        
        print("\n3. Creating material-course mappings...")
        create_material_mappings(db, materials)
        
        print("\n4. Creating student enrollments...")
        create_enrollments(db, users)
        
        print("\n5. Creating sample performance data...")
        create_sample_performance(db, users)
        
        print("\n" + "="*60)
        print("Demo data seeding completed!")
        print("="*60)
        
        print("\n📋 Demo Credentials:")
        print("-" * 40)
        print("Super Admin:  admin@lms.edu / admin123")
        print("Lecturer:     dr.smith@lms.edu / lecturer123")
        print("Student:      alice@student.lms.edu / student123")
        print("-" * 40)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
