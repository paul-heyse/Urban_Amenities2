"""Hex selection and detail viewing."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from importlib import import_module
from typing import Any, cast

import pandas as pd
import structlog

from .types import AmenityEntry, ModeShareMap

logger = structlog.get_logger()


def _import_h3() -> Any:
    return import_module("h3")


@dataclass(slots=True)
class HexDetails:
    """Detailed information for a selected hex."""

    hex_id: str
    lat: float
    lon: float
    state: str
    metro: str | None
    county: str | None
    population: float | None
    aucs: float
    ea: float
    lca: float
    muhaa: float
    jea: float
    morr: float
    cte: float
    sou: float
    top_amenities: list[AmenityEntry] = field(default_factory=list)
    top_modes: ModeShareMap = field(default_factory=dict)

    @classmethod
    def from_row(cls, row: pd.Series) -> HexDetails:
        """
        Create HexDetails from a DataFrame row.

        Args:
            row: DataFrame row with hex data

        Returns:
            HexDetails instance
        """
        amenities: list[AmenityEntry] = []
        raw_amenities = row.get("top_amenities", [])
        if isinstance(raw_amenities, list):
            for item in raw_amenities:
                if not isinstance(item, dict):
                    continue
                name = str(item.get("name", ""))
                category = str(item.get("category", ""))
                score_raw = item.get("score")
                score = float(score_raw) if isinstance(score_raw, (int, float)) else 0.0
                amenities.append(AmenityEntry(name=name, category=category, score=score))

        modes: ModeShareMap = {}
        raw_modes = row.get("top_modes", {})
        if isinstance(raw_modes, dict):
            for mode, value in raw_modes.items():
                if isinstance(mode, str) and isinstance(value, (int, float)):
                    modes[mode] = float(value)

        def _coerce_float(value: Any, fallback: float = 0.0) -> float:
            return float(value) if isinstance(value, (int, float)) else fallback

        population_raw = row.get("population")

        ea_raw = row.get("ea", row.get("EA", 0.0))
        lca_raw = row.get("lca", row.get("LCA", 0.0))
        muhaa_raw = row.get("muhaa", row.get("MUHAA", 0.0))
        jea_raw = row.get("jea", row.get("JEA", 0.0))
        morr_raw = row.get("morr", row.get("MORR", 0.0))
        cte_raw = row.get("cte", row.get("CTE", 0.0))
        sou_raw = row.get("sou", row.get("SOU", 0.0))

        return cls(
            hex_id=str(row.get("hex_id", "")),
            lat=_coerce_float(row.get("lat", row.get("centroid_lat", 0.0))),
            lon=_coerce_float(row.get("lon", row.get("centroid_lon", 0.0))),
            state=str(row.get("state", "")),
            metro=row.get("metro"),
            county=row.get("county"),
            population=(
                _coerce_float(population_raw, fallback=0.0)
                if isinstance(population_raw, (int, float))
                else None
            ),
            aucs=_coerce_float(row.get("aucs", 0.0)),
            ea=_coerce_float(ea_raw),
            lca=_coerce_float(lca_raw),
            muhaa=_coerce_float(muhaa_raw),
            jea=_coerce_float(jea_raw),
            morr=_coerce_float(morr_raw),
            cte=_coerce_float(cte_raw),
            sou=_coerce_float(sou_raw),
            top_amenities=amenities,
            top_modes=modes,
        )


class HexSelector:
    """Manage hex selection and comparison."""

    def __init__(self, df: pd.DataFrame) -> None:
        """
        Initialize hex selector.

        Args:
            df: DataFrame with hex-level scores
        """
        self.df = df
        self.selected_hexes: list[str] = []
        self.max_selection = 5

    def select_hex(self, hex_id: str) -> bool:
        """
        Select a hex for viewing details.

        Args:
            hex_id: Hex ID to select

        Returns:
            True if selection succeeded, False if limit reached
        """
        if hex_id in self.selected_hexes:
            logger.info("hex_already_selected", hex_id=hex_id)
            return True

        if len(self.selected_hexes) >= self.max_selection:
            logger.warning("max_selection_reached", max=self.max_selection)
            return False

        self.selected_hexes.append(hex_id)
        logger.info("hex_selected", hex_id=hex_id, total=len(self.selected_hexes))
        return True

    def deselect_hex(self, hex_id: str) -> None:
        """
        Deselect a hex.

        Args:
            hex_id: Hex ID to deselect
        """
        if hex_id in self.selected_hexes:
            self.selected_hexes.remove(hex_id)
            logger.info("hex_deselected", hex_id=hex_id)

    def clear_selection(self) -> None:
        """Clear all selected hexes."""
        self.selected_hexes.clear()
        logger.info("selection_cleared")

    def get_details(self, hex_id: str) -> HexDetails | None:
        """
        Get detailed information for a hex.

        Args:
            hex_id: Hex ID to get details for

        Returns:
            HexDetails or None if hex not found
        """
        row = self.df[self.df["hex_id"] == hex_id]
        if row.empty:
            logger.warning("hex_not_found", hex_id=hex_id)
            return None

        return HexDetails.from_row(row.iloc[0])

    def get_comparison_data(self) -> pd.DataFrame:
        """
        Get comparison data for all selected hexes.

        Returns:
            DataFrame with selected hexes and their scores
        """
        if not self.selected_hexes:
            return pd.DataFrame()

        return self.df[self.df["hex_id"].isin(self.selected_hexes)].copy()

    def get_neighbors(self, hex_id: str, k: int = 6) -> pd.DataFrame:
        """
        Get neighboring hexes (by H3 ring).

        Args:
            hex_id: Center hex ID
            k: Number of rings (default 1 ring = 6 neighbors)

        Returns:
            DataFrame with neighboring hexes
        """
        h3 = _import_h3()
        neighbor_ids = cast(Sequence[str], h3.k_ring(hex_id, k=k))

        # Filter to neighbors in dataset
        neighbors = self.df[self.df["hex_id"].isin(neighbor_ids)].copy()

        return neighbors
