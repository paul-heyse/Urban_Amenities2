# ruff: noqa: B008
from __future__ import annotations

import json
from collections.abc import Iterable as IterableABC
from collections.abc import Mapping, Sequence
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import typer

from ..calibration.essentials import sensitivity_analysis
from ..config.loader import ParameterLoadError, load_and_document, load_params
from ..export.parquet import summary_statistics, write_explainability, write_scores
from ..export.reports import build_report
from ..hex.core import hex_boundary, hex_neighbors, latlon_to_hex
from ..io.gtfs.realtime import GTFSRealtimeIngestor
from ..io.gtfs.registry import load_registry
from ..io.gtfs.static import GTFSStaticIngestor
from ..io.overture.places import ingest_places
from ..io.overture.transportation import export_networks, prepare_transportation
from ..io.quality.checks import generate_report
from ..io.versioning.snapshots import SnapshotRegistry
from ..logging_utils import configure_logging, get_logger
from ..math.diversity import DiversityConfig
from ..monitoring.health import HealthStatus, format_report, overall_status, run_health_checks
from ..router.api import OSRMClientProtocol, RoutingAPI
from ..router.batch import BatchConfig, SkimBuilder
from ..router.osrm import OSRMClient, OSRMConfig, OSRMRoute, OSRMTable
from ..schemas.scores import EAOutputSchema
from ..scores.aggregation import WeightConfig, aggregate_scores
from ..scores.essentials_access import (
    EssentialCategoryConfig,
    EssentialsAccessCalculator,
    EssentialsAccessConfig,
)
from ..scores.explainability import top_contributors
from ..versioning.manifest import create_run_manifest, get_manifest, list_manifests

app = typer.Typer(help="AUCS utilities")
configure_logging()
logger = get_logger("aucs.cli")

RUN_STORAGE = Path("runs/manifests.jsonl")

config_app = typer.Typer(help="Configuration utilities")
hex_app = typer.Typer(help="Hexagon helpers")
run_app = typer.Typer(help="Run manifest management")
ingest_app = typer.Typer(help="Data ingestion")
data_app = typer.Typer(help="Data quality and snapshots")
score_app = typer.Typer(help="Scoring commands")
calibrate_app = typer.Typer(help="Calibration utilities")
routing_app = typer.Typer(help="Routing tools")


@app.command("healthcheck")
def cli_healthcheck(
    params: Path = typer.Option(
        Path("configs/params_default.yml"),
        "--params",
        help="Parameter configuration file",
        show_default=True,
    ),
    osrm_car: str | None = typer.Option(
        None, "--osrm-car", envvar="OSRM_CAR_URL", help="OSRM car URL"
    ),
    osrm_bike: str | None = typer.Option(
        None, "--osrm-bike", envvar="OSRM_BIKE_URL", help="OSRM bike URL"
    ),
    osrm_foot: str | None = typer.Option(
        None, "--osrm-foot", envvar="OSRM_FOOT_URL", help="OSRM foot URL"
    ),
    otp_url: str | None = typer.Option(
        None, "--otp-url", envvar="OTP_URL", help="OTP GraphQL endpoint"
    ),
    data: list[Path] = typer.Option(
        [],
        "--data",
        help="Data file to verify (can be provided multiple times)",
    ),
    data_max_age: list[int] = typer.Option(
        [],
        "--data-max-age",
        help="Maximum age in days for each --data entry",
    ),
    min_disk_gb: float = typer.Option(100.0, "--min-disk-gb", help="Minimum free disk space in GB"),
    min_memory_gb: float = typer.Option(8.0, "--min-memory-gb", help="Minimum system memory in GB"),
) -> None:
    if data_max_age and len(data_max_age) != len(data):
        raise typer.BadParameter("Provide --data-max-age for each --data entry")
    data_requirements = [
        (path, data_max_age[idx] if idx < len(data_max_age) else None)
        for idx, path in enumerate(data)
    ]
    results = run_health_checks(
        osrm_urls={"car": osrm_car, "bike": osrm_bike, "foot": osrm_foot},
        otp_url=otp_url,
        params_path=params,
        data_paths=data_requirements,
        min_disk_gb=min_disk_gb,
        min_memory_gb=min_memory_gb,
    )
    typer.echo(format_report(results))
    status = overall_status(results)
    if status == HealthStatus.CRITICAL:
        logger.error("healthcheck_failed", status=status.value)
        raise typer.Exit(code=1)
    if status == HealthStatus.WARNING:
        logger.warning("healthcheck_warning", status=status.value)


