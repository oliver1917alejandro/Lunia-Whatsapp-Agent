"""
http_client.py: Reusable async HTTP client using aiohttp
"""
import aiohttp
import asyncio
from typing import Any, Dict, Optional
from src.core.config import Config
from src.core.logger import logger


class AsyncHttpClient:
    """Singleton async HTTP client for making requests with shared session."""
    _session: Optional[aiohttp.ClientSession] = None

    @classmethod
    def _get_session(cls) -> aiohttp.ClientSession:
        if cls._session is None or cls._session.closed:
            timeout = aiohttp.ClientTimeout(total=getattr(Config, 'HTTP_TIMEOUT', 30))
            cls._session = aiohttp.ClientSession(timeout=timeout)
        return cls._session

    @classmethod
    async def request(
        cls,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json: Any = None,
        data: Any = None,
        timeout: Optional[float] = None
    ) -> aiohttp.ClientResponse:
        """
        Perform an HTTP request using the shared session.

        Raises:
            aiohttp.ClientError on network failures
        """
        session = cls._get_session()
        try:
            resp = await session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json,
                data=data,
                timeout=timeout
            )
            return resp
        except Exception as e:
            logger.error(f"HTTP {method} request to {url} failed: {e}")
            raise

    @classmethod
    async def close(cls) -> None:
        """Close the shared HTTP session."""
        if cls._session and not cls._session.closed:
            await cls._session.close()
            cls._session = None
