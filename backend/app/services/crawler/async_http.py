"""
Async HTTP Client for Crawlers
Provides non-blocking HTTP requests using aiohttp
"""
import asyncio
import logging
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager
import aiohttp
from aiohttp import ClientTimeout, ClientError

logger = logging.getLogger(__name__)


class AsyncHTTPClient:
    """
    Async HTTP client wrapper for crawler operations.
    Supports connection pooling and automatic retries.
    """
    
    DEFAULT_TIMEOUT = ClientTimeout(total=30, connect=10)
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0  # seconds
    
    def __init__(
        self,
        timeout: Optional[ClientTimeout] = None,
        max_retries: int = MAX_RETRIES,
        headers: Optional[Dict[str, str]] = None
    ):
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self.max_retries = max_retries
        self.default_headers = headers or {
            "User-Agent": "LMS-Crawler/1.0 (Educational Content Aggregator)"
        }
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create the aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=self.timeout,
                headers=self.default_headers
            )
        return self._session
    
    async def close(self):
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
    
    async def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retry: bool = True
    ) -> Dict[str, Any]:
        """
        Perform async GET request.
        
        Args:
            url: Request URL
            params: Query parameters
            headers: Additional headers
            retry: Whether to retry on failure
            
        Returns:
            JSON response as dict
        """
        session = await self._get_session()
        last_error = None
        
        for attempt in range(self.max_retries if retry else 1):
            try:
                async with session.get(url, params=params, headers=headers) as response:
                    response.raise_for_status()
                    return await response.json()
                    
            except aiohttp.ClientResponseError as e:
                last_error = e
                if e.status == 429:  # Rate limited
                    wait_time = self.RETRY_DELAY * (2 ** attempt)
                    logger.warning(f"Rate limited, waiting {wait_time}s...")
                    await asyncio.sleep(wait_time)
                elif e.status >= 500:  # Server error
                    await asyncio.sleep(self.RETRY_DELAY)
                else:
                    raise
                    
            except (ClientError, asyncio.TimeoutError) as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.RETRY_DELAY)
                    
        raise last_error or Exception("Request failed after retries")
    
    async def get_text(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Perform async GET request and return text response.
        """
        session = await self._get_session()
        
        async with session.get(url, params=params, headers=headers) as response:
            response.raise_for_status()
            return await response.text()
    
    async def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Perform async POST request.
        """
        session = await self._get_session()
        
        async with session.post(url, data=data, json=json, headers=headers) as response:
            response.raise_for_status()
            return await response.json()
    
    async def fetch_many(
        self,
        urls: List[str],
        params_list: Optional[List[Dict[str, Any]]] = None,
        concurrency: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Fetch multiple URLs concurrently with rate limiting.
        
        Args:
            urls: List of URLs to fetch
            params_list: Optional list of params for each URL
            concurrency: Maximum concurrent requests
            
        Returns:
            List of responses (or None for failed requests)
        """
        semaphore = asyncio.Semaphore(concurrency)
        params_list = params_list or [None] * len(urls)
        
        async def fetch_one(url: str, params: Optional[Dict]) -> Optional[Dict]:
            async with semaphore:
                try:
                    return await self.get(url, params=params)
                except Exception as e:
                    logger.warning(f"Failed to fetch {url}: {e}")
                    return None
        
        tasks = [
            fetch_one(url, params)
            for url, params in zip(urls, params_list)
        ]
        
        return await asyncio.gather(*tasks)


# Singleton instance
_client: Optional[AsyncHTTPClient] = None


def get_async_http_client() -> AsyncHTTPClient:
    """Get the singleton async HTTP client."""
    global _client
    if _client is None:
        _client = AsyncHTTPClient()
    return _client


@asynccontextmanager
async def async_http_session():
    """
    Context manager for async HTTP operations.
    Ensures proper cleanup of the session.
    
    Usage:
        async with async_http_session() as client:
            data = await client.get(url)
    """
    client = AsyncHTTPClient()
    try:
        yield client
    finally:
        await client.close()
