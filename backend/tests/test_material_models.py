"""
Unit tests for Material, MaterialTopic, and CrawlLog models
"""
import pytest
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models import User, Course, Material, MaterialTopic, CrawlLog


class TestMaterialModel:
    """Unit tests for Material model"""

    def test_create_material(self, db: Session):
        """Test basic material creation with required fields"""
        material = Material(
            title="Intro to AI",
            url="https://example.com/ai",
            source="OER",
            type="article",
            content_hash="hash_intro_ai"
        )
        db.add(material)
        db.commit()
        db.refresh(material)

        assert material.id is not None
        assert material.title == "Intro to AI"
        assert material.quality_score == 0.0  # default

    def test_material_url_uniqueness(self, db: Session):
        """Test that material URLs must be unique"""
        material1 = Material(
            title="Resource 1",
            url="https://example.com/resource",
            source="MIT OCW",
            type="pdf",
            content_hash="hash_1"
        )
        db.add(material1)
        db.commit()

        material2 = Material(
            title="Resource 2",
            url="https://example.com/resource",
            source="MIT OCW",
            type="pdf",
            content_hash="hash_2"
        )
        db.add(material2)
        with pytest.raises(IntegrityError):
            db.commit()

    def test_material_quality_score_constraint(self, db: Session):
        """Test that quality_score must be between 0.0 and 1.0"""
        material = Material(
            title="Bad Score",
            url="https://example.com/bad-score",
            source="OER",
            type="article",
            quality_score=1.5,
            content_hash="hash_bad_score"
        )
        db.add(material)
        # SQLite enforces CHECK constraint - should raise IntegrityError
        with pytest.raises(IntegrityError):
            db.commit()


class TestMaterialTopicModel:
    """Unit tests for MaterialTopic model"""

    def test_create_material_topic(self, db: Session):
        """Test creating a material-topic mapping"""
        # Create prerequisites
        lecturer = User(
            email="lecturer@test.com",
            hashed_password="hashed",
            role="lecturer"
        )
        db.add(lecturer)
        db.commit()

        course = Course(
            code="CS101",
            name="Intro to CS",
            lecturer_id=lecturer.id
        )
        db.add(course)
        db.commit()

        material = Material(
            title="Week 1 Material",
            url="https://example.com/material-lecturer",
            source="YouTube",
            type="video",
            content_hash="hash_material_lecturer"
        )
        db.add(material)
        db.commit()

        # Create mapping
        topic = MaterialTopic(
            material_id=material.id,
            course_id=course.id,
            week_number=1,
            relevance_score=0.95
        )
        db.add(topic)
        db.commit()
        db.refresh(topic)

        assert topic.id is not None
        assert topic.material_id == material.id
        assert topic.course_id == course.id
        assert topic.week_number == 1
        assert topic.relevance_score == 0.95

    def test_material_topic_week_constraint(self, db: Session):
        """Test that week_number must be between 1 and 14"""
        lecturer = User(
            email="lecturer2@test.com",
            hashed_password="hashed",
            role="lecturer"
        )
        db.add(lecturer)
        db.commit()

        course = Course(
            code="CS102",
            name="Data Structures",
            lecturer_id=lecturer.id
        )
        db.add(course)
        db.commit()

        material = Material(
            title="DS Resource",
            url="https://example.com/ds",
            source="OER",
            type="pdf",
            content_hash="hash_ds"
        )
        db.add(material)
        db.commit()

        # Week 15 is out of range (1-14)
        topic = MaterialTopic(
            material_id=material.id,
            course_id=course.id,
            week_number=15,
            relevance_score=0.9
        )
        db.add(topic)
        with pytest.raises(IntegrityError):
            db.commit()

    def test_material_topics_cascade_on_course_delete(self, db: Session):
        """Test that MaterialTopic entries are deleted when course is deleted"""
        lecturer = User(
            email="lecturer3@test.com",
            hashed_password="hashed",
            role="lecturer"
        )
        db.add(lecturer)
        db.commit()

        course = Course(
            code="CS103",
            name="Algorithms",
            lecturer_id=lecturer.id
        )
        db.add(course)
        db.commit()

        material = Material(
            title="Algo Resource",
            url="https://example.com/algo",
            source="YouTube",
            type="video",
            content_hash="hash_algo"
        )
        db.add(material)
        db.commit()

        topic = MaterialTopic(
            material_id=material.id,
            course_id=course.id,
            week_number=2,
            relevance_score=0.85
        )
        db.add(topic)
        db.commit()

        topic_id = topic.id

        # Delete course
        db.delete(course)
        db.commit()
        db.expire_all()  # Clear identity map to see DB state

        # MaterialTopic should be cascade deleted
        deleted_topic = db.query(MaterialTopic).filter(MaterialTopic.id == topic_id).first()
        assert deleted_topic is None


class TestCrawlLogModel:
    """Unit tests for CrawlLog model"""

    def test_create_crawl_log(self, db: Session):
        """Test creating a crawl log entry"""
        log = CrawlLog(
            crawler_type="youtube",
            status="running",
            items_fetched=0
        )
        db.add(log)
        db.commit()
        db.refresh(log)

        assert log.id is not None
        assert log.crawler_type == "youtube"
        assert log.status == "running"
        assert log.started_at is not None
        assert log.finished_at is None

    def test_crawl_log_completion(self, db: Session):
        """Test updating crawl log on completion"""
        from datetime import datetime

        log = CrawlLog(
            crawler_type="github",
            status="running",
            items_fetched=0
        )
        db.add(log)
        db.commit()

        # Simulate completion
        log.status = "completed"
        log.items_fetched = 25
        log.finished_at = datetime.utcnow()
        db.commit()
        db.refresh(log)

        assert log.status == "completed"
        assert log.items_fetched == 25
        assert log.finished_at is not None

    def test_crawl_log_failure(self, db: Session):
        """Test updating crawl log on failure"""
        from datetime import datetime

        log = CrawlLog(
            crawler_type="oer",
            status="running",
            items_fetched=0
        )
        db.add(log)
        db.commit()

        # Simulate failure
        log.status = "failed"
        log.error_message = "Connection timeout"
        log.finished_at = datetime.utcnow()
        db.commit()
        db.refresh(log)

        assert log.status == "failed"
        assert log.error_message == "Connection timeout"
        assert log.finished_at is not None
