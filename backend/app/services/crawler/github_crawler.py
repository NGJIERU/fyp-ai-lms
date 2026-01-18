"""
GitHub Crawler - Fetches educational repository metadata
Uses PyGithub library for GitHub API access (wrapped in async)
"""
import os
import json
import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from github import Github, GithubException

from app.services.crawler.base import BaseCrawler
from app.models.material import Material

logger = logging.getLogger(__name__)


class GitHubCrawler(BaseCrawler):
    """
    Crawler for GitHub educational repositories.
    Fetches repository metadata, README content, and code structure.
    Uses curated repository lists for higher quality results.
    """
    
    # Educational topic keywords for filtering
    EDUCATIONAL_KEYWORDS = [
        "tutorial", "course", "learn", "education", "guide",
        "examples", "exercises", "practice", "bootcamp", "curriculum"
    ]
    
    def __init__(self, access_token: Optional[str] = None):
        super().__init__("GitHub")
        self.access_token = access_token or os.getenv("GITHUB_ACCESS_TOKEN")
        self.github = Github(self.access_token) if self.access_token else Github()
        self.curated_repos = self._load_curated_repos()
    
    def _load_curated_repos(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load curated repositories from config file."""
        config_path = Path(__file__).parent.parent.parent / "config" / "curated_github.json"
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load curated GitHub config: {e}")
            return {}
    
    def get_curated_repos_for_subject(self, subject: str) -> List[str]:
        """
        Get curated repo names for a subject.
        Returns list of 'owner/repo' strings.
        """
        subject_lower = subject.lower()
        
        if any(kw in subject_lower for kw in ["data", "statistic", "machine learning", "ml", "pandas", "numpy"]):
            repos = self.curated_repos.get("data_science", [])
        elif any(kw in subject_lower for kw in ["ai", "artificial", "neural", "deep learning", "llm", "nlp"]):
            repos = self.curated_repos.get("artificial_intelligence", [])
        elif any(kw in subject_lower for kw in ["software", "programming", "web", "backend", "frontend", "algorithm"]):
            repos = self.curated_repos.get("software_engineering", [])
        else:
            # Combine all repos for unknown subjects
            repos = []
            for repo_list in self.curated_repos.values():
                repos.extend(repo_list)
        
        return [r["repo"] for r in repos if "repo" in r]
    
    async def fetch(self, query: str, limit: int = 10, subject: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch GitHub repositories matching the query.
        If subject is provided, prioritizes curated repos for that subject.
        Uses asyncio.to_thread to wrap sync PyGithub calls.
        """
        try:
            # Run sync GitHub API calls in thread pool
            return await asyncio.to_thread(
                self._fetch_sync, query, limit, subject
            )
        except Exception as e:
            logger.error(f"GitHub API error: {e}")
            return self._get_mock_data(query, limit)
    
    def _fetch_sync(self, query: str, limit: int, subject: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Synchronous fetch implementation (runs in thread pool).
        Prioritizes curated repos when subject is provided.
        """
        results = []
        
        # First, try to fetch from curated repos if subject is provided
        if subject:
            curated_repo_names = self.get_curated_repos_for_subject(subject)
            query_lower = query.lower()
            
            for repo_name in curated_repo_names[:10]:  # Limit API calls
                if len(results) >= limit:
                    break
                try:
                    repo = self.github.get_repo(repo_name)
                    # Check if query matches repo content
                    repo_text = f"{repo.name} {repo.description or ''} {' '.join(repo.get_topics() or [])}".lower()
                    if any(word in repo_text for word in query_lower.split()):
                        repo_data = self._extract_repo_data(repo)
                        if repo_data:
                            repo_data["is_curated"] = True
                            results.append(repo_data)
                except GithubException as e:
                    logger.debug(f"Error fetching curated repo {repo_name}: {e}")
                    continue
        
        # If not enough results, fall back to general search
        if len(results) < limit:
            search_query = f"{query} in:name,description,readme"
            repos = self.github.search_repositories(
                query=search_query,
                sort="stars",
                order="desc"
            )
            
            for repo in repos[:limit * 2]:
                if len(results) >= limit:
                    break
                try:
                    # Skip if already in results
                    if any(r.get("full_name") == repo.full_name for r in results):
                        continue
                    repo_data = self._extract_repo_data(repo)
                    if repo_data:
                        results.append(repo_data)
                except GithubException as e:
                    logger.debug(f"Error fetching repo {repo.full_name}: {e}")
                    continue
        
        return results
    
    def _extract_repo_data(self, repo) -> Optional[Dict[str, Any]]:
        """
        Extract relevant data from a GitHub repository object.
        """
        try:
            # Get README content
            readme_content = None
            try:
                readme = repo.get_readme()
                readme_content = readme.decoded_content.decode('utf-8')[:5000]
            except GithubException:
                pass
            
            # Get topics/tags
            topics = repo.get_topics() if hasattr(repo, 'get_topics') else []
            
            # Get language statistics
            languages = dict(repo.get_languages()) if hasattr(repo, 'get_languages') else {}
            
            return {
                "full_name": repo.full_name,
                "name": repo.name,
                "description": repo.description or "",
                "html_url": repo.html_url,
                "clone_url": repo.clone_url,
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "watchers": repo.watchers_count,
                "open_issues": repo.open_issues_count,
                "language": repo.language,
                "languages": languages,
                "topics": topics,
                "created_at": repo.created_at,
                "updated_at": repo.updated_at,
                "pushed_at": repo.pushed_at,
                "owner": repo.owner.login,
                "owner_type": repo.owner.type,
                "readme": readme_content,
                "license": repo.license.name if repo.license else None,
                "has_wiki": repo.has_wiki,
                "has_pages": repo.has_pages,
            }
        except Exception as e:
            logger.debug(f"Error extracting repo data: {e}")
            return None
    
    def parse(self, raw_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse GitHub repository data into standardized format.
        """
        try:
            # Calculate quality score
            quality_score = self._calculate_quality_score(raw_data)
            
            # Build content text from README and description
            content_parts = []
            if raw_data.get("description"):
                content_parts.append(raw_data["description"])
            if raw_data.get("readme"):
                content_parts.append(raw_data["readme"])
            content_text = "\n\n".join(content_parts)
            
            # Build snippet
            snippet = raw_data.get("description", "")[:200]
            if raw_data.get("topics"):
                snippet += f" | Topics: {', '.join(raw_data['topics'][:5])}"
            
            return {
                "title": raw_data.get("full_name", raw_data.get("name", "")),
                "url": raw_data.get("html_url", ""),
                "type": "repository",
                "author": raw_data.get("owner", ""),
                "publish_date": raw_data.get("created_at"),
                "description": raw_data.get("description", ""),
                "content_text": content_text[:10000],
                "snippet": snippet[:300],
                "quality_score": quality_score,
                "metadata": {
                    "stars": raw_data.get("stars", 0),
                    "forks": raw_data.get("forks", 0),
                    "language": raw_data.get("language"),
                    "topics": raw_data.get("topics", []),
                    "license": raw_data.get("license"),
                    "last_updated": raw_data.get("pushed_at").isoformat() if raw_data.get("pushed_at") else None,
                    "has_readme": bool(raw_data.get("readme")),
                }
            }
            
        except Exception as e:
            logger.error(f"Error parsing GitHub data: {e}")
            return None
    
    def _calculate_quality_score(self, raw_data: Dict[str, Any]) -> float:
        """
        Calculate quality score based on repository metrics.
        Score range: 0.0 - 1.0
        """
        score = 0.0
        
        # Curated repo/organization bonus
        owner = raw_data.get("owner", "").lower()
        full_name = raw_data.get("full_name", "").lower()
        is_curated = raw_data.get("is_curated", False)
        
        # Check if repo is from curated list
        curated_repos = []
        for repo_list in self.curated_repos.values():
            curated_repos.extend([r.get("repo", "").lower() for r in repo_list])
        
        if is_curated or full_name in curated_repos:
            score += 0.25  # Curated bonus
        elif any(owner in repo for repo in curated_repos):
            score += 0.15  # Known org bonus
        else:
            score += 0.05
        
        # Stars (popularity)
        stars = raw_data.get("stars", 0)
        if stars > 10000:
            score += 0.2
        elif stars > 1000:
            score += 0.15
        elif stars > 100:
            score += 0.1
        elif stars > 10:
            score += 0.05
        
        # Forks (community engagement)
        forks = raw_data.get("forks", 0)
        if forks > 1000:
            score += 0.1
        elif forks > 100:
            score += 0.07
        elif forks > 10:
            score += 0.03
        
        # Documentation (README)
        if raw_data.get("readme"):
            readme_len = len(raw_data["readme"])
            if readme_len > 2000:
                score += 0.15
            elif readme_len > 500:
                score += 0.1
            elif readme_len > 100:
                score += 0.05
        
        # Topics/Tags (well-organized)
        topics = raw_data.get("topics", [])
        if len(topics) >= 5:
            score += 0.1
        elif len(topics) >= 2:
            score += 0.05
        
        # Educational keywords in topics
        educational_match = any(
            kw in " ".join(topics).lower()
            for kw in self.EDUCATIONAL_KEYWORDS
        )
        if educational_match:
            score += 0.1
        
        # Recency (recently updated)
        pushed_at = raw_data.get("pushed_at")
        if pushed_at:
            days_since_update = (datetime.now() - pushed_at.replace(tzinfo=None)).days
            if days_since_update < 30:
                score += 0.1
            elif days_since_update < 180:
                score += 0.05
        
        # License (open source)
        if raw_data.get("license"):
            score += 0.05
        
        return min(score, 1.0)
    
    def _get_mock_data(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """
        Return mock data for testing without API access.
        """
        mock_repos = [
            {
                "full_name": f"TheAlgorithms/{query.replace(' ', '-')}",
                "name": query.replace(' ', '-'),
                "description": f"All {query} algorithms implemented for educational purposes",
                "html_url": f"https://github.com/TheAlgorithms/{query.replace(' ', '-')}",
                "clone_url": f"https://github.com/TheAlgorithms/{query.replace(' ', '-')}.git",
                "stars": 15000,
                "forks": 3500,
                "watchers": 500,
                "open_issues": 25,
                "language": "Python",
                "languages": {"Python": 95000},
                "topics": ["algorithms", "education", "tutorial", query.lower()],
                "created_at": datetime(2020, 1, 15),
                "updated_at": datetime(2024, 11, 1),
                "pushed_at": datetime(2024, 11, 1),
                "owner": "TheAlgorithms",
                "owner_type": "Organization",
                "readme": f"# {query} Algorithms\n\nA comprehensive collection of {query} algorithms for learning purposes.\n\n## Contents\n- Basic algorithms\n- Advanced techniques\n- Practice problems",
                "license": "MIT",
                "has_wiki": True,
                "has_pages": True,
            },
            {
                "full_name": f"microsoft/{query.replace(' ', '-')}-tutorial",
                "name": f"{query.replace(' ', '-')}-tutorial",
                "description": f"Official Microsoft tutorial for {query}",
                "html_url": f"https://github.com/microsoft/{query.replace(' ', '-')}-tutorial",
                "clone_url": f"https://github.com/microsoft/{query.replace(' ', '-')}-tutorial.git",
                "stars": 8500,
                "forks": 2100,
                "watchers": 350,
                "open_issues": 12,
                "language": "Python",
                "languages": {"Python": 75000, "Jupyter Notebook": 25000},
                "topics": ["tutorial", "microsoft", "education", query.lower()],
                "created_at": datetime(2021, 6, 10),
                "updated_at": datetime(2024, 10, 15),
                "pushed_at": datetime(2024, 10, 15),
                "owner": "microsoft",
                "owner_type": "Organization",
                "readme": f"# {query} Tutorial\n\nLearn {query} with hands-on examples.\n\n## Prerequisites\n- Python 3.8+\n- Basic programming knowledge",
                "license": "MIT",
                "has_wiki": True,
                "has_pages": False,
            }
        ]
        return mock_repos[:limit]
