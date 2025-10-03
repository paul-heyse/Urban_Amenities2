"""Health check utilities for routing services and data readiness."""

from __future__ import annotations

import shutil
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, cast

import requests


class _DiskUsage(Protocol):
    free: int


class _VirtualMemory(Protocol):
    available: int


class _PsutilModule(Protocol):
    def disk_usage(self, path: str) -> _DiskUsage: ...

    def virtual_memory(self) -> _VirtualMemory: ...


if TYPE_CHECKING:  # pragma: no cover - typing only
    import psutil as _psutil_type  # type: ignore[import-untyped]

    PSUTIL: _PsutilModule | None = cast(_PsutilModule, _psutil_type)
else:
    try:  # pragma: no cover - optional dependency fallback
        import psutil as _psutil_import  # type: ignore[import-untyped]
    except ModuleNotFoundError:  # pragma: no cover - fallback path
        PSUTIL: _PsutilModule | None = None
    else:
        PSUTIL = cast(_PsutilModule, _psutil_import)

from ..config.loader import ParameterLoadError, load_params

__all__ = [
    "HealthCheckResult",
    "HealthStatus",
    "format_report",
    "overall_status",
    "run_health_checks",
]


class HealthStatus(str, Enum):
    OK = "ok"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass(slots=True)
class HealthCheckResult:
    name: str
    status: HealthStatus
    message: str
    details: dict[str, object] | None = None


_STATUS_ICON = {
    HealthStatus.OK: "✅",
    HealthStatus.WARNING: "⚠️",
    HealthStatus.CRITICAL: "❌",
}


def run_health_checks(
    *,
    osrm_urls: Mapping[str, str | None],
    otp_url: str | None,
    params_path: Path,
    data_paths: Sequence[tuple[Path, int | None]] = (),
    min_disk_gb: float = 100.0,
    min_memory_gb: float = 8.0,
    timeout_seconds: int = 5,
) -> list[HealthCheckResult]:
    """Run configured health checks and return their results."""

    results: list[HealthCheckResult] = []
    results.extend(_check_osrm(osrm_urls, timeout_seconds))
    results.append(_check_otp(otp_url, timeout_seconds))
    results.append(_check_params(params_path))
    results.extend(_check_data_paths(data_paths))
    results.append(_check_disk_space(min_disk_gb))
    results.append(_check_memory(min_memory_gb))
    return results


def _check_osrm(
    osrm_urls: Mapping[str, str | None],
    timeout_seconds: int,
) -> Iterable[HealthCheckResult]:
    results: list[HealthCheckResult] = []
    for mode, url in osrm_urls.items():
        name = f"osrm:{mode}"
        if not url:
            results.append(
                HealthCheckResult(
                    name=name,
                    status=HealthStatus.CRITICAL,
                    message="OSRM URL not configured",
                )
            )
            continue
        try:
            response = requests.get(
                f"{url.rstrip('/')}/health",
                timeout=timeout_seconds,
            )
        except requests.RequestException as exc:
            results.append(
                HealthCheckResult(
                    name=name,
                    status=HealthStatus.CRITICAL,
                    message="OSRM health check failed",
                    details={"error": str(exc)},
                )
            )
            continue
        if response.status_code >= 500:
            results.append(
                HealthCheckResult(
                    name=name,
                    status=HealthStatus.CRITICAL,
                    message=f"OSRM unhealthy ({response.status_code})",
                )
            )
        elif response.status_code >= 400:
            results.append(
                HealthCheckResult(
                    name=name,
                    status=HealthStatus.WARNING,
                    message=f"OSRM health endpoint returned {response.status_code}",
                )
            )
        else:
            results.append(
                HealthCheckResult(
                    name=name,
                    status=HealthStatus.OK,
                    message="OSRM reachable",
                )
            )
    return results


def _check_otp(otp_url: str | None, timeout_seconds: int) -> HealthCheckResult:
    if not otp_url:
        return HealthCheckResult(
            name="otp", status=HealthStatus.CRITICAL, message="OTP URL not configured"
        )
    payload = {"query": "{__typename}"}
    try:
        response = requests.post(otp_url, json=payload, timeout=timeout_seconds)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        return HealthCheckResult(
            name="otp",
            status=HealthStatus.CRITICAL,
            message="OTP health check failed",
            details={"error": str(exc)},
        )
    except ValueError as exc:
        return HealthCheckResult(
            name="otp",
            status=HealthStatus.WARNING,
            message="OTP health response not JSON",
            details={"error": str(exc)},
        )
    if "errors" in data:
        return HealthCheckResult(
            name="otp",
            status=HealthStatus.WARNING,
            message="OTP returned GraphQL errors",
            details={"errors": data.get("errors")},
        )
    return HealthCheckResult(name="otp", status=HealthStatus.OK, message="OTP reachable")


