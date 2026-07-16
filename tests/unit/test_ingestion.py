from __future__ import annotations

import hashlib
from pathlib import Path

import duckdb
import pytest

from state_of_data.config import Dataset
from state_of_data.ingestion import (
    DataValidationError,
    file_sha256,
    ingest_all,
    ingest_dataset,
    validate_source,
)


def create_source(path: Path) -> Dataset:
    path.write_text("ID,1.a Idade\na,31\nb,42\n", encoding="utf-8")
    return Dataset(
        year=2024,
        file=path.name,
        rows=2,
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
    )


def test_file_sha256(tmp_path: Path) -> None:
    source = tmp_path / "source.csv"
    source.write_bytes(b"state-of-data")

    assert file_sha256(source) == hashlib.sha256(b"state-of-data").hexdigest()


def test_validate_source_rejects_missing_and_changed_files(tmp_path: Path) -> None:
    missing = Dataset(2024, "missing.csv", 0, "hash")
    with pytest.raises(DataValidationError, match="ausente"):
        validate_source(missing, tmp_path)

    source = tmp_path / "survey.csv"
    source.write_text("changed", encoding="utf-8")
    changed = Dataset(2024, source.name, 0, "wrong")
    with pytest.raises(DataValidationError, match="Checksum"):
        validate_source(changed, tmp_path)


def test_ingest_dataset_normalizes_schema_and_records_provenance(tmp_path: Path) -> None:
    source = tmp_path / "survey.csv"
    dataset = create_source(source)

    with duckdb.connect() as connection:
        count = ingest_dataset(connection, dataset, tmp_path)
        columns = connection.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = 'raw' AND table_name = 'survey_2024' ORDER BY ordinal_position"
        ).fetchall()
        manifest = connection.execute(
            "SELECT survey_year, row_count FROM raw.ingestion_manifest"
        ).fetchone()

    assert count == 2
    assert columns == [("id",), ("q_1_a_idade",)]
    assert manifest == (2024, 2)


def test_ingest_dataset_rolls_back_unexpected_row_count(tmp_path: Path) -> None:
    source = tmp_path / "survey.csv"
    valid = create_source(source)
    invalid = Dataset(valid.year, valid.file, 99, valid.sha256)

    with duckdb.connect() as connection:
        with pytest.raises(DataValidationError, match="Quantidade inesperada"):
            ingest_dataset(connection, invalid, tmp_path)
        table_count = connection.execute(
            "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'raw'"
        ).fetchone()

    assert table_count == (0,)


def test_ingest_all_creates_database(tmp_path: Path) -> None:
    source = tmp_path / "survey.csv"
    dataset = create_source(source)
    database = tmp_path / "warehouse" / "test.duckdb"

    total = ingest_all((dataset,), tmp_path, database)

    assert total == 2
    assert database.is_file()
