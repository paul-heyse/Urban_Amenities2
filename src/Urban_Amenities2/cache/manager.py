"""Cache manager for API responses and routing results."""

from __future__ import annotations

import gzip
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import diskcache
import structlog

logger = structlog.get_logger()


@dataclass
class CacheConfig:
    """Configuration for cache manager."""

    backend: str = "disk"  # 'disk' or 'redis'
    cache_dir: Path = Path(".cache")
    size_limit: int = 50 * 1024**3  # 50 GB
    eviction_policy: str = "least-recently-used"
    compression: bool = True
    default_ttl: int = 86400  # 24 hours in seconds

    # TTL per data source (in seconds)
    ttl_wikipedia: int = 30 * 86400  # 30 days
    ttl_wikidata: int = 30 * 86400  # 30 days
    ttl_noaa: int = 90 * 86400  # 90 days (climate normals are static)
    ttl_faa: int = 365 * 86400  # 1 year (annual data)
    ttl_transitland: int = 7 * 86400  # 7 days
    ttl_routing: int = 30 * 86400  # 30 days
    ttl_overture: int = 90 * 86400  # 90 days (quarterly releases)


class CacheManager:
    """Manage caching for API responses and computed results."""

    def __init__(self, config: CacheConfig | None = None):
        """
        Initialize cache manager.

        Args:
            config: Cache configuration (uses defaults if None)
        """
        self.config = config or CacheConfig()
        self.cache = self._initialize_backend()
        self.stats = {"hits": 0, "misses": 0, "sets": 0, "evictions": 0}

    def _initialize_backend(self) -> diskcache.Cache:
        """Initialize the cache backend."""
        if self.config.backend == "disk":
            self.config.cache_dir.mkdir(parents=True, exist_ok=True)
            return diskcache.Cache(
                str(self.config.cache_dir),
                size_limit=self.config.size_limit,
                eviction_policy=self.config.eviction_policy,
            )
        elif self.config.backend == "redis":
            # Redis backend would go here
            raise NotImplementedError("Redis backend not yet implemented")
        else:
            raise ValueError(f"Unknown cache backend: {self.config.backend}")

    def _make_key(self, source: str, entity_type: str, entity_id: str) -> str:
        """
        Create a cache key.

        Args:
            source: Data source (e.g., 'wikipedia', 'osrm', 'otp')
            entity_type: Entity type (e.g., 'pageviews', 'route', 'table')
            entity_id: Unique identifier for the entity

        Returns:
            Cache key string
        """
        # Hash entity_id if it's very long (e.g., coordinates, complex queries)
        if len(entity_id) > 100:
            entity_id_hash = hashlib.sha256(entity_id.encode()).hexdigest()[:16]
            return f"{source}:{entity_type}:{entity_id_hash}"

        return f"{source}:{entity_type}:{entity_id}"

    def _compress(self, data: bytes) -> bytes:
        """Compress data using gzip."""
        if not self.config.compression:
            return data
        return gzip.compress(data, compresslevel=6)

    def _decompress(self, data: bytes) -> bytes:
        """Decompress gzipped data."""
        if not self.config.compression:
            return data
        return gzip.decompress(data)

    def get(self, source: str, entity_type: str, entity_id: str, default: Any = None) -> Any | None:
        """
        Get a value from the cache.

        Args:
            source: Data source
            entity_type: Entity type
            entity_id: Entity ID
            default: Default value if key not found

        Returns:
            Cached value or default
        """
        key = self._make_key(source, entity_type, entity_id)

        try:
            compressed_data = self.cache.get(key)
            if compressed_data is None:
                self.stats["misses"] += 1
                logger.debug("cache_miss", key=key)
                return default

            self.stats["hits"] += 1
            logger.debug("cache_hit", key=key)

            # Decompress and deserialize
            data_bytes = self._decompress(compressed_data)
            return json.loads(data_bytes.decode("utf-8"))

        except Exception as e:
            logger.error("cache_get_error", key=key, error=str(e))
            return default

    def set(
        self,
        source: str,
        entity_type: str,
        entity_id: str,
        value: Any,
        ttl: int | None = None,
    ) -> bool:
        """
        Set a value in the cache.

        Args:
            source: Data source
            entity_type: Entity type
            entity_id: Entity ID
            value: Value to cache
            ttl: Time-to-live in seconds (uses source-specific TTL if None)

        Returns:
            True if set successfully, False otherwise
        """
        key = self._make_key(source, entity_type, entity_id)

        # Determine TTL
        if ttl is None:
            ttl = self._get_ttl_for_source(source)

        try:
            # Serialize and compress
            data_bytes = json.dumps(value).encode("utf-8")
            compressed_data = self._compress(data_bytes)

            # Set with expiration
            self.cache.set(key, compressed_data, expire=ttl)
            self.stats["sets"] += 1
            logger.debug("cache_set", key=key, size=len(compressed_data), ttl=ttl)
            return True

        except Exception as e:
            logger.error("cache_set_error", key=key, error=str(e))
            return False

    def _get_ttl_for_source(self, source: str) -> int:
        """Get TTL for a specific data source."""
        ttl_map = {
            "wikipedia": self.config.ttl_wikipedia,
            "wikidata": self.config.ttl_wikidata,
            "noaa": self.config.ttl_noaa,
            "faa": self.config.ttl_faa,
            "transitland": self.config.ttl_transitland,
            "osrm": self.config.ttl_routing,
            "otp": self.config.ttl_routing,
            "overture": self.config.ttl_overture,
        }
        return ttl_map.get(source, self.config.default_ttl)

    def invalidate(self, source: str, entity_type: str | None = None) -> int:
        """
        Invalidate cache entries.

        Args:
            source: Data source to invalidate
            entity_type: Optional entity type filter

        Returns:
            Number of keys invalidated
        """
        count = 0

        try:
            for key in list(self.cache.iterkeys()):
                if key.startswith(f"{source}:") and (
                    entity_type is None or f":{entity_type}:" in key
                ):
                    self.cache.delete(key)
                    count += 1

            logger.info("cache_invalidated", source=source, entity_type=entity_type, count=count)
            return count

        except Exception as e:
            logger.error("cache_invalidate_error", source=source, error=str(e))
            return count

    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
        logger.info("cache_cleared")

    def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0.0

        return {
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "sets": self.stats["sets"],
            "hit_rate": hit_rate,
            "total_size": self.cache.volume(),
            "entry_count": len(self.cache),
        }

    def warm_cache(self, entries: list[tuple[str, str, str, Any]]) -> int:
        """
        Pre-populate cache with common queries.

        Args:
            entries: List of (source, entity_type, entity_id, value) tuples

        Returns:
            Number of entries warmed
        """
        count = 0
        for source, entity_type, entity_id, value in entries:
            if self.set(source, entity_type, entity_id, value):
                count += 1

        logger.info("cache_warmed", count=count)
        return count
