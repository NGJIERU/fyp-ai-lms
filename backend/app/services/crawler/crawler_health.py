"""
Crawler Health Service - Monitor and log crawler operations
Provides health checks, statistics, and error tracking for all crawlers
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.material import CrawlLog, Material

logger = logging.getLogger(__name__)


class CrawlerHealthService:
    """
    Service for monitoring crawler health and logging operations.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def start_crawl(self, crawler_type: str) -> CrawlLog:
        """
        Start a new crawl session and return the log entry.
        
        Args:
            crawler_type: Type of crawler (youtube, arxiv, github, etc.)
            
        Returns:
            CrawlLog entry for tracking
        """
        log = CrawlLog(
            crawler_type=crawler_type,
            status="running",
            items_fetched=0,
            started_at=datetime.now(timezone.utc)
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        
        logger.info(f"[{crawler_type}] Crawl started (log_id={log.id})")
        return log
    
    def update_progress(self, log: CrawlLog, items_fetched: int):
        """
        Update crawl progress.
        
        Args:
            log: CrawlLog entry
            items_fetched: Current number of items fetched
        """
        log.items_fetched = items_fetched
        self.db.commit()
        
        logger.debug(f"[{log.crawler_type}] Progress: {items_fetched} items")
    
    def complete_crawl(self, log: CrawlLog, items_fetched: int):
        """
        Mark crawl as completed successfully.
        
        Args:
            log: CrawlLog entry
            items_fetched: Final number of items fetched
        """
        log.status = "completed"
        log.items_fetched = items_fetched
        log.finished_at = datetime.now(timezone.utc)
        self.db.commit()
        
        duration = (log.finished_at - log.started_at).total_seconds()
        logger.info(
            f"[{log.crawler_type}] Crawl completed: "
            f"{items_fetched} items in {duration:.1f}s (log_id={log.id})"
        )
    
    def fail_crawl(self, log: CrawlLog, error_message: str):
        """
        Mark crawl as failed with error message.
        
        Args:
            log: CrawlLog entry
            error_message: Description of the error
        """
        log.status = "failed"
        log.error_message = error_message[:1000]  # Truncate long errors
        log.finished_at = datetime.now(timezone.utc)
        self.db.commit()
        
        logger.error(f"[{log.crawler_type}] Crawl failed: {error_message} (log_id={log.id})")
    
    def get_health_summary(self) -> Dict[str, Any]:
        """
        Get overall crawler health summary.
        
        Returns:
            Dictionary with health metrics
        """
        now = datetime.now(timezone.utc)
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        
        # Recent crawls (24h)
        recent_crawls = (
            self.db.query(CrawlLog)
            .filter(CrawlLog.started_at >= last_24h)
            .all()
        )
        
        # Stats by crawler type
        crawler_stats = {}
        for log in recent_crawls:
            if log.crawler_type not in crawler_stats:
                crawler_stats[log.crawler_type] = {
                    "total": 0,
                    "completed": 0,
                    "failed": 0,
                    "running": 0,
                    "items_fetched": 0,
                    "last_run": None,
                    "last_error": None,
                }
            
            stats = crawler_stats[log.crawler_type]
            stats["total"] += 1
            stats[log.status] = stats.get(log.status, 0) + 1
            stats["items_fetched"] += log.items_fetched
            
            if stats["last_run"] is None or log.started_at > stats["last_run"]:
                stats["last_run"] = log.started_at
            
            if log.status == "failed" and log.error_message:
                stats["last_error"] = log.error_message
        
        # Overall counts
        total_completed = sum(s["completed"] for s in crawler_stats.values())
        total_failed = sum(s["failed"] for s in crawler_stats.values())
        total_running = sum(s["running"] for s in crawler_stats.values())
        
        # Materials stats
        total_materials = self.db.query(func.count(Material.id)).scalar()
        materials_24h = (
            self.db.query(func.count(Material.id))
            .filter(Material.created_at >= last_24h)
            .scalar()
        )
        
        # Calculate health score (0-100)
        health_score = 100
        if total_completed + total_failed > 0:
            success_rate = total_completed / (total_completed + total_failed)
            health_score = int(success_rate * 100)
        
        return {
            "health_score": health_score,
            "status": "healthy" if health_score >= 80 else "degraded" if health_score >= 50 else "unhealthy",
            "period": "last_24h",
            "summary": {
                "total_crawls": len(recent_crawls),
                "completed": total_completed,
                "failed": total_failed,
                "running": total_running,
            },
            "materials": {
                "total": total_materials,
                "added_24h": materials_24h,
            },
            "crawlers": crawler_stats,
            "generated_at": now.isoformat(),
        }
    
    def get_recent_logs(
        self,
        crawler_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get recent crawl logs with optional filters.
        
        Args:
            crawler_type: Filter by crawler type
            status: Filter by status
            limit: Maximum logs to return
            
        Returns:
            List of log entries
        """
        query = self.db.query(CrawlLog).order_by(CrawlLog.started_at.desc())
        
        if crawler_type:
            query = query.filter(CrawlLog.crawler_type == crawler_type)
        if status:
            query = query.filter(CrawlLog.status == status)
        
        logs = query.limit(limit).all()
        
        return [
            {
                "id": log.id,
                "crawler_type": log.crawler_type,
                "status": log.status,
                "items_fetched": log.items_fetched,
                "error_message": log.error_message,
                "started_at": log.started_at.isoformat() if log.started_at else None,
                "finished_at": log.finished_at.isoformat() if log.finished_at else None,
                "duration_seconds": (
                    (log.finished_at - log.started_at).total_seconds()
                    if log.finished_at and log.started_at else None
                ),
            }
            for log in logs
        ]
    
    def get_crawler_stats(self, crawler_type: str, days: int = 7) -> Dict[str, Any]:
        """
        Get detailed stats for a specific crawler.
        
        Args:
            crawler_type: Type of crawler
            days: Number of days to analyze
            
        Returns:
            Detailed statistics
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        
        logs = (
            self.db.query(CrawlLog)
            .filter(
                CrawlLog.crawler_type == crawler_type,
                CrawlLog.started_at >= cutoff
            )
            .all()
        )
        
        if not logs:
            return {
                "crawler_type": crawler_type,
                "period_days": days,
                "total_runs": 0,
                "message": "No crawl data available for this period"
            }
        
        completed = [l for l in logs if l.status == "completed"]
        failed = [l for l in logs if l.status == "failed"]
        
        avg_items = sum(l.items_fetched for l in completed) / len(completed) if completed else 0
        avg_duration = (
            sum((l.finished_at - l.started_at).total_seconds() for l in completed if l.finished_at)
            / len(completed) if completed else 0
        )
        
        return {
            "crawler_type": crawler_type,
            "period_days": days,
            "total_runs": len(logs),
            "completed": len(completed),
            "failed": len(failed),
            "success_rate": len(completed) / len(logs) * 100 if logs else 0,
            "avg_items_per_run": round(avg_items, 1),
            "avg_duration_seconds": round(avg_duration, 1),
            "total_items_fetched": sum(l.items_fetched for l in logs),
            "recent_errors": [
                {"error": l.error_message, "at": l.started_at.isoformat()}
                for l in failed[-5:] if l.error_message
            ],
        }


def get_crawler_health_service(db: Session) -> CrawlerHealthService:
    """Get a crawler health service instance."""
    return CrawlerHealthService(db)
