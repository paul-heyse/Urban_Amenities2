## ADDED Requirements

### Requirement: Score Dataset Selection
The UI data loader SHALL discover score datasets by filename pattern and avoid treating support parquet files (e.g., metadata) as the primary score table.

#### Scenario: Prefer `_scores.parquet`
- **WHEN** multiple parquet files exist in the UI data directory (e.g., `20240101_scores.parquet`, `metadata.parquet`)
- **THEN** the loader SHALL select the newest file matching `*_scores.parquet` as the score dataset before validation.

#### Scenario: Fallback log when no score file present
- **WHEN** no file matches `*_scores.parquet`
- **THEN** the loader SHALL log a warning and leave scores empty instead of raising a KeyError on metadata columns.

#### Scenario: Metadata join remains optional
- **WHEN** `metadata.parquet` is present alongside the score dataset
- **THEN** the loader SHALL join metadata after the score table is validated, preserving required score columns.
