"""Tests for cache manager."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from Urban_Amenities2.cache import CacheConfig, CacheManager


@pytest.fixture
def temp_cache_dir():
    """Create temporary cache directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def cache_manager(temp_cache_dir):
    """Create cache manager with temporary directory."""
    config = CacheConfig(cache_dir=temp_cache_dir, size_limit=10 * 1024**2)  # 10 MB
    return CacheManager(config)


def test_cache_set_and_get(cache_manager):
    """Test setting and getting cached values."""
    source = "wikipedia"
    entity_type = "pageviews"
    entity_id = "Q123456"
    value = {"views": 1000, "date": "2025-01-01"}

    # Set value
    success = cache_manager.set(source, entity_type, entity_id, value)
    assert success

    # Get value
    retrieved = cache_manager.get(source, entity_type, entity_id)
    assert retrieved == value


def test_cache_miss_returns_default(cache_manager):
    """Test that cache miss returns default value."""
    result = cache_manager.get("wikipedia", "pageviews", "nonexistent", default=None)
    assert result is None

    result = cache_manager.get("wikipedia", "pageviews", "nonexistent", default={"views": 0})
    assert result == {"views": 0}


def test_cache_invalidate(cache_manager):
    """Test cache invalidation."""
    # Set multiple values
    cache_manager.set("wikipedia", "pageviews", "Q1", {"views": 100})
    cache_manager.set("wikipedia", "pageviews", "Q2", {"views": 200})
    cache_manager.set("wikidata", "entity", "Q3", {"label": "Test"})

    # Invalidate wikipedia cache
    count = cache_manager.invalidate("wikipedia")
    assert count == 2

    # Verify wikipedia cache is cleared
    assert cache_manager.get("wikipedia", "pageviews", "Q1") is None
    assert cache_manager.get("wikipedia", "pageviews", "Q2") is None

    # Verify wikidata cache still exists
    assert cache_manager.get("wikidata", "entity", "Q3") == {"label": "Test"}


def test_cache_stats(cache_manager):
    """Test cache statistics tracking."""
    # Initial stats
    stats = cache_manager.get_stats()
    assert stats["hits"] == 0
    assert stats["misses"] == 0
    assert stats["sets"] == 0

    # Set and get values
    cache_manager.set("wikipedia", "pageviews", "Q1", {"views": 100})
    cache_manager.get("wikipedia", "pageviews", "Q1")  # Hit
    cache_manager.get("wikipedia", "pageviews", "Q2")  # Miss

    # Check updated stats
    stats = cache_manager.get_stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert stats["sets"] == 1
    assert stats["hit_rate"] == 50.0  # 1 hit / (1 hit + 1 miss) * 100


def test_cache_ttl(cache_manager):
    """Test TTL (time-to-live) for cached values."""
    # Set value with short TTL
    cache_manager.set("test", "entity", "temp", {"data": "value"}, ttl=1)

    # Immediately retrieve (should exist)
    assert cache_manager.get("test", "entity", "temp") == {"data": "value"}

    # Wait for expiration
    import time

    time.sleep(2)

    # Should be expired
    assert cache_manager.get("test", "entity", "temp") is None


def test_cache_compression(temp_cache_dir):
    """Test cache compression."""
    # Create cache with compression
    config_compressed = CacheConfig(cache_dir=temp_cache_dir / "compressed", compression=True)
    cache_compressed = CacheManager(config_compressed)

    # Create cache without compression
    config_uncompressed = CacheConfig(cache_dir=temp_cache_dir / "uncompressed", compression=False)
    cache_uncompressed = CacheManager(config_uncompressed)

    # Store same large data in both
    large_data = {"data": "x" * 10000}  # 10KB of data

    cache_compressed.set("test", "data", "large", large_data)
    cache_uncompressed.set("test", "data", "large", large_data)

    # Verify both can retrieve correctly
    assert cache_compressed.get("test", "data", "large") == large_data
    assert cache_uncompressed.get("test", "data", "large") == large_data

    # Compressed should use less disk space
    compressed_size = cache_compressed.cache.volume()
    uncompressed_size = cache_uncompressed.cache.volume()
    assert compressed_size < uncompressed_size


def test_cache_warm(cache_manager):
    """Test cache warming."""
    entries = [
        ("wikipedia", "pageviews", "Q1", {"views": 100}),
        ("wikipedia", "pageviews", "Q2", {"views": 200}),
        ("wikidata", "entity", "Q3", {"label": "Test"}),
    ]

    count = cache_manager.warm_cache(entries)
    assert count == 3

    # Verify all entries are cached
    assert cache_manager.get("wikipedia", "pageviews", "Q1") == {"views": 100}
    assert cache_manager.get("wikipedia", "pageviews", "Q2") == {"views": 200}
    assert cache_manager.get("wikidata", "entity", "Q3") == {"label": "Test"}


def test_cache_clear(cache_manager):
    """Test clearing entire cache."""
    # Add some data
    cache_manager.set("wikipedia", "pageviews", "Q1", {"views": 100})
    cache_manager.set("wikidata", "entity", "Q2", {"label": "Test"})

    # Clear cache
    cache_manager.clear()

    # Verify cache is empty (diskcache may not report 0 immediately after clear)
    assert cache_manager.get("wikipedia", "pageviews", "Q1") is None
    assert cache_manager.get("wikidata", "entity", "Q2") is None
    # DiskCache clear() removes data but disk space may persist
    assert len(list(cache_manager.cache.iterkeys())) == 0
