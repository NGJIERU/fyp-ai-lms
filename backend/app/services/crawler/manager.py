import logging
from typing import List, Type, Dict, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import traceback

from app.core.database import SessionLocal
from app.models.material import Material, CrawlLog, MaterialTopic
from app.models.syllabus import Syllabus
from app.models.course import Course
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
                db.flush()  # Get the material ID
                
                # Auto-map to relevant courses based on syllabus matching
                mappings_created = self._auto_map_material(db, new_material)
                logger.debug(f"Created {mappings_created} mappings for material {new_material.id}")
                
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
    
    def _auto_map_material(self, db: Session, material: Material) -> int:
        """
        Auto-map a crawled material to relevant courses based on keyword matching.
        Creates MaterialTopic entries with approved_by_lecturer=False for review.
        
        Returns number of mappings created.
        """
        mappings_created = 0
        
        # Get material text for matching
        material_text = f"{material.title or ''} {material.description or ''} {material.content_text or ''}".lower()
        
        # Get all active syllabuses
        syllabuses = (
            db.query(Syllabus)
            .filter(Syllabus.is_active == True)
            .all()
        )
        
        for syllabus in syllabuses:
            # Simple keyword matching based on syllabus topic
            topic_keywords = syllabus.topic.lower().split()
            
            # Check if any significant keywords match (skip common words)
            common_words = {'to', 'the', 'and', 'or', 'a', 'an', 'in', 'of', 'for', 'with', '&', '-'}
            significant_keywords = [kw for kw in topic_keywords if kw not in common_words and len(kw) > 2]
            
            # Count matches
            matches = sum(1 for kw in significant_keywords if kw in material_text)
            
            # Require at least 2 keyword matches or 50% of keywords
            min_matches = max(2, len(significant_keywords) // 2)
            
            if matches >= min_matches:
                # Check if mapping already exists
                existing = (
                    db.query(MaterialTopic)
                    .filter(
                        MaterialTopic.material_id == material.id,
                        MaterialTopic.course_id == syllabus.course_id,
                        MaterialTopic.week_number == syllabus.week_number
                    )
                    .first()
                )
                
                if not existing:
                    # Calculate relevance score based on match ratio
                    relevance_score = min(matches / len(significant_keywords), 1.0) if significant_keywords else 0.5
                    
                    mapping = MaterialTopic(
                        material_id=material.id,
                        course_id=syllabus.course_id,
                        week_number=syllabus.week_number,
                        relevance_score=relevance_score,
                        approved_by_lecturer=False  # Pending review!
                    )
                    db.add(mapping)
                    mappings_created += 1
                    
                    logger.info(
                        f"Auto-mapped material {material.id} to course {syllabus.course_id} "
                        f"week {syllabus.week_number} (relevance: {relevance_score:.2f})"
                    )
        
        return mappings_created
