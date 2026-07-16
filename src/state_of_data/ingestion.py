"""Validated, idempotent ingestion of raw survey CSVs into DuckDB."""

from __future__ import annotations

import csv
import hashlib
from datetime import UTC, datetime
from pathlib import Path

import duckdb
import structlog

from state_of_data.config import Dataset
from state_of_data.naming import unique_column_names

LOGGER = structlog.get_logger(__name__)


class DataValidationError(ValueError):
    """Raised when an immutable raw input differs from its contract."""


def file_sha256(path: Path) -> str:
    """Calculate a file digest without loading the whole dataset in memory."""

    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _quoted_identifier(value: str) -> str:
    return f'"{value.replace(chr(34), chr(34) * 2)}"'


def _sql_literal(value: str) -> str:
    return f"'{value.replace(chr(39), chr(39) * 2)}'"


def _read_header(path: Path) -> list[str]:
    with path.open(encoding="utf-8-sig", newline="") as source:
        return next(csv.reader(source))


def validate_source(dataset: Dataset, raw_dir: Path) -> Path:
    """Validate existence and checksum before a source reaches the warehouse."""

    source_path = raw_dir / dataset.file
    if not source_path.is_file():
        raise DataValidationError(f"Arquivo bruto ausente: {source_path}")
    actual_hash = file_sha256(source_path)
    if actual_hash != dataset.sha256:
        raise DataValidationError(
            f"Checksum divergente para {dataset.file}: esperado {dataset.sha256}, "
            f"obtido {actual_hash}."
        )
    return source_path


def ingest_dataset(
    connection: duckdb.DuckDBPyConnection,
    dataset: Dataset,
    raw_dir: Path,
) -> int:
    """Replace one raw table atomically and record its provenance."""

    source_path = validate_source(dataset, raw_dir)
    original_names = _read_header(source_path)
    normalized_names = unique_column_names(original_names)
    projections = ",\n".join(
        f"{_quoted_identifier(source)} AS {_quoted_identifier(target)}"
        for source, target in zip(original_names, normalized_names, strict=True)
    )
    table_name = f"survey_{dataset.year}"

    connection.execute("BEGIN TRANSACTION")
    try:
        connection.execute("CREATE SCHEMA IF NOT EXISTS raw")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS raw.ingestion_manifest (
                survey_year INTEGER PRIMARY KEY,
                source_file VARCHAR NOT NULL,
                source_sha256 VARCHAR NOT NULL,
                row_count BIGINT NOT NULL,
                ingested_at TIMESTAMPTZ NOT NULL
            )
            """
        )
        connection.execute(
            f"""
            CREATE OR REPLACE TABLE raw.{table_name} AS
            SELECT
                {projections}
            FROM read_csv(
                {_sql_literal(source_path.as_posix())},
                header = true,
                all_varchar = true,
                strict_mode = true
            )
            """
        )
        row = connection.execute(f"SELECT count(*) FROM raw.{table_name}").fetchone()
        row_count = int(row[0]) if row else 0
        if row_count != dataset.rows:
            raise DataValidationError(
                f"Quantidade inesperada em {dataset.file}: esperada {dataset.rows}, "
                f"obtida {row_count}."
            )

        connection.execute(
            "DELETE FROM raw.ingestion_manifest WHERE survey_year = ?",
            [dataset.year],
        )
        connection.execute(
            """
            INSERT INTO raw.ingestion_manifest VALUES (?, ?, ?, ?, ?)
            """,
            [dataset.year, dataset.file, dataset.sha256, row_count, datetime.now(UTC)],
        )
        connection.execute("COMMIT")
    except Exception:
        connection.execute("ROLLBACK")
        raise

    LOGGER.info(
        "dataset_ingested",
        survey_year=dataset.year,
        rows=row_count,
        columns=len(normalized_names),
    )
    return row_count


def ingest_all(datasets: tuple[Dataset, ...], raw_dir: Path, database: Path) -> int:
    """Ingest all contracted sources and return their total row count."""

    database.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    with duckdb.connect(database.as_posix()) as connection:
        for dataset in datasets:
            total += ingest_dataset(connection, dataset, raw_dir)
    LOGGER.info("ingestion_completed", datasets=len(datasets), rows=total, database=str(database))
    return total
