import sys
import os
import random
from datetime import datetime, timedelta

# Add parent directory to path to allow imports from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.material import Material, CrawlLog
from app.services.processing.embedding_service import get_embedding_service

def backfill_embeddings(db):
    print("--- Backfilling Embeddings ---")
    embedding_service = get_embedding_service(model_name="local_fast", use_openai=False)
    
    # Fetch materials without embeddings
    materials = db.query(Material).filter(Material.embedding == None).all()
    print(f"Found {len(materials)} materials without embeddings.")
    
    if not materials:
        print("No materials to process.")
        return

    success_count = 0
    for material in materials:
        try:
            print(f"Processing: {material.title[:50]}...")
            # Convert material to dict for embedding service
            material_data = {
                "title": material.title,
                "description": material.description,
                "snippet": material.snippet,
                "content_text": material.content_text
            }
            
            # Generate embedding
            vector = embedding_service.embed_material(material_data)
            
            # Save to DB
            material.embedding = vector
            success_count += 1
        except Exception as e:
            print(f"Failed to embed material {material.id}: {e}")
            
    db.commit()
    print(f"Successfully generated embeddings for {success_count} materials.\n")

def seed_crawler_logs(db):
    print("--- Seeding Crawler Logs ---")
    
    # Check if we already have recent logs to avoid spamming
    recent_logs = db.query(CrawlLog).order_by(CrawlLog.started_at.desc()).limit(5).all()
    if recent_logs:
        print(f"Found {len(recent_logs)} recent logs. Skipping seed to preserve history.")
        # Uncomment below to force seed if needed
        # return 

    crawlers = ["github", "youtube", "arxiv", "oer_commons"]
    statuses = ["completed", "completed", "completed", "failed"]
    
    # clear existing logs to ensure a clean slate if requested (optional)
    # db.query(CrawlLog).delete() 

    new_logs = []
    
    # 1. Successful run 2 hours ago
    new_logs.append(CrawlLog(
        crawler_type="github",
        status="completed",
        items_fetched=12,
        started_at=datetime.utcnow() - timedelta(hours=2),
        finished_at=datetime.utcnow() - timedelta(hours=1, minutes=58),
    ))

    # 2. Successful run 5 hours ago
    new_logs.append(CrawlLog(
        crawler_type="arxiv",
        status="completed",
        items_fetched=5,
        started_at=datetime.utcnow() - timedelta(hours=5),
        finished_at=datetime.utcnow() - timedelta(hours=4, minutes=59),
    ))

    # 3. Failed run 1 day ago
    new_logs.append(CrawlLog(
        crawler_type="youtube",
        status="failed",
        items_fetched=0,
        error_message="API Quota Exceeded for key ending in ...x892",
        started_at=datetime.utcnow() - timedelta(days=1),
        finished_at=datetime.utcnow() - timedelta(days=1, minutes=1),
    ))
    
    # 4. Successful large run 1 day ago
    new_logs.append(CrawlLog(
        crawler_type="oer_commons",
        status="completed",
        items_fetched=45,
        started_at=datetime.utcnow() - timedelta(days=1, hours=2),
        finished_at=datetime.utcnow() - timedelta(days=1, hours=1, minutes=30),
    ))

    for log in new_logs:
        db.add(log)
    
    db.commit()
    print(f"Seeded {len(new_logs)} crawler logs.\n")

def main():
    db = SessionLocal()
    try:
        backfill_embeddings(db)
        seed_crawler_logs(db)
    finally:
        db.close()

if __name__ == "__main__":
    main()
