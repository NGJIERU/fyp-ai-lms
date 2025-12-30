import logging
from typing import List, Type, Dict
from sqlalchemy.orm import Session
from datetime import datetime
import traceback

from app.core.database import SessionLocal
from app.models.material import Material, CrawlLog
from app.services.crawler.base import BaseCrawler

logger = logging.getLogger(__name__)

class CrawlerManager:
    """
    Orchestrates multiple crawlers, handles logging, and saves data.
    """
    
    def __init__(self, db_session_factory=None):
        self.crawlers: Dict[str, BaseCrawler] = {}
        self.db_session_factory = db_session_factory or SessionLocal

    def register_crawler(self, crawler: BaseCrawler):
        """Register a crawler instance"""
        # Store with lowercase key for case-insensitive lookup
        self.crawlers[crawler.source_name.lower()] = crawler

    def get_crawler(self, source_name: str) -> BaseCrawler:
        # Lookup with lowercase for case-insensitive matching
        return self.crawlers.get(source_name.lower())

    async def run_crawler(self, source_name: str, query: str, limit: int = 10):
        """
        Run a specific crawler by source name.
        """
        crawler = self.get_crawler(source_name)
        if not crawler:
            logger.error(f"Crawler for source '{source_name}' not found.")
            return

        db = self.db_session_factory()
        log_entry = CrawlLog(
            crawler_type=source_name,
            status="running",
            items_fetched=0
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)

        try:
            logger.info(f"Starting crawl for {source_name} with query '{query}'")
            
            # 1. Fetch
            raw_items = await crawler.fetch(query, limit)
            
            items_saved = 0
            seen_urls = set()  # Track URLs within this batch
            
            for raw_item in raw_items:
                # 2. Parse
                parsed_item = crawler.parse(raw_item)
                if not parsed_item:
                    continue
                
                # 3. Normalize
                material_data = crawler.normalize(parsed_item)
                url = material_data["url"]
                
                # Deduplicate within batch
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                
                # 4. Save (Deduplicate against DB)
                # Check if URL already exists
                existing = db.query(Material).filter(Material.url == url).first()
                if existing:
                    # Optional: Update existing? For now, skip.
                    continue
                
                # Check content hash
                existing_hash = db.query(Material).filter(Material.content_hash == material_data["content_hash"]).first()
                if existing_hash:
                    continue

                new_material = Material(**material_data)
                db.add(new_material)
                items_saved += 1
            
            db.commit()
            
            # Update log
            log_entry.status = "completed"
            log_entry.items_fetched = items_saved
            log_entry.finished_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Completed crawl for {source_name}. Saved {items_saved} items.")

        except Exception as e:
            logger.error(f"Error running crawler {source_name}: {e}")
            error_trace = traceback.format_exc()
            
            log_entry.status = "failed"
            log_entry.error_message = str(e) + "\n" + error_trace
            log_entry.finished_at = datetime.utcnow()
            db.commit()
        finally:
            db.close()
