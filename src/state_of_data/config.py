"""Project paths and dataset metadata."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Dataset:
    """One immutable survey source."""

    year: int
    file: str
    rows: int
    sha256: str
    kaggle_ref: str = ""
    source_url: str = ""
    license: str = ""


def database_path() -> Path:
    """Return the configured local DuckDB path."""

    configured = os.getenv("STATE_OF_DATA_DB_PATH")
    return Path(configured) if configured else PROJECT_ROOT / "data/warehouse/state_of_data.duckdb"


def load_manifest(path: Path | None = None) -> tuple[Dataset, ...]:
    """Load and minimally validate the raw-data manifest."""

    manifest_path = path or PROJECT_ROOT / "data/raw/manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    datasets = tuple(Dataset(**item) for item in payload["datasets"])

    years = [dataset.year for dataset in datasets]
    if len(years) != len(set(years)):
        raise ValueError("O manifesto contém anos duplicados.")
    if years != sorted(years):
        raise ValueError("Os datasets do manifesto devem estar ordenados por ano.")
    return datasets
