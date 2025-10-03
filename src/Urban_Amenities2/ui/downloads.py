"""Typed helpers for generating Dash download payloads."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import cast

from .contracts import DownloadPayload


def build_file_download(
    path: Path,
    *,
    filename: str | None = None,
    mimetype: str | None = None,
) -> DownloadPayload:
    """Return a Dash-compatible download payload for the given file."""

    payload: DownloadPayload = cast(
        DownloadPayload,
        {
            "content": base64.b64encode(path.read_bytes()).decode("ascii"),
            "filename": filename or path.name,
            "type": mimetype,
            "base64": True,
        },
    )
    return payload


__all__ = ["build_file_download"]
