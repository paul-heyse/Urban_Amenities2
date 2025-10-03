from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Agency:
    name: str
    state: str
    modes: list[str]
    static_url: str | None
    realtime_urls: list[str]
    license: str | None
    notes: str

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "state": self.state,
            "modes": self.modes,
            "static_url": self.static_url,
            "realtime_urls": self.realtime_urls,
            "license": self.license,
            "notes": self.notes,
        }


STATE_HEADERS = {
    "Colorado": "CO",
    "Utah": "UT",
    "Idaho": "ID",
    "Intercity rail (multi‑state relevance)": "Multi",
}


def load_registry(path: Path | str = Path("docs/AUCS place category crosswalk")) -> list[Agency]:
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    footnotes = _parse_footnotes(text)
    agencies: list[Agency] = []
    state = None
    for line in text.splitlines():
        header_match = re.match(r"^### (.+)$", line.strip())
        if header_match:
            state_label = header_match.group(1).strip()
            state = STATE_HEADERS.get(state_label)
            continue
        bullet_match = re.match(r"^\* \*\*(.+?)\*\* — Modes: \*\*(.+?)\*\*\.(.*)$", line.strip())
        if bullet_match and state:
            name = bullet_match.group(1).strip()
            modes = [mode.strip() for mode in bullet_match.group(2).split(",")]
            remainder = bullet_match.group(3)
            static_url, rt_urls = _extract_urls(remainder, footnotes)
            license_text = _extract_license(remainder)
            notes = remainder.strip()
            agencies.append(
                Agency(
                    name=name,
                    state=state,
                    modes=modes,
                    static_url=static_url,
                    realtime_urls=rt_urls,
                    license=license_text,
                    notes=notes,
                )
            )
    return agencies


def _extract_urls(text: str, footnotes: dict[str, str]) -> tuple[str | None, list[str]]:
    references = re.findall(r"\[(\d+)\]", text)
    urls = [footnotes.get(ref) for ref in references if ref in footnotes]
    static_url = urls[0] if urls else None
    return static_url, urls[1:]


def _extract_license(text: str) -> str | None:
    if "open license" in text.lower():
        return "open"
    if "license" in text.lower():
        return "restricted"
    return None


def _parse_footnotes(text: str) -> dict[str, str]:
    footnotes: dict[str, str] = {}
    pattern = re.compile(r"^\[(\d+)\]:\s*(\S+)", re.MULTILINE)
    for match in pattern.finditer(text):
        footnotes[match.group(1)] = match.group(2)
    return footnotes


def filter_by_state(registry: Iterable[Agency], state: str) -> list[Agency]:
    state = state.upper()
    return [agency for agency in registry if agency.state == state or agency.state == "Multi"]


__all__ = ["Agency", "load_registry", "filter_by_state"]
