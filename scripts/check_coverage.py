"""Utilities for enforcing coverage thresholds in CI."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


@dataclass(frozen=True)
class CoverageSummary:
    line_rate: float
    branch_rate: float
    lines_valid: int
    lines_covered: int
    branches_valid: int
    branches_covered: int

    @property
    def line_percent(self) -> float:
        return self.line_rate * 100.0

    @property
    def branch_percent(self) -> float:
        return self.branch_rate * 100.0

    def to_dict(self) -> dict[str, float | int]:
        return {
            "line_percent": round(self.line_percent, 2),
            "branch_percent": round(self.branch_percent, 2),
            "lines_valid": self.lines_valid,
            "lines_covered": self.lines_covered,
            "branches_valid": self.branches_valid,
            "branches_covered": self.branches_covered,
        }


def parse_coverage(xml_path: Path) -> CoverageSummary:
    if not xml_path.exists():
        raise FileNotFoundError(f"Coverage XML not found: {xml_path}")
    tree = ET.parse(xml_path)
    root = tree.getroot()
    try:
        line_rate = float(root.attrib.get("line-rate", 0.0))
        branch_rate = float(root.attrib.get("branch-rate", 0.0))
        lines_valid = int(root.attrib.get("lines-valid", 0))
        lines_covered = int(root.attrib.get("lines-covered", 0))
        branches_valid = int(root.attrib.get("branches-valid", 0))
        branches_covered = int(root.attrib.get("branches-covered", 0))
    except ValueError as exc:  # pragma: no cover - defensive guard
        raise ValueError("Malformed coverage XML attributes") from exc
    return CoverageSummary(
        line_rate=line_rate,
        branch_rate=branch_rate,
        lines_valid=lines_valid,
        lines_covered=lines_covered,
        branches_valid=branches_valid,
        branches_covered=branches_covered,
    )


def write_summary(summary: CoverageSummary, output: Path | None) -> None:
    if output is None:
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(summary.to_dict(), indent=2, sort_keys=True)
    output.write_text(payload + "\n", encoding="utf-8")


def append_job_summary(summary: CoverageSummary) -> None:
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_file:
        return
    lines = [
        "## Test coverage summary",
        f"- Line coverage: {summary.line_percent:.2f}% ({summary.lines_covered}/{summary.lines_valid})",
        f"- Branch coverage: {summary.branch_percent:.2f}% ({summary.branches_covered}/{summary.branches_valid})",
    ]
    with Path(summary_file).open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def enforce_thresholds(summary: CoverageSummary, line_threshold: float, branch_threshold: float) -> None:
    failures: list[str] = []
    if summary.line_percent + 1e-9 < line_threshold:
        failures.append(
            f"Line coverage {summary.line_percent:.2f}% is below required {line_threshold:.2f}%"
        )
    if summary.branches_valid == 0:
        failures.append("Coverage report is missing branch metrics")
    elif summary.branch_percent + 1e-9 < branch_threshold:
        failures.append(
            f"Branch coverage {summary.branch_percent:.2f}% is below required {branch_threshold:.2f}%"
        )
    if failures:
        message = "\n".join(failures)
        raise SystemExit(message)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate pytest coverage thresholds")
    parser.add_argument("--xml", type=Path, default=Path("coverage.xml"), help="Path to coverage XML report")
    parser.add_argument(
        "--json", type=Path, default=None, help="Optional path to write a machine-readable summary"
    )
    parser.add_argument(
        "--line-threshold",
        type=float,
        default=95.0,
        help="Minimum acceptable line coverage percentage",
    )
    parser.add_argument(
        "--branch-threshold",
        type=float,
        default=90.0,
        help="Minimum acceptable branch coverage percentage",
    )
    args = parser.parse_args(argv)

    summary = parse_coverage(args.xml)
    print(
        f"Line coverage: {summary.line_percent:.2f}% ({summary.lines_covered}/{summary.lines_valid})",
        file=sys.stderr,
    )
    print(
        f"Branch coverage: {summary.branch_percent:.2f}% ({summary.branches_covered}/{summary.branches_valid})",
        file=sys.stderr,
    )
    write_summary(summary, args.json)
    append_job_summary(summary)
    enforce_thresholds(summary, args.line_threshold, args.branch_threshold)
    return 0


if __name__ == "__main__":  # pragma: no cover - entrypoint guard
    raise SystemExit(main())
