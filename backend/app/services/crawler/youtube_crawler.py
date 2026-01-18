"""
YouTube Crawler - Fetches educational video metadata and transcripts
Uses YouTube Data API v3 and youtube-transcript-api for transcripts
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import re
from pathlib import Path

from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled

from app.services.crawler.base import BaseCrawler
from app.services.crawler.async_http import get_async_http_client
from app.models.material import Material

logger = logging.getLogger(__name__)


class YouTubeCrawler(BaseCrawler):
    """
    Crawler for YouTube educational videos.
    Fetches video metadata and transcripts for educational content.
    Uses curated channel lists for higher quality results.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__("YouTube")
        self.api_key = api_key or os.getenv("YOUTUBE_API_KEY")
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.curated_channels = self._load_curated_channels()
    
    def _load_curated_channels(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load curated channels from config file."""
        config_path = Path(__file__).parent.parent.parent / "config" / "curated_channels.json"
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load curated channels config: {e}")
            return {}
    
    def get_channel_ids_for_subject(self, subject: str) -> List[str]:
        """
        Get curated channel IDs for a subject.
        Maps common subject names to config keys.
        """
        subject_lower = subject.lower()
        
        # Map subject keywords to config keys
        if any(kw in subject_lower for kw in ["data", "statistic", "machine learning", "ml", "pandas", "numpy"]):
            channels = self.curated_channels.get("data_science", [])
        elif any(kw in subject_lower for kw in ["ai", "artificial", "neural", "deep learning", "llm", "nlp"]):
            channels = self.curated_channels.get("artificial_intelligence", [])
        elif any(kw in subject_lower for kw in ["software", "programming", "web", "backend", "frontend", "algorithm"]):
            channels = self.curated_channels.get("software_engineering", [])
        else:
            # Combine all channels for unknown subjects
            channels = []
            for ch_list in self.curated_channels.values():
                channels.extend(ch_list)
        
        return [ch["channel_id"] for ch in channels if "channel_id" in ch]
    
    async def fetch(self, query: str, limit: int = 10, subject: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch YouTube videos matching the query.
        If subject is provided, searches within curated channels for that subject.
        Otherwise falls back to general YouTube search.
        """
        if not self.api_key:
            logger.warning("YouTube API key not configured. Using mock data.")
            return self._get_mock_data(query, limit)
        
        try:
            http_client = get_async_http_client()
            all_videos = []
            
            # Get curated channel IDs for the subject
            channel_ids = self.get_channel_ids_for_subject(subject) if subject else []
            
            if channel_ids:
                # Search within each curated channel (up to 5 channels to limit API calls)
                for channel_id in channel_ids[:5]:
                    if len(all_videos) >= limit * 2:
                        break
                    
                    search_url = f"{self.base_url}/search"
                    params = {
                        "part": "snippet",
                        "q": query,
                        "type": "video",
                        "channelId": channel_id,  # Search within this channel
                        "maxResults": min(limit, 10),
                        "relevanceLanguage": "en",
                        "key": self.api_key
                    }
                    
                    try:
                        search_results = await http_client.get(search_url, params=params)
                        items = search_results.get("items", [])
                        all_videos.extend(items)
                    except Exception as e:
                        logger.debug(f"Error searching channel {channel_id}: {e}")
                        continue
            
            # If no curated results, fall back to general search
            if not all_videos:
                search_url = f"{self.base_url}/search"
                params = {
                    "part": "snippet",
                    "q": f"{query} tutorial education",
                    "type": "video",
                    "maxResults": min(limit * 2, 50),
                    "relevanceLanguage": "en",
                    "videoDuration": "medium",
                    "videoDefinition": "high",
                    "key": self.api_key
                }
                search_results = await http_client.get(search_url, params=params)
                all_videos = search_results.get("items", [])
            
            # Get video details for more metadata
            video_ids = [item["id"]["videoId"] for item in all_videos if item.get("id", {}).get("videoId")]
            if not video_ids:
                return []
            
            videos_url = f"{self.base_url}/videos"
            videos_params = {
                "part": "snippet,statistics,contentDetails",
                "id": ",".join(video_ids[:limit * 2]),
                "key": self.api_key
            }
            
            videos_data = await http_client.get(videos_url, params=videos_params)
            
            return videos_data.get("items", [])[:limit]
            
        except Exception as e:
            logger.error(f"YouTube API error: {e}")
            return self._get_mock_data(query, limit)
    
    def parse(self, raw_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse YouTube video data into standardized format.
        """
        try:
            snippet = raw_data.get("snippet", {})
            statistics = raw_data.get("statistics", {})
            content_details = raw_data.get("contentDetails", {})
            
            video_id = raw_data.get("id")
            if isinstance(video_id, dict):
                video_id = video_id.get("videoId")
            
            if not video_id:
                return None
            
            # Get transcript if available
            transcript_text = self._get_transcript(video_id)
            
            # Parse duration
            duration = self._parse_duration(content_details.get("duration", ""))
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(
                channel_title=snippet.get("channelTitle", ""),
                view_count=int(statistics.get("viewCount", 0)),
                like_count=int(statistics.get("likeCount", 0)),
                has_transcript=bool(transcript_text),
                duration_minutes=duration
            )
            
            # Parse publish date
            publish_date = None
            if snippet.get("publishedAt"):
                try:
                    publish_date = datetime.fromisoformat(
                        snippet["publishedAt"].replace("Z", "+00:00")
                    )
                except ValueError:
                    pass
            
            return {
                "title": snippet.get("title", ""),
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "type": "video",
                "author": snippet.get("channelTitle", ""),
                "publish_date": publish_date,
                "description": snippet.get("description", "")[:500],
                "content_text": transcript_text,
                "snippet": snippet.get("description", "")[:200],
                "quality_score": quality_score,
                "metadata": {
                    "video_id": video_id,
                    "channel_id": snippet.get("channelId"),
                    "view_count": int(statistics.get("viewCount", 0)),
                    "like_count": int(statistics.get("likeCount", 0)),
                    "duration_minutes": duration,
                    "has_transcript": bool(transcript_text)
                }
            }
            
        except Exception as e:
            logger.error(f"Error parsing YouTube data: {e}")
            return None
    
    def _get_transcript(self, video_id: str) -> Optional[str]:
        """
        Fetch video transcript using youtube-transcript-api.
        """
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
            # Combine transcript segments
            full_text = " ".join([segment["text"] for segment in transcript_list])
            # Limit length
            return full_text[:10000] if full_text else None
        except (NoTranscriptFound, TranscriptsDisabled):
            logger.debug(f"No transcript available for video {video_id}")
            return None
        except Exception as e:
            logger.debug(f"Error fetching transcript for {video_id}: {e}")
            return None
    
    def _parse_duration(self, duration_str: str) -> int:
        """
        Parse ISO 8601 duration to minutes.
        Example: PT1H30M15S -> 90
        """
        if not duration_str:
            return 0
        
        pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
        match = re.match(pattern, duration_str)
        if not match:
            return 0
        
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        
        return hours * 60 + minutes + (1 if seconds > 30 else 0)
    
    def _calculate_quality_score(
        self,
        channel_title: str,
        view_count: int,
        like_count: int,
        has_transcript: bool,
        duration_minutes: int
    ) -> float:
        """
        Calculate quality score based on multiple factors.
        Score range: 0.0 - 1.0
        """
        score = 0.0
        
        # Domain authority (educational channel bonus)
        curated_channel_names = []
        for ch_list in self.curated_channels.values():
            curated_channel_names.extend([ch.get("channel_name", "").lower() for ch in ch_list])
        
        if any(name in channel_title.lower() for name in curated_channel_names if name):
            score += 0.3  # Curated channel bonus
        else:
            score += 0.1  # Base score for unknown channels
        
        # Popularity (view count)
        if view_count > 1000000:
            score += 0.2
        elif view_count > 100000:
            score += 0.15
        elif view_count > 10000:
            score += 0.1
        elif view_count > 1000:
            score += 0.05
        
        # Engagement (like ratio approximation)
        if view_count > 0 and like_count > 0:
            like_ratio = like_count / view_count
            if like_ratio > 0.05:
                score += 0.15
            elif like_ratio > 0.03:
                score += 0.1
            elif like_ratio > 0.01:
                score += 0.05
        
        # Transcript availability (important for RAG)
        if has_transcript:
            score += 0.2
        
        # Duration (prefer medium-length tutorials)
        if 10 <= duration_minutes <= 30:
            score += 0.15
        elif 5 <= duration_minutes <= 60:
            score += 0.1
        elif duration_minutes > 60:
            score += 0.05
        
        return min(score, 1.0)
    
    def _get_mock_data(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """
        Return mock data for testing without API key.
        """
        mock_videos = [
            {
                "id": "mock_video_1",
                "snippet": {
                    "title": f"Introduction to {query} - Complete Tutorial",
                    "description": f"Learn {query} from scratch in this comprehensive tutorial.",
                    "channelTitle": "freeCodeCamp.org",
                    "channelId": "UC8butISFwT-Wl7EV0hUK0BQ",
                    "publishedAt": "2024-01-15T10:00:00Z"
                },
                "statistics": {
                    "viewCount": "150000",
                    "likeCount": "8500"
                },
                "contentDetails": {
                    "duration": "PT45M30S"
                }
            },
            {
                "id": "mock_video_2",
                "snippet": {
                    "title": f"{query} for Beginners - Step by Step Guide",
                    "description": f"A beginner-friendly guide to understanding {query}.",
                    "channelTitle": "Corey Schafer",
                    "channelId": "UCCezIgC97PvUuR4_gbFUs5g",
                    "publishedAt": "2024-02-20T14:00:00Z"
                },
                "statistics": {
                    "viewCount": "85000",
                    "likeCount": "4200"
                },
                "contentDetails": {
                    "duration": "PT25M15S"
                }
            }
        ]
        return mock_videos[:limit]