def _parse_bbox(bbox: str | None) -> tuple[float, float, float, float] | None:
    if not bbox:
        return None
    parts = [float(part) for part in bbox.split(",")]
    if len(parts) != 4:
        raise typer.BadParameter("bbox must be min_lon,min_lat,max_lon,max_lat")
    return parts[0], parts[1], parts[2], parts[3]


def _load_table(path: Path, id_column: str) -> pd.DataFrame:
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path)


def _json_safe(value: object) -> object:
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return [_json_safe(item) for item in value.tolist()]
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, (pd.Series, pd.Index)):
        return [_json_safe(item) for item in value.tolist()]
    if isinstance(value, Mapping):
        return {str(key): _json_safe(val) for key, val in value.items()}
    if isinstance(value, IterableABC) and not isinstance(value, (str, bytes)):
        return [_json_safe(item) for item in value]
    return value


def _sanitize_properties(record: Mapping[str, object]) -> dict[str, object]:
    return {str(key): _json_safe(value) for key, value in record.items()}


def _load_coords(path: Path, id_column: str) -> dict[str, tuple[float, float]]:
    table = _load_table(path, id_column)
    return {row[id_column]: (row["lon"], row["lat"]) for _, row in table.iterrows()}


def _haversine(origin: tuple[float, float], destination: tuple[float, float]) -> float:
    from math import asin, cos, radians, sin, sqrt

    lon1, lat1 = origin
    lon2, lat2 = destination
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return 6371000 * c


class GreatCircleOSRM(OSRMClientProtocol):
    def __init__(self, mode: str):
        self.mode = mode

    def _speed(self) -> float:
        return {"car": 15.0, "bike": 5.0, "foot": 1.4}.get(self.mode, 10.0)

    def route(self, coords: Sequence[tuple[float, float]]) -> OSRMRoute:
        distance = _haversine(coords[0], coords[-1])
        duration = distance / self._speed()
        return OSRMRoute(duration=duration, distance=distance, legs=[])

    def table(
        self,
        sources: Sequence[tuple[float, float]],
        destinations: Sequence[tuple[float, float]],
    ) -> OSRMTable:
        durations: list[list[float | None]] = []
        distances: list[list[float | None]] = []
        for origin in sources:
            row_duration: list[float | None] = []
            row_distance: list[float | None] = []
            for destination in destinations:
                dist = _haversine(origin, destination)
                row_distance.append(dist)
                row_duration.append(dist / self._speed())
            durations.append(row_duration)
            distances.append(row_distance)
        return OSRMTable(durations=durations, distances=distances)


def _parse_weights(value: str) -> dict[str, float]:
    candidate = Path(value)
    if candidate.exists():
        payload = json.loads(candidate.read_text(encoding="utf-8"))
    else:
        payload = json.loads(value)
    return {key: float(weight) for key, weight in payload.items()}


@config_app.command("validate")
def config_validate(path: Path) -> None:
    try:
        load_params(path)
        typer.echo(f"Configuration {path} is valid")
    except ParameterLoadError as exc:
        logger.error("config_validate_failed", path=str(path), error=str(exc))
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=1) from exc


@config_app.command("show")
def config_show(path: Path) -> None:
    try:
        summary = load_and_document(path)
    except ParameterLoadError as exc:
        logger.error("config_show_failed", path=str(path), error=str(exc))
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=1) from exc
    typer.echo(summary)


@hex_app.command("info")
def hex_info(lat: float, lon: float, k: int = typer.Option(1, help="Neighbourhood size")) -> None:
    hex_id = latlon_to_hex(lat, lon)
    neighbours = list(hex_neighbors(hex_id, k))
    typer.echo(f"hex: {hex_id}")
    typer.echo("neighbors:")
    for neighbor in neighbours:
        typer.echo(f"  - {neighbor}")


@run_app.command("init")
def run_init(params: Path, git_commit: str | None = typer.Option(None)) -> None:
    try:
        _, param_hash = load_params(params)
    except ParameterLoadError as exc:
        logger.error("run_init_failed", path=str(params), error=str(exc))
        raise typer.Exit(code=1) from exc

    manifest = create_run_manifest(
        param_hash, data_snapshot_ids=[], git_commit=git_commit, storage=RUN_STORAGE
    )
    typer.echo(f"Created run {manifest.run_id} with hash {manifest.param_hash}")