def _check_params(path: Path) -> HealthCheckResult:
    try:
        params, param_hash = load_params(path)
    except ParameterLoadError as exc:
        return HealthCheckResult(
            name="params",
            status=HealthStatus.CRITICAL,
            message="Parameter validation failed",
            details={"error": str(exc)},
        )
    return HealthCheckResult(
        name="params",
        status=HealthStatus.OK,
        message="Parameters validated",
        details={"hash": param_hash, "time_slices": list(params.iter_time_slice_ids())},
    )


def _check_data_paths(data_paths: Sequence[tuple[Path, int | None]]) -> Iterable[HealthCheckResult]:
    results: list[HealthCheckResult] = []
    for path, max_age in data_paths:
        name = f"data:{path.name}"
        if not path.exists():
            results.append(
                HealthCheckResult(
                    name=name,
                    status=HealthStatus.CRITICAL,
                    message="Required data file missing",
                )
            )
            continue
        if max_age is None:
            results.append(
                HealthCheckResult(name=name, status=HealthStatus.OK, message="File present")
            )
            continue
        modified = datetime.fromtimestamp(path.stat().st_mtime)
        age_days = (datetime.utcnow() - modified).days
        if age_days > max_age:
            results.append(
                HealthCheckResult(
                    name=name,
                    status=HealthStatus.WARNING,
                    message="Data is stale",
                    details={"age_days": age_days, "max_age_days": max_age},
                )
            )
        else:
            results.append(
                HealthCheckResult(
                    name=name,
                    status=HealthStatus.OK,
                    message="Data fresh",
                    details={"age_days": age_days},
                )
            )
    return results


def _check_disk_space(min_gb: float) -> HealthCheckResult:
    anchor = Path.cwd().anchor or str(Path.cwd())
    if PSUTIL is not None:
        usage_free = PSUTIL.disk_usage(anchor).free
    else:  # pragma: no cover - fallback path
        usage_free = shutil.disk_usage(anchor).free
    free_gb = usage_free / 1024**3
    if free_gb < min_gb:
        return HealthCheckResult(
            name="disk",
            status=HealthStatus.CRITICAL,
            message="Insufficient disk space",
            details={"free_gb": round(free_gb, 2), "required_gb": min_gb},
        )
    return HealthCheckResult(
        name="disk",
        status=HealthStatus.OK,
        message="Disk space sufficient",
        details={"free_gb": round(free_gb, 2)},
    )


def _check_memory(min_gb: float) -> HealthCheckResult:
    if PSUTIL is None:  # pragma: no cover - fallback path
        return HealthCheckResult(
            name="memory",
            status=HealthStatus.WARNING,
            message="psutil not installed; memory availability unknown",
        )
    virtual = PSUTIL.virtual_memory()
    available_gb = virtual.available / 1024**3
    if available_gb < min_gb:
        return HealthCheckResult(
            name="memory",
            status=HealthStatus.CRITICAL,
            message="Insufficient memory available",
            details={"available_gb": round(available_gb, 2), "required_gb": min_gb},
        )
    return HealthCheckResult(
        name="memory",
        status=HealthStatus.OK,
        message="Memory available",
        details={"available_gb": round(available_gb, 2)},
    )


def format_report(results: Sequence[HealthCheckResult]) -> str:
    lines = []
    for result in results:
        icon = _STATUS_ICON.get(result.status, "-")
        line = f"{icon} {result.name}: {result.message}"
        lines.append(line)
        if result.details:
            for key, value in result.details.items():
                lines.append(f"    • {key}: {value}")
    return "\n".join(lines)


def overall_status(results: Sequence[HealthCheckResult]) -> HealthStatus:
    if any(result.status == HealthStatus.CRITICAL for result in results):
        return HealthStatus.CRITICAL
    if any(result.status == HealthStatus.WARNING for result in results):
        return HealthStatus.WARNING
    return HealthStatus.OK
