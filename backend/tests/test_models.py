"""
Unit tests for Course and Syllabus models
"""
import pytest
from sqlalchemy.orm import Session
from datetime import datetime

from app.models import Course, Syllabus, User
from app.models.user import UserRole


class TestCourseModel:
    """Unit tests for Course model"""
    
    def test_create_course(self, db: Session):
        """Test creating a course"""
        lecturer = User(
            email="lecturer@test.com",
            hashed_password="hashed",
            full_name="Test Lecturer",
            role=UserRole.LECTURER
        )
        db.add(lecturer)
        db.commit()
        db.refresh(lecturer)
        
        course = Course(
            code="CS101",
            name="Computer Science",
            description="Test course",
            lecturer_id=lecturer.id
        )
        db.add(course)
        db.commit()
        db.refresh(course)
        
        assert course.id is not None
        assert course.code == "CS101"
        assert course.name == "Computer Science"
        assert course.lecturer_id == lecturer.id
        assert course.created_at is not None
        assert course.updated_at is not None
    
    def test_course_code_uniqueness(self, db: Session):
        """Test that course codes must be unique"""
        lecturer = User(
            email="lecturer2@test.com",
            hashed_password="hashed",
            full_name="Test Lecturer 2",
            role=UserRole.LECTURER
        )
        db.add(lecturer)
        db.commit()
        db.refresh(lecturer)
        
        course1 = Course(code="CS101", name="Course 1", lecturer_id=lecturer.id)
        db.add(course1)
        db.commit()
        
        course2 = Course(code="CS101", name="Course 2", lecturer_id=lecturer.id)
        db.add(course2)
        
        with pytest.raises(Exception):  # Should raise IntegrityError
            db.commit()
    
    def test_course_lecturer_relationship(self, db: Session):
        """Test course-lecturer relationship"""
        lecturer = User(
            email="lecturer3@test.com",
            hashed_password="hashed",
            full_name="Test Lecturer 3",
            role=UserRole.LECTURER
        )
        db.add(lecturer)
        db.commit()
        db.refresh(lecturer)
        
        course = Course(code="CS102", name="Course", lecturer_id=lecturer.id)
        db.add(course)
        db.commit()
        db.refresh(course)
        
        assert course.lecturer.id == lecturer.id
        assert course.lecturer.email == lecturer.email
        assert len(lecturer.courses) == 1


