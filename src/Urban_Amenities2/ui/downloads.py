"""Typed helpers for generating Dash download payloads."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import cast

from dash import dcc

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


def send_file(
    path: Path,
    *,
    filename: str | None = None,
    content_type: str | None = None,
) -> DownloadPayload:
    """Compatibility wrapper returning Dash download payloads."""

    return cast(
        DownloadPayload,
        dcc.send_file(str(path), filename=filename, type=content_type),
    )


__all__ = ["build_file_download", "send_file"]
