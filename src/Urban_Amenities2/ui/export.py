"""Export utilities for AUCS data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import geopandas as gpd
import pandas as pd
import structlog
from shapely.geometry import Polygon

logger = structlog.get_logger()


def hex_to_polygon(hex_id: str) -> Polygon:
    """
    Convert H3 hex ID to Shapely polygon.

    Args:
        hex_id: H3 hex ID

    Returns:
        Shapely Polygon
    """
    import h3

    boundary = h3.h3_to_geo_boundary(hex_id, geo_json=True)
    return Polygon(boundary)


def export_geojson(
    df: pd.DataFrame,
    output_path: Path,
    properties: list[str] | None = None,
) -> None:
    """
    Export DataFrame to GeoJSON.

    Args:
        df: DataFrame with hex_id and score columns
        output_path: Path to output GeoJSON file
        properties: List of properties to include (defaults to all columns)
    """
    logger.info("export_geojson_start", rows=len(df), output=str(output_path))

    # Convert hex IDs to geometries
    geometries = [hex_to_polygon(hex_id) for hex_id in df["hex_id"]]

    # Create GeoDataFrame
    gdf = gpd.GeoDataFrame(df, geometry=geometries, crs="EPSG:4326")

    # Select properties to include
    if properties:
        columns_to_keep = ["geometry"] + [p for p in properties if p in gdf.columns]
        gdf = gdf[columns_to_keep]

    # Write to file
    gdf.to_file(output_path, driver="GeoJSON")
    logger.info("export_geojson_complete", path=str(output_path))


def export_csv(
    df: pd.DataFrame,
    output_path: Path,
    include_geometry: bool = False,
) -> None:
    """
    Export DataFrame to CSV.

    Args:
        df: DataFrame with hex-level data
        output_path: Path to output CSV file
        include_geometry: Whether to include lat/lon columns
    """
    logger.info("export_csv_start", rows=len(df), output=str(output_path))

    export_df = df.copy()

    # Optionally add lat/lon centroids
    if include_geometry and "lat" not in export_df.columns:
        import h3

        centroids = [h3.h3_to_geo(hex_id) for hex_id in export_df["hex_id"]]
        export_df["lat"] = [c[0] for c in centroids]
        export_df["lon"] = [c[1] for c in centroids]

    export_df.to_csv(output_path, index=False)
    logger.info("export_csv_complete", path=str(output_path))


def export_shapefile(df: pd.DataFrame, output_path: Path) -> None:
    """
    Export DataFrame to Shapefile.

    Args:
        df: DataFrame with hex_id and score columns
        output_path: Path to output Shapefile (.shp)
    """
    logger.info("export_shapefile_start", rows=len(df), output=str(output_path))

    # Convert hex IDs to geometries
    geometries = [hex_to_polygon(hex_id) for hex_id in df["hex_id"]]

    # Create GeoDataFrame
    gdf = gpd.GeoDataFrame(df, geometry=geometries, crs="EPSG:4326")

    # Truncate column names to 10 chars (Shapefile limitation)
    gdf.columns = [col[:10] if len(col) > 10 else col for col in gdf.columns]

    # Write to file
    gdf.to_file(output_path, driver="ESRI Shapefile")
    logger.info("export_shapefile_complete", path=str(output_path))


def export_parquet(df: pd.DataFrame, output_path: Path) -> None:
    """
    Export DataFrame to Parquet (most efficient).

    Args:
        df: DataFrame with hex-level data
        output_path: Path to output Parquet file
    """
    logger.info("export_parquet_start", rows=len(df), output=str(output_path))
    df.to_parquet(output_path, compression="snappy", index=False)
    logger.info("export_parquet_complete", path=str(output_path))


def create_shareable_url(
    base_url: str,
    state: str | None = None,
    metro: str | None = None,
    subscore: str | None = None,
    zoom: int | None = None,
    center_lat: float | None = None,
    center_lon: float | None = None,
) -> str:
    """
    Create a shareable URL with encoded parameters.

    Args:
        base_url: Base application URL
        state: Selected state filter
        metro: Selected metro filter
        subscore: Selected subscore
        zoom: Map zoom level
        center_lat: Map center latitude
        center_lon: Map center longitude

    Returns:
        URL string with query parameters
    """
    from urllib.parse import urlencode

    params = {}

    if state:
        params["state"] = state
    if metro:
        params["metro"] = metro
    if subscore:
        params["subscore"] = subscore
    if zoom is not None:
        params["zoom"] = zoom
    if center_lat is not None and center_lon is not None:
        params["lat"] = center_lat
        params["lon"] = center_lon

    if not params:
        return base_url

    query_string = urlencode(params)
    return f"{base_url}?{query_string}"