class TestSyllabusModel:
    """Unit tests for Syllabus model"""
    
    def test_create_syllabus(self, db: Session):
        """Test creating a syllabus entry"""
        lecturer = User(
            email="lecturer4@test.com",
            hashed_password="hashed",
            full_name="Test Lecturer 4",
            role=UserRole.LECTURER
        )
        db.add(lecturer)
        db.commit()
        db.refresh(lecturer)
        
        course = Course(code="CS103", name="Course", lecturer_id=lecturer.id)
        db.add(course)
        db.commit()
        db.refresh(course)
        
        syllabus = Syllabus(
            course_id=course.id,
            week_number=1,
            topic="Introduction",
            content="Week 1 content",
            version=1,
            is_active=True,
            created_by=lecturer.id
        )
        db.add(syllabus)
        db.commit()
        db.refresh(syllabus)
        
        assert syllabus.id is not None
        assert syllabus.course_id == course.id
        assert syllabus.week_number == 1
        assert syllabus.version == 1
        assert syllabus.is_active is True
        assert syllabus.created_at is not None
    
    def test_syllabus_week_number_constraint(self, db: Session):
        """Test that week_number must be between 1 and 14"""
        lecturer = User(
            email="lecturer5@test.com",
            hashed_password="hashed",
            full_name="Test Lecturer 5",
            role=UserRole.LECTURER
        )
        db.add(lecturer)
        db.commit()
        db.refresh(lecturer)
        
        course = Course(code="CS104", name="Course", lecturer_id=lecturer.id)
        db.add(course)
        db.commit()
        db.refresh(course)
        
        # Week 0 should fail
        syllabus1 = Syllabus(
            course_id=course.id,
            week_number=0,
            topic="Invalid",
            created_by=lecturer.id
        )
        db.add(syllabus1)
        with pytest.raises(Exception):
            db.commit()
        db.rollback()
        
        # Week 15 should fail
        syllabus2 = Syllabus(
            course_id=course.id,
            week_number=15,
            topic="Invalid",
            created_by=lecturer.id
        )
        db.add(syllabus2)
        with pytest.raises(Exception):
            db.commit()
    
    def test_unique_active_syllabus_per_week(self, db: Session):
        """Test that only one active syllabus can exist per course per week"""
        lecturer = User(
            email="lecturer6@test.com",
            hashed_password="hashed",
            full_name="Test Lecturer 6",
            role=UserRole.LECTURER
        )
        db.add(lecturer)
        db.commit()
        db.refresh(lecturer)
        
        course = Course(code="CS105", name="Course", lecturer_id=lecturer.id)
        db.add(course)
        db.commit()
        db.refresh(course)
        
        # Create first active syllabus
        syllabus1 = Syllabus(
            course_id=course.id,
            week_number=1,
            topic="Week 1",
            is_active=True,
            created_by=lecturer.id
        )
        db.add(syllabus1)
        db.commit()
        
        # Try to create second active syllabus for same week
        syllabus2 = Syllabus(
            course_id=course.id,
            week_number=1,
            topic="Week 1 Updated",
            is_active=True,
            created_by=lecturer.id
        )
        db.add(syllabus2)
        with pytest.raises(Exception):  # Should raise IntegrityError
            db.commit()
    
    def test_syllabus_versioning(self, db: Session):
        """Test syllabus versioning - multiple inactive versions allowed"""
        lecturer = User(
            email="lecturer7@test.com",
            hashed_password="hashed",
            full_name="Test Lecturer 7",
            role=UserRole.LECTURER
        )
        db.add(lecturer)
        db.commit()
        db.refresh(lecturer)
        
        course = Course(code="CS106", name="Course", lecturer_id=lecturer.id)
        db.add(course)
        db.commit()
        db.refresh(course)
        
        # Create version 1 (active)
        syllabus1 = Syllabus(
            course_id=course.id,
            week_number=1,
            topic="Week 1 v1",
            version=1,
            is_active=True,
            created_by=lecturer.id
        )
        db.add(syllabus1)
        db.commit()
        
        # Deactivate version 1
        syllabus1.is_active = False
        
        # Create version 2 (active)
        syllabus2 = Syllabus(
            course_id=course.id,
            week_number=1,
            topic="Week 1 v2",
            version=2,
            is_active=True,
            created_by=lecturer.id
        )
        db.add(syllabus2)
        db.commit()
        
        # Both should exist
        assert syllabus1.version == 1
        assert syllabus1.is_active is False
        assert syllabus2.version == 2
        assert syllabus2.is_active is True
    
    def test_syllabus_course_relationship(self, db: Session):
        """Test syllabus-course relationship"""
        lecturer = User(
            email="lecturer8@test.com",
            hashed_password="hashed",
            full_name="Test Lecturer 8",
            role=UserRole.LECTURER
        )
        db.add(lecturer)
        db.commit()
        db.refresh(lecturer)
        
        course = Course(code="CS107", name="Course", lecturer_id=lecturer.id)
        db.add(course)
        db.commit()
        db.refresh(course)
        
        syllabus = Syllabus(
            course_id=course.id,
            week_number=1,
            topic="Week 1",
            created_by=lecturer.id
        )
        db.add(syllabus)
        db.commit()
        db.refresh(syllabus)
        
        assert syllabus.course.id == course.id
        assert len(course.syllabus) == 1
    
    def test_cascade_delete(self, db: Session):
        """Test that deleting a course cascades to syllabus"""
        lecturer = User(
            email="lecturer9@test.com",
            hashed_password="hashed",
            full_name="Test Lecturer 9",
            role=UserRole.LECTURER
        )
        db.add(lecturer)
        db.commit()
        db.refresh(lecturer)
        
        course = Course(code="CS108", name="Course", lecturer_id=lecturer.id)
        db.add(course)
        db.commit()
        db.refresh(course)
        
        syllabus = Syllabus(
            course_id=course.id,
            week_number=1,
            topic="Week 1",
            created_by=lecturer.id
        )
        db.add(syllabus)
        db.commit()
        
        syllabus_id = syllabus.id
        
        # Delete course
        db.delete(course)
        db.commit()
        
        # Syllabus should be deleted
        deleted_syllabus = db.query(Syllabus).filter(Syllabus.id == syllabus_id).first()
        assert deleted_syllabus is None

