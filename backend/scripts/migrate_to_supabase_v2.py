"""
Migrate data from local PostgreSQL to Supabase using SQLAlchemy ORM
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models import User, Course, Syllabus, Material, MaterialTopic, StudentEnrollment, QuizAttempt, TopicPerformance

# Local PostgreSQL connection
LOCAL_DB_URL = "postgresql://jieru_0901:@localhost/lms_db"

# Supabase PostgreSQL connection
SUPABASE_DB_URL = "postgresql://postgres:Ngjieren%4002@db.yxyplzwvunedqvcdetqg.supabase.co:5432/postgres"

local_engine = create_engine(LOCAL_DB_URL)
supabase_engine = create_engine(SUPABASE_DB_URL)

LocalSession = sessionmaker(bind=local_engine)
SupabaseSession = sessionmaker(bind=supabase_engine)

def main():
    print("🚀 Migrating data from Local PostgreSQL to Supabase...")
    print("="*60)
    
    local_db = LocalSession()
    supabase_db = SupabaseSession()
    
    try:
        # 1. Clear Supabase tables
        print("\n1. Clearing Supabase tables...")
        supabase_db.execute(text("TRUNCATE TABLE quiz_attempts, topic_performance, student_enrollments, material_topics, materials, syllabus, courses, users RESTART IDENTITY CASCADE"))
        supabase_db.commit()
        print("   Tables cleared")
        
        # 2. Migrate Users
        print("\n2. Migrating users...")
        users = local_db.query(User).all()
        for u in users:
            new_user = User(
                id=u.id,
                email=u.email,
                hashed_password=u.hashed_password,
                full_name=u.full_name,
                role=u.role,
                is_active=u.is_active
            )
            supabase_db.merge(new_user)
        supabase_db.commit()
        supabase_db.execute(text("SELECT setval('users_id_seq', (SELECT MAX(id) FROM users))"))
        supabase_db.commit()
        print(f"   Migrated {len(users)} users")
        
        # 3. Migrate Courses
        print("\n3. Migrating courses...")
        courses = local_db.query(Course).all()
        for c in courses:
            new_course = Course(
                id=c.id,
                code=c.code,
                name=c.name,
                description=c.description,
                lecturer_id=c.lecturer_id,
                is_active=c.is_active
            )
            supabase_db.merge(new_course)
        supabase_db.commit()
        supabase_db.execute(text("SELECT setval('courses_id_seq', (SELECT MAX(id) FROM courses))"))
        supabase_db.commit()
        print(f"   Migrated {len(courses)} courses")
        
        # 4. Migrate Syllabus
        print("\n4. Migrating syllabus...")
        syllabus_entries = local_db.query(Syllabus).all()
        for s in syllabus_entries:
            new_syllabus = Syllabus(
                id=s.id,
                course_id=s.course_id,
                week_number=s.week_number,
                topic=s.topic,
                content=s.content,
                version=getattr(s, 'version', 1),
                is_active=getattr(s, 'is_active', True),
                created_by=s.created_by if hasattr(s, 'created_by') else s.course.lecturer_id,
                created_at=s.created_at
            )
            supabase_db.merge(new_syllabus)
        supabase_db.commit()
        supabase_db.execute(text("SELECT setval('syllabus_id_seq', (SELECT MAX(id) FROM syllabus))"))
        supabase_db.commit()
        print(f"   Migrated {len(syllabus_entries)} syllabus entries")
        
        # 5. Migrate Materials
        print("\n5. Migrating materials...")
        materials = local_db.query(Material).all()
        for m in materials:
            new_material = Material(
                id=m.id,
                title=m.title,
                url=m.url,
                source=m.source,
                type=m.type,
                material_type=getattr(m, 'material_type', 'crawled'),
                author=m.author,
                publish_date=getattr(m, 'publish_date', None),
                description=m.description,
                content_text=getattr(m, 'content_text', None),
                snippet=getattr(m, 'snippet', None),
                quality_score=getattr(m, 'quality_score', 0.0),
                content_hash=getattr(m, 'content_hash', None),
                uploaded_by=getattr(m, 'uploaded_by', None),
                file_name=getattr(m, 'file_name', None),
                file_path=getattr(m, 'file_path', None),
                file_size=getattr(m, 'file_size', None),
                content_type=getattr(m, 'content_type', None)
            )
            supabase_db.merge(new_material)
        supabase_db.commit()
        supabase_db.execute(text("SELECT setval('materials_id_seq', (SELECT MAX(id) FROM materials))"))
        supabase_db.commit()
        print(f"   Migrated {len(materials)} materials")
        
        # 6. Migrate Material Topics
        print("\n6. Migrating material topics...")
        material_topics = local_db.query(MaterialTopic).all()
        for mt in material_topics:
            new_mt = MaterialTopic(
                id=mt.id,
                material_id=mt.material_id,
                course_id=mt.course_id,
                week_number=mt.week_number,
                relevance_score=getattr(mt, 'relevance_score', None),
                approved_by_lecturer=getattr(mt, 'approved_by_lecturer', False),
                approved_by=getattr(mt, 'approved_by', None),
                approved_at=getattr(mt, 'approved_at', None)
            )
            supabase_db.merge(new_mt)
        supabase_db.commit()
        supabase_db.execute(text("SELECT setval('material_topics_id_seq', (SELECT MAX(id) FROM material_topics))"))
        supabase_db.commit()
        print(f"   Migrated {len(material_topics)} material topics")
        
        # 7. Migrate Student Enrollments
        print("\n7. Migrating student enrollments...")
        enrollments = local_db.query(StudentEnrollment).all()
        for e in enrollments:
            new_enrollment = StudentEnrollment(
                id=e.id,
                student_id=e.student_id,
                course_id=e.course_id,
                enrolled_at=e.enrolled_at,
                is_active=e.is_active
            )
            supabase_db.merge(new_enrollment)
        supabase_db.commit()
        supabase_db.execute(text("SELECT setval('student_enrollments_id_seq', (SELECT MAX(id) FROM student_enrollments))"))
        supabase_db.commit()
        print(f"   Migrated {len(enrollments)} enrollments")
        
        # 8. Migrate Quiz Attempts
        print("\n8. Migrating quiz attempts...")
        quiz_attempts = local_db.query(QuizAttempt).all()
        for qa in quiz_attempts:
            new_qa = QuizAttempt(
                id=qa.id,
                student_id=qa.student_id,
                course_id=qa.course_id,
                week_number=qa.week_number,
                question_type=qa.question_type,
                question_data=qa.question_data,
                student_answer=qa.student_answer,
                score=qa.score,
                max_score=qa.max_score,
                is_correct=qa.is_correct,
                feedback=qa.feedback,
                mode=qa.mode,
                attempted_at=qa.attempted_at,
                time_spent_seconds=qa.time_spent_seconds
            )
            supabase_db.merge(new_qa)
        supabase_db.commit()
        supabase_db.execute(text("SELECT setval('quiz_attempts_id_seq', (SELECT MAX(id) FROM quiz_attempts))"))
        supabase_db.commit()
        print(f"   Migrated {len(quiz_attempts)} quiz attempts")
        
        # 9. Migrate Topic Performance
        print("\n9. Migrating topic performance...")
        performances = local_db.query(TopicPerformance).all()
        for p in performances:
            new_perf = TopicPerformance(
                id=p.id,
                student_id=p.student_id,
                course_id=p.course_id,
                week_number=p.week_number,
                total_attempts=p.total_attempts,
                correct_attempts=p.correct_attempts,
                average_score=p.average_score,
                is_weak_topic=p.is_weak_topic,
                mastery_level=p.mastery_level,
                last_attempt_at=p.last_attempt_at
            )
            supabase_db.merge(new_perf)
        supabase_db.commit()
        supabase_db.execute(text("SELECT setval('topic_performance_id_seq', (SELECT MAX(id) FROM topic_performance))"))
        supabase_db.commit()
        print(f"   Migrated {len(performances)} performance records")
        
        print("\n" + "="*60)
        print("✅ Migration complete!")
        
        # Verify
        print("\n📊 Final counts in Supabase:")
        result = supabase_db.execute(text("""
            SELECT 'users' as tbl, COUNT(*) FROM users
            UNION ALL SELECT 'courses', COUNT(*) FROM courses
            UNION ALL SELECT 'syllabus', COUNT(*) FROM syllabus
            UNION ALL SELECT 'materials', COUNT(*) FROM materials
            UNION ALL SELECT 'material_topics', COUNT(*) FROM material_topics
            UNION ALL SELECT 'student_enrollments', COUNT(*) FROM student_enrollments
            UNION ALL SELECT 'quiz_attempts', COUNT(*) FROM quiz_attempts
            UNION ALL SELECT 'topic_performance', COUNT(*) FROM topic_performance
        """))
        for row in result:
            print(f"   {row[0]}: {row[1]}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        supabase_db.rollback()
    finally:
        local_db.close()
        supabase_db.close()

if __name__ == "__main__":
    main()
