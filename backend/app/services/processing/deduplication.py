"""
Content Deduplication Service
Detects and manages duplicate materials from crawlers
"""
import hashlib
import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlparse, parse_qs, urlencode
from difflib import SequenceMatcher
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.material import Material, MaterialTopic

logger = logging.getLogger(__name__)


class DeduplicationService:
    """
    Service for detecting and managing duplicate materials.
    Uses URL normalization and title similarity.
    """
    
    # Similarity threshold for title matching (0.0 - 1.0)
    TITLE_SIMILARITY_THRESHOLD = 0.85
    
    # URL parameters to ignore when normalizing
    IGNORE_URL_PARAMS = {
        'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
        'ref', 'source', 'feature', 'app', 'si'  # YouTube 'si' param
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def normalize_url(self, url: str) -> str:
        """
        Normalize URL for comparison.
        Removes tracking params and standardizes format.
        
        Args:
            url: Original URL
            
        Returns:
            Normalized URL string
        """
        if not url:
            return ""
        
        try:
            parsed = urlparse(url.lower().strip())
            
            # Remove www prefix
            netloc = parsed.netloc
            if netloc.startswith('www.'):
                netloc = netloc[4:]
            
            # Handle YouTube special cases
            if 'youtube.com' in netloc or 'youtu.be' in netloc:
                return self._normalize_youtube_url(url)
            
            # Handle arXiv special cases
            if 'arxiv.org' in netloc:
                return self._normalize_arxiv_url(url)
            
            # Filter out tracking parameters
            query_params = parse_qs(parsed.query)
            filtered_params = {
                k: v for k, v in query_params.items()
                if k.lower() not in self.IGNORE_URL_PARAMS
            }
            
            # Rebuild URL
            clean_query = urlencode(filtered_params, doseq=True) if filtered_params else ""
            path = parsed.path.rstrip('/')
            
            return f"{parsed.scheme}://{netloc}{path}{'?' + clean_query if clean_query else ''}"
            
        except Exception as e:
            logger.warning(f"URL normalization failed for {url}: {e}")
            return url.lower().strip()
    
    def _normalize_youtube_url(self, url: str) -> str:
        """Normalize YouTube URLs to standard format."""
        parsed = urlparse(url)
        
        # Extract video ID
        video_id = None
        if 'youtu.be' in parsed.netloc:
            video_id = parsed.path.strip('/')
        else:
            query_params = parse_qs(parsed.query)
            video_id = query_params.get('v', [None])[0]
        
        if video_id:
            return f"https://youtube.com/watch?v={video_id}"
        return url.lower()
    
    def _normalize_arxiv_url(self, url: str) -> str:
        """Normalize arXiv URLs to standard format."""
        # Extract paper ID from various arXiv URL formats
        match = re.search(r'(\d{4}\.\d{4,5})', url)
        if match:
            paper_id = match.group(1)
            return f"https://arxiv.org/abs/{paper_id}"
        return url.lower()
    
    def compute_content_hash(self, content: str) -> str:
        """
        Compute SHA-256 hash of content for exact duplicate detection.
        
        Args:
            content: Text content to hash
            
        Returns:
            64-character hex hash string
        """
        if not content:
            return ""
        
        # Normalize whitespace and case
        normalized = re.sub(r'\s+', ' ', content.lower().strip())
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()
    
    def title_similarity(self, title1: str, title2: str) -> float:
        """
        Compute similarity ratio between two titles.
        
        Args:
            title1: First title
            title2: Second title
            
        Returns:
            Similarity ratio (0.0 - 1.0)
        """
        if not title1 or not title2:
            return 0.0
        
        # Normalize titles
        t1 = re.sub(r'[^\w\s]', '', title1.lower())
        t2 = re.sub(r'[^\w\s]', '', title2.lower())
        
        return SequenceMatcher(None, t1, t2).ratio()
    
    def find_duplicates(
        self,
        material: Material,
        check_url: bool = True,
        check_title: bool = True,
        check_hash: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Find potential duplicates of a material.
        
        Args:
            material: Material to check
            check_url: Check for URL duplicates
            check_title: Check for title similarity
            check_hash: Check for content hash matches
            
        Returns:
            List of potential duplicates with match info
        """
        duplicates = []
        
        # URL-based detection
        if check_url and material.url:
            normalized_url = self.normalize_url(material.url)
            url_matches = (
                self.db.query(Material)
                .filter(
                    Material.id != material.id,
                    Material.url.isnot(None)
                )
                .all()
            )
            
            for m in url_matches:
                if self.normalize_url(m.url) == normalized_url:
                    duplicates.append({
                        "material_id": m.id,
                        "title": m.title,
                        "match_type": "url",
                        "confidence": 1.0,
                        "details": f"Same normalized URL: {normalized_url}"
                    })
        
        # Content hash detection
        if check_hash and material.content_hash:
            hash_matches = (
                self.db.query(Material)
                .filter(
                    Material.id != material.id,
                    Material.content_hash == material.content_hash
                )
                .all()
            )
            
            for m in hash_matches:
                # Avoid adding if already found by URL
                if not any(d["material_id"] == m.id for d in duplicates):
                    duplicates.append({
                        "material_id": m.id,
                        "title": m.title,
                        "match_type": "content_hash",
                        "confidence": 1.0,
                        "details": "Identical content hash"
                    })
        
        # Title similarity detection
        if check_title and material.title:
            # Get materials from same source for comparison
            title_candidates = (
                self.db.query(Material)
                .filter(
                    Material.id != material.id,
                    Material.source == material.source
                )
                .all()
            )
            
            for m in title_candidates:
                # Skip if already found
                if any(d["material_id"] == m.id for d in duplicates):
                    continue
                
                similarity = self.title_similarity(material.title, m.title)
                if similarity >= self.TITLE_SIMILARITY_THRESHOLD:
                    duplicates.append({
                        "material_id": m.id,
                        "title": m.title,
                        "match_type": "title_similarity",
                        "confidence": round(similarity, 3),
                        "details": f"Title similarity: {similarity:.1%}"
                    })
        
        return duplicates
    
    def scan_all_duplicates(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Scan database for all duplicate groups.
        
        Args:
            limit: Maximum number of duplicate groups to return
            
        Returns:
            List of duplicate groups
        """
        # Find materials with duplicate URLs
        url_groups = {}
        materials = self.db.query(Material).filter(Material.url.isnot(None)).all()
        
        for m in materials:
            normalized = self.normalize_url(m.url)
            if normalized not in url_groups:
                url_groups[normalized] = []
            url_groups[normalized].append(m)
        
        # Filter to only groups with duplicates
        duplicate_groups = []
        for url, group in url_groups.items():
            if len(group) > 1:
                # Sort by quality score descending
                group.sort(key=lambda x: x.quality_score, reverse=True)
                duplicate_groups.append({
                    "match_type": "url",
                    "normalized_url": url,
                    "count": len(group),
                    "materials": [
                        {
                            "id": m.id,
                            "title": m.title,
                            "source": m.source,
                            "quality_score": m.quality_score,
                            "created_at": m.created_at.isoformat() if m.created_at else None
                        }
                        for m in group
                    ],
                    "recommended_keep": group[0].id  # Highest quality
                })
        
        # Also check content hash duplicates
        hash_counts = (
            self.db.query(Material.content_hash, func.count(Material.id))
            .filter(Material.content_hash.isnot(None), Material.content_hash != "")
            .group_by(Material.content_hash)
            .having(func.count(Material.id) > 1)
            .all()
        )
        
        for content_hash, count in hash_counts:
            hash_group = (
                self.db.query(Material)
                .filter(Material.content_hash == content_hash)
                .order_by(Material.quality_score.desc())
                .all()
            )
            
            # Check if already covered by URL
            urls = [self.normalize_url(m.url) for m in hash_group if m.url]
            if urls and urls[0] in url_groups and len(url_groups[urls[0]]) > 1:
                continue
            
            duplicate_groups.append({
                "match_type": "content_hash",
                "content_hash": content_hash[:16] + "...",
                "count": len(hash_group),
                "materials": [
                    {
                        "id": m.id,
                        "title": m.title,
                        "source": m.source,
                        "quality_score": m.quality_score,
                        "created_at": m.created_at.isoformat() if m.created_at else None
                    }
                    for m in hash_group
                ],
                "recommended_keep": hash_group[0].id
            })
        
        return duplicate_groups[:limit]
    
    def merge_duplicates(
        self,
        keep_id: int,
        remove_ids: List[int],
        transfer_topics: bool = True
    ) -> Dict[str, Any]:
        """
        Merge duplicate materials by keeping one and removing others.
        
        Args:
            keep_id: ID of material to keep
            remove_ids: IDs of materials to remove
            transfer_topics: Whether to transfer topic mappings
            
        Returns:
            Merge result summary
        """
        keep_material = self.db.query(Material).filter(Material.id == keep_id).first()
        if not keep_material:
            raise ValueError(f"Material {keep_id} not found")
        
        removed_count = 0
        topics_transferred = 0
        
        for remove_id in remove_ids:
            if remove_id == keep_id:
                continue
            
            remove_material = self.db.query(Material).filter(Material.id == remove_id).first()
            if not remove_material:
                continue
            
            # Transfer topic mappings
            if transfer_topics:
                existing_topics = (
                    self.db.query(MaterialTopic)
                    .filter(MaterialTopic.material_id == remove_id)
                    .all()
                )
                
                for topic in existing_topics:
                    # Check if mapping already exists
                    exists = (
                        self.db.query(MaterialTopic)
                        .filter(
                            MaterialTopic.material_id == keep_id,
                            MaterialTopic.course_id == topic.course_id,
                            MaterialTopic.week_number == topic.week_number
                        )
                        .first()
                    )
                    
                    if not exists:
                        topic.material_id = keep_id
                        topics_transferred += 1
                    else:
                        self.db.delete(topic)
            
            # Aggregate view/download counts
            keep_material.view_count += remove_material.view_count
            keep_material.download_count += remove_material.download_count
            
            # Delete the duplicate
            self.db.delete(remove_material)
            removed_count += 1
        
        self.db.commit()
        
        logger.info(
            f"Merged duplicates: kept {keep_id}, removed {removed_count} materials, "
            f"transferred {topics_transferred} topic mappings"
        )
        
        return {
            "kept_material_id": keep_id,
            "removed_count": removed_count,
            "topics_transferred": topics_transferred
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get deduplication statistics."""
        total = self.db.query(func.count(Material.id)).scalar()
        with_hash = (
            self.db.query(func.count(Material.id))
            .filter(Material.content_hash.isnot(None), Material.content_hash != "")
            .scalar()
        )
        
        duplicate_groups = self.scan_all_duplicates(limit=1000)
        duplicate_count = sum(g["count"] - 1 for g in duplicate_groups)
        
        return {
            "total_materials": total,
            "materials_with_hash": with_hash,
            "duplicate_groups": len(duplicate_groups),
            "removable_duplicates": duplicate_count,
            "potential_savings_percent": round(duplicate_count / total * 100, 1) if total > 0 else 0
        }


def get_deduplication_service(db: Session) -> DeduplicationService:
    """Get a deduplication service instance."""
    return DeduplicationService(db)
