"""
Unit tests for CrawlerManager and crawling workflow
"""
import pytest
import uuid
from sqlalchemy.orm import Session

from app.models import Material, CrawlLog
from app.services.crawler.manager import CrawlerManager
from app.services.crawler.base import BaseCrawler
from tests.conftest import TestingSessionLocal


class DummyCrawler(BaseCrawler):
    """Simple dummy crawler for testing happy path"""

    def __init__(self, source_name: str = "dummy"):
        super().__init__(source_name)

    async def fetch(self, query: str, limit: int = 10):
        # Generate unique URLs for each run
        base_id = str(uuid.uuid4())
        return [
            {"title": "Resource 1", "url": f"https://example.com/{base_id}/1", "type": "video"},
            {"title": "Resource 2", "url": f"https://example.com/{base_id}/2", "type": "article"},
            # Duplicate URL (should be skipped by dedup)
            {"title": "Resource 1 Duplicate", "url": f"https://example.com/{base_id}/1", "type": "video"},
        ][:limit]

    def parse(self, raw_data):
        return raw_data


class ErrorCrawler(BaseCrawler):
    """Crawler that raises to test error handling"""

    def __init__(self, source_name: str = "error_source"):
        super().__init__(source_name)

    async def fetch(self, query: str, limit: int = 10):
        raise RuntimeError("Fetch failed")

    def parse(self, raw_data):
        return None


class TestCrawlerManager:
    """Unit tests for CrawlerManager"""

    def test_register_and_get_crawler(self):
        """Test registering and retrieving crawlers"""
        manager = CrawlerManager()
        crawler = DummyCrawler(source_name="youtube")

        manager.register_crawler(crawler)

        assert manager.get_crawler("youtube") is crawler
        assert manager.get_crawler("github") is None

    @pytest.mark.asyncio
    async def test_run_crawler_saves_materials_and_log(self, db: Session):
        """Test that run_crawler saves materials and updates CrawlLog"""
        # Inject TestingSessionLocal so manager uses the same in-memory DB
        manager = CrawlerManager(db_session_factory=TestingSessionLocal)

        crawler = DummyCrawler(source_name="dummy_source")
        manager.register_crawler(crawler)

        await manager.run_crawler("dummy_source", query="python", limit=10)

        db.expire_all()

        # Two unique URLs, so two materials should be saved
        materials = db.query(Material).all()
        assert len(materials) == 2

        # Verify CrawlLog entry
        logs = db.query(CrawlLog).filter(CrawlLog.crawler_type == "dummy_source").all()
        assert len(logs) == 1
        log = logs[0]
        assert log.status == "completed"
        assert log.items_fetched == 2
        assert log.finished_at is not None

    @pytest.mark.asyncio
    async def test_run_crawler_error_updates_log(self, db: Session):
        """Test that errors during crawling are captured in CrawlLog"""
        # Inject TestingSessionLocal so manager uses the same in-memory DB
        manager = CrawlerManager(db_session_factory=TestingSessionLocal)

        crawler = ErrorCrawler(source_name="error_source")
        manager.register_crawler(crawler)

        await manager.run_crawler("error_source", query="python", limit=5)

        db.expire_all()

        log = db.query(CrawlLog).filter(CrawlLog.crawler_type == "error_source").first()
        assert log is not None
        assert log.status == "failed"
        assert log.error_message is not None
        assert "Fetch failed" in log.error_message
        assert log.finished_at is not None

    @pytest.mark.asyncio
    async def test_run_crawler_unknown_source(self, db: Session):
        """Test that running an unknown crawler type does not create logs or materials"""
        manager = CrawlerManager(db_session_factory=TestingSessionLocal)

        await manager.run_crawler("nonexistent", query="python", limit=5)

        materials = db.query(Material).all()
        logs = db.query(CrawlLog).all()
        assert materials == []
        assert logs == []
