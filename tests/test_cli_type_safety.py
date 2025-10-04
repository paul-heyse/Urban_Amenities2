from __future__ import annotations

import pytest

from Urban_Amenities2.cli.main import _ensure_str_mapping


def test_ensure_str_mapping_accepts_string_keys() -> None:
    mapping = {"hex_id": "abc123", "value": 1.0}
    result = _ensure_str_mapping(mapping)
    assert result == mapping


def test_ensure_str_mapping_rejects_non_string_keys() -> None:
    mapping = {1: "value"}
    with pytest.raises(TypeError):
        _ensure_str_mapping(mapping)
