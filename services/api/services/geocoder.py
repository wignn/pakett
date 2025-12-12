"""
Geocoding Service.
Provides geocoding with caching using Nominatim (OpenStreetMap).
"""

import hashlib
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import asyncio

import httpx
import redis.asyncio as redis
from tenacity import retry, stop_after_attempt, wait_exponential

from config import settings

logger = logging.getLogger(__name__)


@dataclass
class GeocodingResult:
    """Result of geocoding operation."""
    lat: float
    lon: float
    confidence: float
    source: str
    place_id: Optional[str] = None
    display_name: Optional[str] = None
    cached: bool = False
    raw_response: Optional[Dict] = None


class Geocoder:
    """
    Geocoding service with caching and rate limiting.
    
    Supports:
    - Nominatim (OpenStreetMap) - default, free
    - LocationIQ - free tier available
    - OpenCage - free tier available
    """
    
    def __init__(self):
        """Initialize geocoder with Redis cache."""
        self._redis: Optional[redis.Redis] = None
        self._http_client: Optional[httpx.AsyncClient] = None
        self._rate_limit_lock = asyncio.Lock()
        self._last_request_time = 0.0
    
    async def _get_redis(self) -> redis.Redis:
        """Get Redis connection."""
        if self._redis is None:
            self._redis = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
        return self._redis
    
    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=30.0,
                headers={
                    "User-Agent": "PaketRoutingAPI/1.0 (contact@example.com)"
                }
            )
        return self._http_client
    
    async def close(self):
        """Close connections."""
        if self._redis:
            await self._redis.close()
            self._redis = None
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
    
    def _hash_address(self, address: str) -> str:
        """Create hash key for address caching."""
        normalized = address.lower().strip()
        return f"geocode:{hashlib.sha256(normalized.encode()).hexdigest()[:16]}"
    
    async def _get_from_cache(self, address: str) -> Optional[GeocodingResult]:
        """Try to get geocoding result from cache."""
        try:
            redis_client = await self._get_redis()
            cache_key = self._hash_address(address)
            cached = await redis_client.hgetall(cache_key)
            
            if cached:
                logger.debug(f"Cache hit for address: {address[:50]}...")
                # Update hit count and last used
                await redis_client.hincrby(cache_key, "hit_count", 1)
                
                return GeocodingResult(
                    lat=float(cached["lat"]),
                    lon=float(cached["lon"]),
                    confidence=float(cached.get("confidence", 0.8)),
                    source=cached.get("source", "cache"),
                    place_id=cached.get("place_id"),
                    display_name=cached.get("display_name"),
                    cached=True
                )
        except Exception as e:
            logger.warning(f"Cache lookup failed: {e}")
        
        return None
    
    async def _save_to_cache(self, address: str, result: GeocodingResult):
        """Save geocoding result to cache."""
        try:
            redis_client = await self._get_redis()
            cache_key = self._hash_address(address)
            
            await redis_client.hset(cache_key, mapping={
                "lat": str(result.lat),
                "lon": str(result.lon),
                "confidence": str(result.confidence),
                "source": result.source,
                "place_id": result.place_id or "",
                "display_name": result.display_name or "",
                "hit_count": "1",
            })
            
            # Set TTL
            await redis_client.expire(cache_key, settings.cache_ttl_seconds)
            logger.debug(f"Cached geocoding result for: {address[:50]}...")
            
        except Exception as e:
            logger.warning(f"Failed to cache geocoding result: {e}")
    
    async def _rate_limit(self):
        """Enforce rate limiting for external API calls."""
        async with self._rate_limit_lock:
            import time
            now = time.time()
            elapsed = now - self._last_request_time
            min_interval = 1.0 / settings.geocoding_rate_limit
            
            if elapsed < min_interval:
                await asyncio.sleep(min_interval - elapsed)
            
            self._last_request_time = time.time()
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def _geocode_nominatim(self, address: str) -> Optional[GeocodingResult]:
        """Geocode using Nominatim (OpenStreetMap)."""
        await self._rate_limit()
        
        client = await self._get_http_client()
        
        params = {
            "q": address,
            "format": "json",
            "limit": 5,
            "addressdetails": 1,
            "countrycodes": "id",  # Focus on Indonesia
        }
        
        try:
            response = await client.get(
                f"{settings.nominatim_url}/search",
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            if not data:
                logger.warning(f"No results from Nominatim for: {address[:50]}...")
                return None
            
            # Take the first (best) result
            best = data[0]
            
            # Calculate confidence based on importance and type
            importance = float(best.get("importance", 0.5))
            confidence = min(importance * 1.2, 1.0)  # Scale up importance
            
            return GeocodingResult(
                lat=float(best["lat"]),
                lon=float(best["lon"]),
                confidence=confidence,
                source="nominatim",
                place_id=best.get("place_id"),
                display_name=best.get("display_name"),
                raw_response=best
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Nominatim HTTP error: {e}")
            raise
        except Exception as e:
            logger.error(f"Nominatim geocoding failed: {e}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def _geocode_locationiq(self, address: str) -> Optional[GeocodingResult]:
        """Geocode using LocationIQ (requires API key)."""
        if not settings.geocoding_api_key:
            raise ValueError("LocationIQ requires an API key")
        
        await self._rate_limit()
        
        client = await self._get_http_client()
        
        params = {
            "key": settings.geocoding_api_key,
            "q": address,
            "format": "json",
            "limit": 5,
            "countrycodes": "id",
        }
        
        try:
            response = await client.get(
                "https://us1.locationiq.com/v1/search",
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            if not data:
                return None
            
            best = data[0]
            
            return GeocodingResult(
                lat=float(best["lat"]),
                lon=float(best["lon"]),
                confidence=float(best.get("importance", 0.7)),
                source="locationiq",
                place_id=best.get("place_id"),
                display_name=best.get("display_name"),
                raw_response=best
            )
            
        except Exception as e:
            logger.error(f"LocationIQ geocoding failed: {e}")
            raise
    
    async def geocode(
        self,
        address: str,
        use_cache: bool = True
    ) -> Optional[GeocodingResult]:
        """
        Geocode an address to coordinates.
        
        Args:
            address: Address string to geocode
            use_cache: Whether to check cache first
            
        Returns:
            GeocodingResult or None if geocoding failed
        """
        if not address or len(address.strip()) < 5:
            logger.warning("Address too short for geocoding")
            return None
        
        # Check cache first
        if use_cache:
            cached = await self._get_from_cache(address)
            if cached:
                return cached
        
        # Try geocoding providers
        result: Optional[GeocodingResult] = None
        
        provider = settings.geocoding_provider.lower()
        
        try:
            if provider == "nominatim":
                result = await self._geocode_nominatim(address)
            elif provider == "locationiq":
                result = await self._geocode_locationiq(address)
            else:
                # Default to Nominatim
                result = await self._geocode_nominatim(address)
        except Exception as e:
            logger.error(f"All geocoding attempts failed for: {address[:50]}... Error: {e}")
            return None
        
        # Cache successful result
        if result and use_cache:
            await self._save_to_cache(address, result)
        
        return result
    
    async def geocode_batch(
        self,
        addresses: List[str],
        use_cache: bool = True,
        max_concurrent: int = 5
    ) -> Dict[str, Optional[GeocodingResult]]:
        """
        Geocode multiple addresses with concurrency control.
        
        Args:
            addresses: List of addresses to geocode
            use_cache: Whether to use cache
            max_concurrent: Maximum concurrent geocoding requests
            
        Returns:
            Dictionary mapping address to result
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def geocode_with_semaphore(addr: str) -> tuple:
            async with semaphore:
                result = await self.geocode(addr, use_cache=use_cache)
                return (addr, result)
        
        tasks = [geocode_with_semaphore(addr) for addr in addresses]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            addr: result if not isinstance(result, Exception) else None
            for addr, result in results
            if isinstance(result, tuple)
        }


# Singleton instance
_geocoder_instance: Optional[Geocoder] = None


def get_geocoder() -> Geocoder:
    """Get singleton geocoder instance."""
    global _geocoder_instance
    if _geocoder_instance is None:
        _geocoder_instance = Geocoder()
    return _geocoder_instance
