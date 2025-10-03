"""Utilities for enforcing coverage thresholds in CI."""

from __future__ import annotations

import argparse
import configparser
import json
import os
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


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


def write_summary(
    summary: CoverageSummary,
    output: Path | None,
    package_rates: dict[str, float] | None = None,
) -> None:
    if output is None:
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    payload_dict: dict[str, float | int | dict[str, float]] = summary.to_dict()
    if package_rates:
        payload_dict["packages"] = {k: round(v, 2) for k, v in package_rates.items()}
    payload = json.dumps(payload_dict, indent=2, sort_keys=True)
    output.write_text(payload + "\n", encoding="utf-8")


def append_job_summary(summary: CoverageSummary, package_rates: dict[str, float]) -> None:
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_file:
        return
    lines = [
        "## Test coverage summary",
        f"- Line coverage: {summary.line_percent:.2f}% ({summary.lines_covered}/{summary.lines_valid})",
        f"- Branch coverage: {summary.branch_percent:.2f}% ({summary.branches_covered}/{summary.branches_valid})",
    ]
    if package_rates:
        lines.append("- Package coverage:")
        for package, rate in sorted(package_rates.items()):
            lines.append(f"  - {package}: {rate:.2f}%")
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
        raise SystemExit("\n".join(failures))


def collect_package_rates(xml_root: ET.Element, packages: dict[str, float]) -> dict[str, float]:
    results: dict[str, float] = {}
    for package in packages:
        total = 0
        covered = 0
        candidates = {package}
        if "." in package:
            candidates.add(package.split(".", 1)[1])
        package_names: set[str] = set()
        for pkg in xml_root.findall(".//package"):
            name = pkg.get("name", "")
            for candidate in candidates:
                if name == candidate or name.startswith(f"{candidate}."):
                    package_names.add(name)
                    break
        processed: set[str] = set()
        queue = list(package_names)
        while queue:
            pkg_name = queue.pop()
            if pkg_name in processed:
                continue
            processed.add(pkg_name)
            for cls in xml_root.findall(f".//package[@name='{pkg_name}']/classes/class"):
                for line in cls.findall("lines/line"):
                    total += 1
                    hits = line.get("hits", "0")
                    try:
                        if int(hits) > 0:
                            covered += 1
                    except ValueError:
                        continue
            prefix = f"{pkg_name}."
            for nested in xml_root.findall(".//package"):
                nested_name = nested.get("name", "")
                if nested_name.startswith(prefix) and nested_name not in processed:
                    queue.append(nested_name)
        if total == 0:
            results[package] = 0.0
        else:
            results[package] = (covered / total) * 100.0
    return results


def enforce_package_thresholds(
    package_rates: dict[str, float],
    package_thresholds: dict[str, float],
) -> None:
    failures: list[str] = []
    for package, required in package_thresholds.items():
        observed = package_rates.get(package, 0.0)
        if observed + 1e-9 < required:
            failures.append(
                f"{package} coverage {observed:.2f}% is below required {required:.2f}%"
            )
    if failures:
        raise SystemExit("\n".join(failures))


def load_thresholds(config_path: Path | None) -> tuple[float | None, dict[str, float]]:
    if config_path is None:
        return None, {}
    parser = configparser.ConfigParser()
    parser.optionxform = str
    if not config_path.exists():
        return None, {}
    parser.read(config_path, encoding="utf-8")
    if not parser.has_section("thresholds"):
        return None, {}
    overall = None
    packages: dict[str, float] = {}
    for key, value in parser.items("thresholds"):
        try:
            numeric = float(value)
        except ValueError:
            continue
        if key.lower() == "overall":
            overall = numeric
        else:
            packages[key] = numeric
    return overall, packages


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate pytest coverage thresholds")
    parser.add_argument("--xml", type=Path, default=Path("coverage.xml"), help="Path to coverage XML report")
    parser.add_argument(
        "--json", type=Path, default=None, help="Optional path to write a machine-readable summary"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(".coveragerc"),
        help="Path to coverage configuration file with threshold metadata",
    )
    parser.add_argument(
        "--line-threshold",
        type=float,
        default=None,
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
    overall_threshold, package_thresholds = load_thresholds(args.config)
    line_threshold = args.line_threshold if args.line_threshold is not None else overall_threshold
    if line_threshold is None:
        line_threshold = 95.0
    print(
        f"Line coverage: {summary.line_percent:.2f}% ({summary.lines_covered}/{summary.lines_valid})",
        file=sys.stderr,
    )
    print(
        f"Branch coverage: {summary.branch_percent:.2f}% ({summary.branches_covered}/{summary.branches_valid})",
        file=sys.stderr,
    )
    package_rates: dict[str, float] = {}
    if package_thresholds:
        xml_root = ET.parse(args.xml).getroot()
        package_rates = collect_package_rates(xml_root, package_thresholds)
        for package, rate in sorted(package_rates.items()):
            print(f"{package}: {rate:.2f}%", file=sys.stderr)

    write_summary(summary, args.json, package_rates)
    append_job_summary(summary, package_rates)
    enforce_thresholds(summary, float(line_threshold), args.branch_threshold)
    if package_thresholds:
        enforce_package_thresholds(package_rates, package_thresholds)
    return 0


if __name__ == "__main__":  # pragma: no cover - entrypoint guard
    raise SystemExit(main())
