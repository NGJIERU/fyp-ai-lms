#!/usr/bin/env python3
"""
Script to trigger material crawling for courses.
Run from backend directory: python scripts/crawl_materials.py

Usage:
    python scripts/crawl_materials.py --course-id 1
    python scripts/crawl_materials.py --all
    python scripts/crawl_materials.py --query "machine learning" --subject "Data Science"
"""
import sys
import asyncio
import argparse
import logging

# Add parent directory to path for imports
sys.path.insert(0, '.')

# Load environment variables from .env
from dotenv import load_dotenv
load_dotenv()

from app.core.database import SessionLocal
from app.models.course import Course
from app.services.crawler.manager import CrawlerManager
from app.services.crawler import YouTubeCrawler, GitHubCrawler, ArxivCrawler, OERCrawler

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_crawler_manager():
    """Initialize and return crawler manager with all crawlers registered."""
    manager = CrawlerManager()
    manager.register_crawler(YouTubeCrawler())
    manager.register_crawler(GitHubCrawler())
    manager.register_crawler(ArxivCrawler())
    manager.register_crawler(OERCrawler())
    return manager


async def crawl_for_course(course_id: int, limit_per_topic: int = 5):
    """Crawl materials for a specific course."""
    manager = get_crawler_manager()
    await manager.crawl_for_course(course_id, limit_per_topic)


async def crawl_all_courses(limit_per_topic: int = 3):
    """Crawl materials for all active courses."""
    db = SessionLocal()
    try:
        courses = db.query(Course).filter(Course.is_active == True).all()
        logger.info(f"Found {len(courses)} active courses")
        
        manager = get_crawler_manager()
        for course in courses:
            logger.info(f"Processing course: {course.name} (ID: {course.id})")
            await manager.crawl_for_course(course.id, limit_per_topic)
    finally:
        db.close()


async def crawl_query(query: str, subject: str = None, limit: int = 10, sources: list = None):
    """Crawl specific query across selected sources."""
    manager = get_crawler_manager()
    
    sources = sources or ['youtube', 'github', 'arxiv']
    
    for source in sources:
        logger.info(f"Crawling {source} for: {query} (subject: {subject})")
        await manager.run_crawler(source, query, limit, subject=subject)


def main():
    parser = argparse.ArgumentParser(description='Crawl educational materials')
    parser.add_argument('--course-id', type=int, help='Crawl for specific course ID')
    parser.add_argument('--all', action='store_true', help='Crawl for all active courses')
    parser.add_argument('--query', type=str, help='Custom search query')
    parser.add_argument('--subject', type=str, help='Subject for curated source matching')
    parser.add_argument('--limit', type=int, default=5, help='Max items per source (default: 5)')
    parser.add_argument('--sources', nargs='+', default=['youtube', 'github', 'arxiv'],
                        help='Sources to crawl (default: youtube github arxiv)')
    
    args = parser.parse_args()
    
    if args.course_id:
        logger.info(f"Crawling materials for course ID: {args.course_id}")
        asyncio.run(crawl_for_course(args.course_id, args.limit))
    elif args.all:
        logger.info("Crawling materials for all courses")
        asyncio.run(crawl_all_courses(args.limit))
    elif args.query:
        logger.info(f"Crawling for query: {args.query}")
        asyncio.run(crawl_query(args.query, args.subject, args.limit, args.sources))
    else:
        parser.print_help()
        print("\nExamples:")
        print("  python scripts/crawl_materials.py --course-id 1")
        print("  python scripts/crawl_materials.py --all --limit 3")
        print("  python scripts/crawl_materials.py --query 'neural networks' --subject 'Artificial Intelligence'")


if __name__ == "__main__":
    main()
