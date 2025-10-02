# Data Pipeline Overview

The AUCS ingestion stack follows a modular, repeatable flow that mirrors the
OpenSpec specifications in `openspec/changes/add-data-ingestion`. The major
stages are summarised below.

## 1. Acquisition

* **Registry bootstrap** – `io.gtfs.registry` and `io.versioning.snapshots`
  maintain the list of source endpoints and track hashes for idempotent
  downloads.
* **Overture** – `io.overture.places` and `io.overture.transportation` provide
  BigQuery and cloud-parquet readers with bounding box/state filters so the
  pipeline can ingest either per-state slices or full national extracts.
* **External APIs** – NOAA (climate), FAA (airports), RIDB (recreation),
  Wikimedia/Wikidata (enrichment) and state registries are accessed through thin
  clients that normalise responses and persist raw bytes for reproducibility.

## 2. Normalisation

* **Category crosswalk** – `xwalk.overture_aucs` loads the curated YAML mapping
  from `docs/AUCS place category crosswalk` and applies include/exclude rules,
  ensuring every POI receives an AUCS taxonomy label.
* **Deduplication** – `dedupe.pois` combines brand proximity, fuzzy matching,
  and distance thresholds to collapse duplicate Overture records prior to H3
  indexing.
* **Schema harmonisation** – each module (e.g. `education.nces`, `jobs.lodes`,
  `parks.padus`) renames columns, enforces types, and appends metadata such as
  `quality`, `weight`, or `source` before writing Parquet outputs.

## 3. Spatial Indexing

* **H3 assignment** – utilities in `hex.aggregation` convert points, polygons,
  and lines to hexagonal indices. POIs, schools, jobs, and airports all produce
  resolution-9 hex IDs, while transportation/trails leverage helper methods for
  centroid or sampled indexing.
* **Accessibility weights** – routing matrices (see `router.batch`) and the
  accessibility builder (`accessibility.matrices`) convert skim outputs into
  per-POI weights that downstream scoring modules consume.

## 4. Enrichment & Quality

* **Knowledge graph augmentation** – `io.enrichment.wikidata` and
  `io.enrichment.wikipedia` attach capacity, heritage, and popularity metrics to
  POIs via `merge_enrichment`.
* **Quality checks** – `io.quality.checks.coverage_check` et al. compute
  coverage, completeness, validity, and consistency statistics, emitting HTML/JSON
  reports under `data/quality_reports/`.

## 5. Persistence & Versioning

* All raw downloads are hashed by `SnapshotRegistry` into
  `data/snapshots.jsonl`, enabling incremental refreshes and provenance audits.
* Processed artefacts live under `data/processed/` using predictable filenames
  per module (see `docs/data_sources.md` for the catalogue).

## 6. Orchestration

* The Typer CLI (`cli/main.py`) exposes commands for discrete ingestion steps,
  full-state runs (`aucs ingest all`), quality reporting, and snapshot
  inspection.
* Example workflows are provided in `examples/ingest_co_data.py` and
  `examples/compute_ea.ipynb` to bootstrap local testing or pipelines.

Downstream scoring and aggregation consume these normalised datasets; refer to
`docs/subscores/essentials_access.md` and `docs/routing.md` for specialised
pipelines.
