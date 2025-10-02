"""Hex selection and detail viewing."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import structlog

logger = structlog.get_logger()


@dataclass
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
    top_amenities: list[dict[str, str]] = None
    top_modes: dict[str, float] = None

    @classmethod
    def from_row(cls, row: pd.Series) -> HexDetails:
        """
        Create HexDetails from a DataFrame row.

        Args:
            row: DataFrame row with hex data

        Returns:
            HexDetails instance
        """
        return cls(
            hex_id=row["hex_id"],
            lat=row["lat"],
            lon=row["lon"],
            state=row["state"],
            metro=row.get("metro"),
            county=row.get("county"),
            population=row.get("population"),
            aucs=row["aucs"],
            ea=row["ea"],
            lca=row["lca"],
            muhaa=row["muhaa"],
            jea=row["jea"],
            morr=row["morr"],
            cte=row["cte"],
            sou=row["sou"],
            top_amenities=row.get("top_amenities", []),
            top_modes=row.get("top_modes", {}),
        )


class HexSelector:
    """Manage hex selection and comparison."""

    def __init__(self, df: pd.DataFrame):
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
        import h3

        # Get neighbor hex IDs
        neighbor_ids = list(h3.k_ring(hex_id, k=1))

        # Filter to neighbors in dataset
        neighbors = self.df[self.df["hex_id"].isin(neighbor_ids)].copy()

        return neighbors

