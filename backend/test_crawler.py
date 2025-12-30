"""
Test script to directly run crawler and check database logging
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.crawler import YouTubeCrawler, GitHubCrawler
from app.services.crawler.manager import CrawlerManager
from app.core.database import SessionLocal
from app.models.material import CrawlLog

async def test_crawler():
    print("=" * 60)
    print("Testing Crawler System")
    print("=" * 60)
    
    # Create manager
    manager = CrawlerManager()
    
    # Register crawlers
    youtube = YouTubeCrawler()
    github = GitHubCrawler()
    
    manager.register_crawler(youtube)
    manager.register_crawler(github)
    
    print(f"\nRegistered crawlers: {list(manager.crawlers.keys())}")
    
    # Test YouTube crawler
    print("\n" + "=" * 60)
    print("Running YouTube Crawler...")
    print("=" * 60)
    
    try:
        await manager.run_crawler("youtube", "python tutorial", limit=3)
        print("✓ YouTube crawler completed")
    except Exception as e:
        print(f"✗ YouTube crawler failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Check database
    print("\n" + "=" * 60)
    print("Checking Database Logs...")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        logs = db.query(CrawlLog).order_by(CrawlLog.started_at.desc()).limit(5).all()
        print(f"\nFound {len(logs)} crawler logs:")
        for log in logs:
            print(f"  - {log.crawler_type}: {log.status} ({log.items_fetched} items)")
            if log.error_message:
                print(f"    Error: {log.error_message[:100]}...")
    finally:
        db.close()
    
    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_crawler())