@run_app.command("show")
def run_show(run_id: str) -> None:
    manifest = get_manifest(run_id, RUN_STORAGE)
    if not manifest:
        typer.echo(f"Run {run_id} not found")
        raise typer.Exit(code=1)
    typer.echo(manifest.to_json())


@run_app.command("list")
def run_list() -> None:
    manifests = list_manifests(RUN_STORAGE)
    if not manifests:
        typer.echo("No runs recorded")
        return
    for manifest in manifests:
        typer.echo(manifest.to_json())


@ingest_app.command("overture-places")
def cli_ingest_places(
    source: Path = typer.Argument(..., help="Overture Places parquet path"),
    crosswalk: Path = typer.Option(
        Path("docs/AUCS place category crosswalk"), help="Crosswalk document"
    ),
    bbox: str | None = typer.Option(None, help="Bounding box min_lon,min_lat,max_lon,max_lat"),
    output: Path = typer.Option(Path("data/processed/pois.parquet"), help="Output parquet"),
) -> None:
    parsed_bbox = _parse_bbox(bbox)
    ingest_places(source, crosswalk_path=crosswalk, bbox=parsed_bbox, output_path=output)
    typer.echo(f"Wrote POIs to {output}")


@ingest_app.command("gtfs")
def cli_ingest_gtfs(
    agency_name: str = typer.Argument(..., help="Agency name as listed in the registry"),
    output_dir: Path = typer.Option(Path("data/processed"), help="Directory for outputs"),
) -> None:
    registry = load_registry()
    agency = next((item for item in registry if item.name.lower() == agency_name.lower()), None)
    if not agency:
        typer.echo(f"Agency {agency_name} not found in registry")
        raise typer.Exit(code=1)
    outputs = GTFSStaticIngestor().ingest(agency, output_dir=output_dir)
    typer.echo(f"Static GTFS outputs: {outputs}")
    if agency.realtime_urls:
        realtime_path = GTFSRealtimeIngestor().ingest(agency)
        typer.echo(f"Realtime metrics written to {realtime_path}")


@ingest_app.command("all")
def cli_ingest_all(
    places_source: Path = typer.Option(
        Path("data/raw/overture_places.parquet"), help="Overture Places source"
    ),
    states: str = typer.Option("CO,UT,ID", help="States to process"),
) -> None:
    ingest_places(places_source, output_path=Path("data/processed/pois.parquet"))
    state_list = [item.strip() for item in states.split(",") if item.strip()]
    registry = load_registry()
    ingestor = GTFSStaticIngestor()
    for agency in registry:
        if agency.state in state_list:
            ingestor.ingest(agency)
    typer.echo("Completed ingestion for requested states")


@data_app.command("quality-report")
def cli_quality_report(
    pois_path: Path = typer.Option(Path("data/processed/pois.parquet"), help="POI parquet"),
    output_dir: Path = typer.Option(Path("data/quality_reports"), help="Report directory"),
) -> None:
    pois = pd.read_parquet(pois_path)
    report = generate_report(pois, output_dir=output_dir)
    typer.echo(json.dumps(report, indent=2))


@data_app.command("list-snapshots")
def cli_list_snapshots(
    path: Path = typer.Option(Path("data/snapshots.jsonl"), help="Snapshot registry")
) -> None:
    registry = SnapshotRegistry(path)
    records = registry.list_json()
    if not records:
        typer.echo("No snapshots recorded")
        return
    for record in records:
        typer.echo(json.dumps(record, sort_keys=True))


@routing_app.command("build-osrm")
def routing_build_osrm(
    segments_path: Path = typer.Argument(..., help="Transportation segments parquet"),
    profile: str = typer.Option("car", help="OSRM profile"),
    output_dir: Path = typer.Option(Path("data/processed"), help="Output directory"),
) -> None:
    frame = pd.read_parquet(segments_path)
    prepared = prepare_transportation(frame)
    paths = export_networks(prepared, output_root=output_dir)
    typer.echo(f"Exported networks: {paths}")


