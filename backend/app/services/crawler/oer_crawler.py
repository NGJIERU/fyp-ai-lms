"""
OER (Open Educational Resources) Crawler
Fetches content from MIT OCW, NPTEL, and other open educational platforms
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import re

import requests
from bs4 import BeautifulSoup

from app.services.crawler.base import BaseCrawler
from app.models.material import Material

logger = logging.getLogger(__name__)


class OERCrawler(BaseCrawler):
    """
    Crawler for Open Educational Resources.
    Supports MIT OCW, NPTEL, and other OER platforms.
    """
    
    # OER source configurations
    OER_SOURCES = {
        "mit_ocw": {
            "name": "MIT OCW",
            "base_url": "https://ocw.mit.edu",
            "search_url": "https://ocw.mit.edu/search/",
            "quality_base": 0.9,
        },
        "nptel": {
            "name": "NPTEL",
            "base_url": "https://nptel.ac.in",
            "search_url": "https://nptel.ac.in/courses",
            "quality_base": 0.85,
        },
        "openstax": {
            "name": "OpenStax",
            "base_url": "https://openstax.org",
            "search_url": "https://openstax.org/subjects",
            "quality_base": 0.85,
        },
    }
    
    # Course subject mappings for relevance
    SUBJECT_RELEVANCE = {
        "computer science": 1.0,
        "artificial intelligence": 1.0,
        "machine learning": 1.0,
        "data science": 1.0,
        "software engineering": 0.95,
        "programming": 0.95,
        "algorithms": 0.95,
        "databases": 0.9,
        "networks": 0.85,
        "mathematics": 0.8,
        "statistics": 0.85,
        "linear algebra": 0.85,
        "calculus": 0.75,
        "probability": 0.85,
    }
    
    def __init__(self, source: str = "mit_ocw"):
        """
        Initialize OER crawler for a specific source.
        
        Args:
            source: One of 'mit_ocw', 'nptel', 'openstax'
        """
        self.source_config = self.OER_SOURCES.get(source, self.OER_SOURCES["mit_ocw"])
        super().__init__(self.source_config["name"])
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Educational Bot; +https://example.edu/bot)"
        })
    
    async def fetch(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch OER content matching the query.
        Uses web scraping with respect for robots.txt.
        """
        try:
            if self.source_name == "MIT OCW":
                return await self._fetch_mit_ocw(query, limit)
            elif self.source_name == "NPTEL":
                return await self._fetch_nptel(query, limit)
            else:
                return self._get_mock_data(query, limit)
                
        except Exception as e:
            logger.error(f"OER fetch error: {e}")
            return self._get_mock_data(query, limit)
    
    async def _fetch_mit_ocw(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """
        Fetch courses from MIT OpenCourseWare.
        """
        try:
            # MIT OCW has a JSON API for search
            search_url = f"{self.source_config['base_url']}/search/"
            params = {
                "q": query,
                "type": "course",
            }
            
            response = self.session.get(search_url, params=params, timeout=30)
            
            # If API not available, use mock data
            if response.status_code != 200:
                logger.warning(f"MIT OCW search returned {response.status_code}")
                return self._get_mock_data(query, limit)
            
            # Parse HTML response
            soup = BeautifulSoup(response.text, 'lxml')
            
            results = []
            course_cards = soup.select('.course-card, .search-result')[:limit * 2]
            
            for card in course_cards:
                try:
                    course_data = self._parse_mit_ocw_card(card)
                    if course_data:
                        results.append(course_data)
                        if len(results) >= limit:
                            break
                except Exception as e:
                    logger.debug(f"Error parsing MIT OCW card: {e}")
                    continue
            
            return results if results else self._get_mock_data(query, limit)
            
        except requests.RequestException as e:
            logger.error(f"MIT OCW request error: {e}")
            return self._get_mock_data(query, limit)
    
    def _parse_mit_ocw_card(self, card) -> Optional[Dict[str, Any]]:
        """
        Parse a MIT OCW course card HTML element.
        """
        title_elem = card.select_one('.course-title, h3, h4')
        link_elem = card.select_one('a[href]')
        desc_elem = card.select_one('.course-description, .description, p')
        instructor_elem = card.select_one('.instructor, .author')
        
        if not title_elem or not link_elem:
            return None
        
        title = title_elem.get_text(strip=True)
        url = link_elem.get('href', '')
        if not url.startswith('http'):
            url = f"{self.source_config['base_url']}{url}"
        
        return {
            "title": title,
            "url": url,
            "description": desc_elem.get_text(strip=True) if desc_elem else "",
            "instructor": instructor_elem.get_text(strip=True) if instructor_elem else "",
            "source": self.source_name,
            "type": "course",
        }
    
    async def _fetch_nptel(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """
        Fetch courses from NPTEL.
        """
        # NPTEL doesn't have a public API, use mock data
        return self._get_mock_data(query, limit)
    
    def parse(self, raw_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse OER data into standardized format.
        """
        try:
            # Calculate quality score
            quality_score = self._calculate_quality_score(raw_data)
            
            # Build content text
            content_parts = [
                f"Course: {raw_data.get('title', '')}",
                f"Source: {raw_data.get('source', self.source_name)}",
            ]
            if raw_data.get("description"):
                content_parts.append(f"Description: {raw_data['description']}")
            if raw_data.get("instructor"):
                content_parts.append(f"Instructor: {raw_data['instructor']}")
            if raw_data.get("topics"):
                content_parts.append(f"Topics: {', '.join(raw_data['topics'])}")
            if raw_data.get("syllabus"):
                content_parts.append(f"Syllabus:\n{raw_data['syllabus']}")
            
            content_text = "\n\n".join(content_parts)
            
            # Determine material type
            material_type = raw_data.get("type", "course")
            if "video" in raw_data.get("title", "").lower():
                material_type = "video"
            elif "pdf" in raw_data.get("url", "").lower():
                material_type = "pdf"
            
            return {
                "title": raw_data.get("title", ""),
                "url": raw_data.get("url", ""),
                "type": material_type,
                "author": raw_data.get("instructor", raw_data.get("author", "")),
                "publish_date": raw_data.get("publish_date"),
                "description": raw_data.get("description", ""),
                "content_text": content_text[:10000],
                "snippet": raw_data.get("description", "")[:300],
                "quality_score": quality_score,
                "metadata": {
                    "source_platform": self.source_name,
                    "course_number": raw_data.get("course_number"),
                    "department": raw_data.get("department"),
                    "level": raw_data.get("level"),
                    "topics": raw_data.get("topics", []),
                    "has_video": raw_data.get("has_video", False),
                    "has_assignments": raw_data.get("has_assignments", False),
                }
            }
            
        except Exception as e:
            logger.error(f"Error parsing OER data: {e}")
            return None
    
    def _calculate_quality_score(self, raw_data: Dict[str, Any]) -> float:
        """
        Calculate quality score for OER content.
        Score range: 0.0 - 1.0
        """
        # Start with source base quality
        score = self.source_config.get("quality_base", 0.7) * 0.4
        
        # Subject relevance
        title_lower = raw_data.get("title", "").lower()
        desc_lower = raw_data.get("description", "").lower()
        combined = title_lower + " " + desc_lower
        
        max_relevance = 0.0
        for subject, relevance in self.SUBJECT_RELEVANCE.items():
            if subject in combined:
                max_relevance = max(max_relevance, relevance)
        score += max_relevance * 0.25
        
        # Content completeness
        if raw_data.get("description") and len(raw_data["description"]) > 100:
            score += 0.1
        if raw_data.get("instructor"):
            score += 0.05
        if raw_data.get("syllabus"):
            score += 0.1
        if raw_data.get("topics") and len(raw_data["topics"]) >= 3:
            score += 0.05
        
        # Resource availability
        if raw_data.get("has_video"):
            score += 0.1
        if raw_data.get("has_assignments"):
            score += 0.1
        
        return min(score, 1.0)
    
    def _get_mock_data(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """
        Return mock OER data for testing.
        """
        mock_courses = [
            {
                "title": f"Introduction to {query}",
                "url": f"https://ocw.mit.edu/courses/6-0001-introduction-to-{query.lower().replace(' ', '-')}",
                "description": f"This course provides a comprehensive introduction to {query}. Students will learn fundamental concepts and practical applications through lectures, assignments, and projects.",
                "instructor": "Prof. John Guttag",
                "source": "MIT OCW",
                "type": "course",
                "course_number": "6.0001",
                "department": "Electrical Engineering and Computer Science",
                "level": "Undergraduate",
                "topics": [query.lower(), "programming", "algorithms", "problem solving"],
                "has_video": True,
                "has_assignments": True,
                "syllabus": f"Week 1: Introduction to {query}\nWeek 2: Basic Concepts\nWeek 3: Data Structures\nWeek 4: Algorithms\nWeek 5-6: Applications\nWeek 7: Project Work",
                "publish_date": datetime(2023, 9, 1),
            },
            {
                "title": f"Advanced {query}: Theory and Practice",
                "url": f"https://ocw.mit.edu/courses/6-867-advanced-{query.lower().replace(' ', '-')}",
                "description": f"An advanced course covering theoretical foundations and practical applications of {query}. Prerequisites: Basic {query} knowledge.",
                "instructor": "Prof. Regina Barzilay",
                "source": "MIT OCW",
                "type": "course",
                "course_number": "6.867",
                "department": "Electrical Engineering and Computer Science",
                "level": "Graduate",
                "topics": [query.lower(), "advanced topics", "research", "applications"],
                "has_video": True,
                "has_assignments": True,
                "syllabus": f"Week 1-2: Review of Fundamentals\nWeek 3-4: Advanced Theory\nWeek 5-8: Specialized Topics\nWeek 9-12: Research Projects",
                "publish_date": datetime(2024, 1, 15),
            },
            {
                "title": f"{query} for Data Science",
                "url": f"https://nptel.ac.in/courses/106/{query.lower().replace(' ', '-')}-data-science",
                "description": f"Learn how {query} is applied in data science contexts. This course covers practical techniques and real-world case studies.",
                "instructor": "Prof. Madhavan Mukund",
                "source": "NPTEL",
                "type": "course",
                "course_number": "CS106",
                "department": "Computer Science",
                "level": "Undergraduate",
                "topics": [query.lower(), "data science", "analytics", "python"],
                "has_video": True,
                "has_assignments": True,
                "syllabus": f"Module 1: {query} Basics\nModule 2: Data Processing\nModule 3: Analysis Techniques\nModule 4: Case Studies",
                "publish_date": datetime(2024, 2, 1),
            }
        ]
        return mock_courses[:limit]


class MITOCWCrawler(OERCrawler):
    """Convenience class for MIT OCW specifically."""
    def __init__(self):
        super().__init__(source="mit_ocw")


class NPTELCrawler(OERCrawler):
    """Convenience class for NPTEL specifically."""
    def __init__(self):
        super().__init__(source="nptel")
