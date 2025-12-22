from .base import BaseCrawler
from .manager import CrawlerManager
from .youtube_crawler import YouTubeCrawler
from .github_crawler import GitHubCrawler
from .arxiv_crawler import ArxivCrawler
from .oer_crawler import OERCrawler, MITOCWCrawler, NPTELCrawler

__all__ = [
    "BaseCrawler",
    "CrawlerManager",
    "YouTubeCrawler",
    "GitHubCrawler",
    "ArxivCrawler",
    "OERCrawler",
    "MITOCWCrawler",
    "NPTELCrawler",
]