@routing_app.command("build-otp")
def routing_build_otp(
    gtfs_dir: Path = typer.Argument(..., help="Directory with GTFS feeds"),
    output_path: Path = typer.Option(
        Path("data/processed/otp_manifest.json"), help="Output manifest"
    ),
) -> None:
    feeds = sorted(p.name for p in gtfs_dir.glob("*.zip"))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps({"feeds": feeds, "generated_at": datetime.utcnow().isoformat()}),
        encoding="utf-8",
    )
    typer.echo(f"OTP manifest written to {output_path}")


@app.command("aggregate")
def cli_aggregate(
    subscores: Path = typer.Argument(..., help="Parquet/CSV with subscore columns and hex_id"),
    weights: str = typer.Option(..., help="JSON weights mapping or path to JSON file"),
    output: Path = typer.Option(
        Path("data/processed/aucs.parquet"), help="Output Parquet for AUCS scores"
    ),
    explainability_output: Path | None = typer.Option(
        None, help="Optional explainability Parquet output"
    ),
    run_id: str | None = typer.Option(None, help="Run identifier to annotate outputs"),
    report_path: Path | None = typer.Option(None, help="Optional QA HTML report"),
) -> None:
    try:
        frame = _load_table(subscores, "hex_id")
    except FileNotFoundError as exc:
        logger.error("aggregate_input_missing", path=str(subscores))
        typer.echo(f"Error: File not found: {subscores}")
        raise typer.Exit(code=1) from exc
    weight_config = WeightConfig(_parse_weights(weights))
    try:
        aggregated = aggregate_scores(frame, value_column="aucs", weight_config=weight_config)
    except KeyboardInterrupt as exc:
        typer.echo("Operation cancelled by user")
        raise typer.Exit(code=1) from exc
    aggregated["run_id"] = run_id or "manual"
    aggregated["generated_at"] = datetime.utcnow().isoformat()
    write_scores(aggregated, output)
    typer.echo(f"Wrote AUCS scores to {output}")
    if explainability_output and "contributors" in frame.columns:
        explain = top_contributors(frame)
        write_explainability(explain, explainability_output)
        typer.echo(f"Wrote explainability to {explainability_output}")
    stats = summary_statistics(aggregated, score_column="aucs")
    typer.echo(json.dumps(stats, indent=2))
    if report_path:
        build_report(aggregated, frame, report_path)
        typer.echo(f"QA report written to {report_path}")


@app.command("show")
def cli_show(
    hex_id: str = typer.Option(..., "--hex", help="Hex ID to inspect"),
    scores: Path = typer.Option(
        Path("data/processed/aucs.parquet"), "--scores", help="Scores table"
    ),
) -> None:
    frame = _load_table(scores, "hex_id")
    match = frame[frame["hex_id"] == hex_id]
    if match.empty:
        typer.echo(f"Hex {hex_id} not found in {scores}")
        raise typer.Exit(code=1)
    typer.echo(match.to_json(orient="records", indent=2))


@app.command("export")
def cli_export(
    output: Path = typer.Argument(..., help="Output path"),
    format: str = typer.Option("geojson", help="Export format", case_sensitive=False),
    scores: Path = typer.Option(
        Path("data/processed/aucs.parquet"), "--scores", help="Scores table"
    ),
) -> None:
    frame = _load_table(scores, "hex_id")
    fmt = format.lower()
    if fmt != "geojson":
        typer.echo(f"Unsupported export format: {format}")
        raise typer.Exit(code=1)
    features = []
    for record in frame.to_dict(orient="records"):
        hex_id = record["hex_id"]
        properties = _sanitize_properties(record)
        try:
            boundary = [(float(lon), float(lat)) for lat, lon in hex_boundary(hex_id)]
        except ValueError:
            logger.warning("invalid_hex", hex_id=hex_id)
            features.append(
                {
                    "type": "Feature",
                    "geometry": None,
                    "properties": properties,
                }
            )
            continue
        if boundary and boundary[0] != boundary[-1]:
            boundary.append(boundary[0])
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": [boundary]},
                "properties": properties,
            }
        )
    collection = {"type": "FeatureCollection", "features": features}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(collection, indent=2), encoding="utf-8")
    typer.echo(f"Wrote GeoJSON to {output}")


