
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User
from app.models.course import Course
from app.models.performance import TopicPerformance

def simulate_weakness():
    db = SessionLocal()
    try:
        # 1. Get Alice (The Test Student)
        alice = db.query(User).filter(User.email == "alice@student.lms.edu").first()
        if not alice:
            print("❌ Error: User 'alice@student.lms.edu' not found.")
            return

        # 2. Get the first course
        course = db.query(Course).first()
        if not course:
            print("❌ Error: No courses found in DB.")
            return

        print(f"👉 Simulating weakness for Student: {alice.full_name}, Course: {course.name}")

        # 3. Create 'Weak' Performance for Week 2
        week_num = 2
        perf = db.query(TopicPerformance).filter(
            TopicPerformance.student_id == alice.id,
            TopicPerformance.course_id == course.id,
            TopicPerformance.week_number == week_num
        ).first()

        if not perf:
            perf = TopicPerformance(
                student_id=alice.id,
                course_id=course.id,
                week_number=week_num
            )
            db.add(perf)
        
        # Set stats to simulate failure
        perf.total_attempts = 5
        perf.correct_attempts = 1
        perf.average_score = 45.0  # < 60% threshold
        perf.is_weak_topic = True
        perf.mastery_level = "remedial"
        
        db.commit()
        print(f"✅ SUCCESS: Week {week_num} marked as 'Weak Topic' (Score: 45%).")
        print("Please refresh your Student Dashboard to see the changes.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    simulate_weakness()
