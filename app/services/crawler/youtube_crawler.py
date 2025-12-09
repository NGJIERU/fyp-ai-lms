"""
YouTube Crawler - Fetches educational video metadata and transcripts
Uses YouTube Data API v3 and youtube-transcript-api for transcripts
"""
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import re

from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
import requests

from app.services.crawler.base import BaseCrawler
from app.models.material import Material

logger = logging.getLogger(__name__)


class YouTubeCrawler(BaseCrawler):
    """
    Crawler for YouTube educational videos.
    Fetches video metadata and transcripts for educational content.
    """
    
    # Educational channels whitelist (domain authority)
    EDUCATIONAL_CHANNELS = {
        "MIT OpenCourseWare": 1.0,
        "Stanford": 0.95,
        "3Blue1Brown": 0.9,
        "Sentdex": 0.85,
        "Corey Schafer": 0.85,
        "freeCodeCamp.org": 0.9,
        "CS Dojo": 0.8,
        "Tech With Tim": 0.8,
        "Traversy Media": 0.85,
        "The Coding Train": 0.85,
        "StatQuest with Josh Starmer": 0.9,
        "Two Minute Papers": 0.85,
        "Computerphile": 0.9,
        "Numberphile": 0.85,
    }
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__("YouTube")
        self.api_key = api_key or os.getenv("YOUTUBE_API_KEY")
        self.base_url = "https://www.googleapis.com/youtube/v3"
    
    async def fetch(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch YouTube videos matching the query.
        Prioritizes educational content.
        """
        if not self.api_key:
            logger.warning("YouTube API key not configured. Using mock data.")
            return self._get_mock_data(query, limit)
        
        try:
            # Search for videos
            search_url = f"{self.base_url}/search"
            params = {
                "part": "snippet",
                "q": f"{query} tutorial education",
                "type": "video",
                "maxResults": min(limit * 2, 50),  # Fetch more to filter
                "relevanceLanguage": "en",
                "videoDuration": "medium",  # 4-20 minutes
                "videoDefinition": "high",
                "key": self.api_key
            }
            
            response = requests.get(search_url, params=params, timeout=30)
            response.raise_for_status()
            search_results = response.json()
            
            # Get video details for more metadata
            video_ids = [item["id"]["videoId"] for item in search_results.get("items", [])]
            if not video_ids:
                return []
            
            videos_url = f"{self.base_url}/videos"
            videos_params = {
                "part": "snippet,statistics,contentDetails",
                "id": ",".join(video_ids),
                "key": self.api_key
            }
            
            videos_response = requests.get(videos_url, params=videos_params, timeout=30)
            videos_response.raise_for_status()
            videos_data = videos_response.json()
            
            return videos_data.get("items", [])[:limit]
            
        except requests.RequestException as e:
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
        for channel, authority in self.EDUCATIONAL_CHANNELS.items():
            if channel.lower() in channel_title.lower():
                score += authority * 0.3
                break
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
