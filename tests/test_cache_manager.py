"""Cache manager behaviour and error handling tests."""

from __future__ import annotations

import json
from typing import Any

import pytest

from Urban_Amenities2.cache.manager import CacheManager


def test_cache_roundtrip(cache_manager: CacheManager) -> None:
    value = {"value": 42}
    assert cache_manager.get("wikipedia", "page", "42") is None

    stored = cache_manager.set("wikipedia", "page", "42", value)
    assert stored is True

    retrieved = cache_manager.get("wikipedia", "page", "42")
    assert retrieved == value

    stats = cache_manager.get_stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 1  # initial miss
    assert stats["sets"] == 1
    assert stats["hit_rate"] > 0


def test_cache_key_hashing(cache_manager: CacheManager) -> None:
    long_key = "x" * 120
    hashed = cache_manager._make_key("wikidata", "entity", long_key)
    assert len(hashed.split(":")) == 3
    assert long_key not in hashed


def test_cache_ttl_selection(cache_manager: CacheManager, monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_set(key: str, value: bytes, expire: int | None = None) -> bool:
        captured["key"] = key
        captured["expire"] = expire
        return True

    monkeypatch.setattr(cache_manager.cache, "set", fake_set)

    cache_manager.set("wikipedia", "page", "1", {"title": "Test"})
    assert captured["expire"] == cache_manager.config.ttl_wikipedia

    cache_manager.set("otp", "trip", "2", {"legs": []})
    assert captured["expire"] == cache_manager.config.ttl_routing


def test_cache_invalidate_and_clear(cache_manager: CacheManager) -> None:
    payloads = [
        ("wikipedia", "page", "1", {"title": "A"}),
        ("wikipedia", "page", "2", {"title": "B"}),
        ("wikidata", "entity", "Q1", {"labels": {"en": "Item"}}),
    ]
    cache_manager.warm_cache(payloads)
    assert cache_manager.invalidate("wikipedia", entity_type="page") == 2
    assert cache_manager.get("wikipedia", "page", "1") is None

    cache_manager.clear()
    assert cache_manager.get("wikidata", "entity", "Q1") is None


def test_cache_get_error_returns_default(
    cache_manager: CacheManager, monkeypatch: pytest.MonkeyPatch
) -> None:
    def faulty_get(key: str) -> bytes:
        raise RuntimeError("boom")

    monkeypatch.setattr(cache_manager.cache, "get", faulty_get)
    assert cache_manager.get("wikidata", "entity", "broken", default={}) == {}


def test_cache_serialisation_errors(
    cache_manager: CacheManager, monkeypatch: pytest.MonkeyPatch
) -> None:
    def bad_dumps(value: Any) -> str:
        raise TypeError("no serialise")

    monkeypatch.setattr(json, "dumps", bad_dumps)
    assert cache_manager.set("wikidata", "entity", "broken", {"a": 1}) is False
