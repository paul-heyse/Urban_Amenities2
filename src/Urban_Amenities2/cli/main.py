"""Typer based command line interface for AUCS core infrastructure."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from ..config.loader import ParameterLoadError, load_and_document, load_params
from ..hex.core import hex_neighbors, latlon_to_hex
from ..logging_utils import configure_logging, get_logger
from ..versioning.manifest import create_run_manifest, get_manifest, list_manifests

app = typer.Typer(help="AUCS core infrastructure utilities")
configure_logging()
logger = get_logger("aucs.cli")

RUN_STORAGE = Path("runs/manifests.jsonl")

config_app = typer.Typer(help="Configuration utilities")
hex_app = typer.Typer(help="Hexagon helpers")
run_app = typer.Typer(help="Run manifest management")


@config_app.command("validate")
def config_validate(path: Path) -> None:
    """Validate a parameter configuration file."""

    try:
        load_params(path)
        typer.echo(f"Configuration {path} is valid")
    except ParameterLoadError as exc:
        logger.error("config_validate_failed", path=str(path), error=str(exc))
        raise typer.Exit(code=1) from exc


@config_app.command("show")
def config_show(path: Path) -> None:
    """Display parameter configuration in a human readable form."""

    try:
        summary = load_and_document(path)
    except ParameterLoadError as exc:
        logger.error("config_show_failed", path=str(path), error=str(exc))
        raise typer.Exit(code=1) from exc
    typer.echo(summary)


@hex_app.command("info")
def hex_info(lat: float, lon: float, k: int = typer.Option(1, help="Neighbourhood size")) -> None:
    """Display information about the hexagon covering the provided coordinates."""

    hex_id = latlon_to_hex(lat, lon)
    neighbours = list(hex_neighbors(hex_id, k))
    typer.echo(f"hex: {hex_id}")
    typer.echo("neighbors:")
    for neighbor in neighbours:
        typer.echo(f"  - {neighbor}")


@run_app.command("init")
def run_init(params: Path, git_commit: Optional[str] = typer.Option(None)) -> None:
    """Initialise a new scoring run manifest."""

    try:
        _, param_hash = load_params(params)
    except ParameterLoadError as exc:
        logger.error("run_init_failed", path=str(params), error=str(exc))
        raise typer.Exit(code=1) from exc

    manifest = create_run_manifest(param_hash, data_snapshot_ids=[], git_commit=git_commit, storage=RUN_STORAGE)
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


app.add_typer(config_app, name="config")
app.add_typer(hex_app, name="hex")
app.add_typer(run_app, name="run")


if __name__ == "__main__":
    app()