@routing_app.command("compute-skims")
def routing_compute_skims(
    origins_path: Path = typer.Argument(..., help="Origins table with columns id, lat, lon"),
    destinations_path: Path = typer.Argument(..., help="Destinations table"),
    output_path: Path = typer.Option(Path("data/processed/skims.parquet"), help="Output path"),
    mode: str = typer.Option("car", help="Mode"),
    period: str | None = typer.Option(None, help="Period label"),
    osrm_base_url: str | None = typer.Option(None, help="Optional OSRM base URL"),
) -> None:
    origin_coords = _load_coords(origins_path, "id")
    dest_coords = _load_coords(destinations_path, "id")
    client: OSRMClientProtocol
    if osrm_base_url:
        client = OSRMClient(OSRMConfig(base_url=osrm_base_url, profile=mode))
    else:
        client = GreatCircleOSRM(mode)
    api = RoutingAPI({mode: client})
    builder = SkimBuilder(api, BatchConfig(mode=mode, period=period))
    frame = builder.matrix(list(origin_coords.values()), list(dest_coords.values()))
    origin_keys = list(origin_coords.keys())
    dest_keys = list(dest_coords.keys())
    frame["origin_id"] = frame["origin_index"].map(lambda idx: origin_keys[idx])
    frame["destination_id"] = frame["destination_index"].map(lambda idx: dest_keys[idx])
    builder.write_parquet(frame, output_path)


@score_app.command("ea")
def score_ea(
    pois_path: Path = typer.Argument(..., help="POI parquet"),
    accessibility_path: Path = typer.Argument(..., help="Accessibility parquet"),
    output: Path = typer.Option(Path("data/processed/ea_scores.parquet"), help="Output path"),
    category_output: Path | None = typer.Option(None, help="Optional category scores output"),
    hex_id: str | None = typer.Option(None, help="Optional hex filter"),
) -> None:
    pois = pd.read_parquet(pois_path)
    accessibility = pd.read_parquet(accessibility_path)
    if hex_id:
        accessibility = accessibility[
            accessibility.get("hex_id", accessibility.get("origin_hex")) == hex_id
        ]
        if accessibility.empty:
            typer.echo(f"No accessibility records for hex {hex_id}")
            raise typer.Exit(code=1)
    categories = sorted(pois["aucstype"].dropna().unique())
    category_params = {
        category: EssentialCategoryConfig(rho=0.5, kappa=0.1, diversity=DiversityConfig())
        for category in categories
    }
    config = EssentialsAccessConfig(categories=categories, category_params=category_params)
    calculator = EssentialsAccessCalculator(config)
    ea_scores, category_scores = calculator.compute(pois, accessibility)
    EAOutputSchema.validate(ea_scores)
    ea_scores.to_parquet(output)
    if category_output:
        category_scores.to_parquet(category_output)
    typer.echo(f"EA scores written to {output}")
    if hex_id:
        typer.echo(ea_scores[ea_scores["hex_id"] == hex_id].to_string(index=False))


@calibrate_app.command("ea")
def calibrate_ea(
    pois_path: Path = typer.Argument(..., help="POI parquet"),
    accessibility_path: Path = typer.Argument(..., help="Accessibility parquet"),
    parameter: str = typer.Option(
        "rho:groceries", help="Parameter descriptor (e.g. rho:groceries)"
    ),
    values: str = typer.Option("0.3,0.5,0.7", help="Comma separated parameter values"),
) -> None:
    pois = pd.read_parquet(pois_path)
    accessibility = pd.read_parquet(accessibility_path)
    categories = sorted(pois["aucstype"].dropna().unique())
    category_params = {
        category: EssentialCategoryConfig(rho=0.5, kappa=0.1, diversity=DiversityConfig())
        for category in categories
    }
    config = EssentialsAccessConfig(categories=categories, category_params=category_params)
    calculator = EssentialsAccessCalculator(config)
    value_list = [float(item) for item in values.split(",") if item.strip()]
    results = sensitivity_analysis(calculator, pois, accessibility, parameter, value_list)
    typer.echo(results.to_string(index=False))


app.add_typer(config_app, name="config")
app.add_typer(hex_app, name="hex")
app.add_typer(run_app, name="run")
app.add_typer(ingest_app, name="ingest")
app.add_typer(data_app, name="data")
app.add_typer(score_app, name="score")
app.add_typer(calibrate_app, name="calibrate")
app.add_typer(routing_app, name="routing")


if __name__ == "__main__":
    app()
