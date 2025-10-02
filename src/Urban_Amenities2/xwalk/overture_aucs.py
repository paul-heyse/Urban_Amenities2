from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from ruamel.yaml import YAML


@dataclass(frozen=True)
class CategoryMatch:
    """Resolved AUCS category for an Overture place."""

    aucstype: str
    group: str
    rule_name: str
    notes: Optional[str]


@dataclass
class _Rule:
    include: List[Tuple[str, ...]]
    exclude: List[Tuple[str, ...]]
    notes: Optional[str]
    group: str
    rule_name: str

    def matches(self, category_path: Sequence[str]) -> bool:
        """Return True when the supplied category matches the rule."""

        path_tuple = tuple(category_path)
        if not any(_prefix_matches(path_tuple, inc) for inc in self.include):
            return False
        if any(_prefix_matches(path_tuple, exc) for exc in self.exclude):
            return False
        return True

    def to_match(self) -> CategoryMatch:
        return CategoryMatch(
            aucstype=self.rule_name,
            group=self.group,
            rule_name=self.rule_name,
            notes=self.notes,
        )


class CategoryMatcher:
    """Category mapper that applies prefix-based rules."""

    def __init__(self, rules: Iterable[_Rule]):
        self._rules: Dict[str, _Rule] = {rule.rule_name: rule for rule in rules}

    def categories(self) -> List[str]:
        return sorted(self._rules.keys())

    def match_single(self, category: str) -> Optional[CategoryMatch]:
        path = _normalise_category(category)
        if not path:
            return None
        for rule in self._rules.values():
            if rule.matches(path):
                return rule.to_match()
        return None

    def match_many(self, categories: Sequence[str]) -> Optional[CategoryMatch]:
        for category in categories:
            match = self.match_single(category)
            if match:
                return match
        return None

    def assign(
        self,
        frame,
        primary_column: str = "primary_category",
        alternate_column: str = "categories",
        output_column: str = "aucstype",
    ):
        import pandas as pd

        if not isinstance(frame, pd.DataFrame):
            raise TypeError("CategoryMatcher.assign expects a pandas DataFrame")
        frame = frame.copy()

        def _resolve(row: pd.Series) -> Tuple[Optional[str], Optional[str], Optional[str]]:
            categories: List[str] = []
            primary = row.get(primary_column)
            if isinstance(primary, str):
                categories.append(primary)
            alternates = row.get(alternate_column)
            if isinstance(alternates, str):
                categories.append(alternates)
            elif isinstance(alternates, Iterable):
                categories.extend([cat for cat in alternates if isinstance(cat, str)])
            match = self.match_many(categories)
            if not match:
                return None, None, None
            return match.aucstype, match.group, match.notes

        matches = frame.apply(_resolve, axis=1)
        result = pd.DataFrame(matches.tolist(), columns=[output_column, f"{output_column}_group", f"{output_column}_notes"])
        for column in result.columns:
            frame[column] = result[column]
        return frame


def load_crosswalk(path: Path | str = Path("docs/AUCS place category crosswalk")) -> CategoryMatcher:
    """Load the AUCS crosswalk YAML from the provided documentation file."""

    path = Path(path)
    text = path.read_text(encoding="utf-8")
    yaml_block = _extract_yaml_block(text)
    if not yaml_block:
        msg = f"No YAML crosswalk block found in {path}"
        raise ValueError(msg)
    yaml = YAML(typ="safe")
    data = yaml.load(yaml_block)
    aucs = data.get("aucscrosswalk") if isinstance(data, dict) else None
    if not isinstance(aucs, dict):
        msg = "Crosswalk YAML missing 'aucscrosswalk' root"
        raise ValueError(msg)

    rules: List[_Rule] = []
    for group, group_rules in aucs.items():
        if not isinstance(group_rules, dict):
            continue
        for rule_name, rule_def in group_rules.items():
            include = [item.get("prefix", []) for item in rule_def.get("include", [])]
            include = [_normalise_category(".".join(prefix)) for prefix in include]
            exclude = [item.get("prefix", []) for item in rule_def.get("exclude", [])]
            exclude = [_normalise_category(".".join(prefix)) for prefix in exclude]
            include = [tpl for tpl in include if tpl]
            notes = rule_def.get("notes")
            rules.append(
                _Rule(
                    include=include or [_normalise_category(rule_name)],
                    exclude=exclude,
                    notes=notes,
                    group=group,
                    rule_name=rule_name,
                )
            )
    return CategoryMatcher(rules)


def _extract_yaml_block(text: str) -> Optional[str]:
    start = text.find("```yaml")
    if start == -1:
        return None
    start += len("```yaml")
    end = text.find("```", start)
    if end == -1:
        return None
    return text[start:end].strip()


def _normalise_category(category: str) -> Tuple[str, ...]:
    if not category:
        return ()
    cleaned = category.replace("|", " ")
    parts = [part.strip().lower().replace(" ", "_") for part in cleaned.replace(">", ".").split(".")]
    return tuple(part for part in parts if part)


def _prefix_matches(path: Tuple[str, ...], prefix: Tuple[str, ...]) -> bool:
    if not prefix:
        return False
    if len(prefix) > len(path):
        return False
    return path[: len(prefix)] == prefix


__all__ = ["CategoryMatcher", "CategoryMatch", "load_crosswalk"]
