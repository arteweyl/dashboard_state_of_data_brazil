from __future__ import annotations

import json
from pathlib import Path

import pytest

from state_of_data.config import database_path, load_manifest


def write_manifest(path: Path, datasets: list[dict[str, object]]) -> None:
    path.write_text(json.dumps({"datasets": datasets}), encoding="utf-8")


def test_load_manifest_returns_ordered_datasets(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    write_manifest(
        manifest,
        [{"year": 2024, "file": "survey.csv", "rows": 2, "sha256": "abc"}],
    )

    datasets = load_manifest(manifest)

    assert datasets[0].year == 2024
    assert datasets[0].file == "survey.csv"


@pytest.mark.parametrize(
    "items,message",
    [
        (
            [
                {"year": 2024, "file": "a", "rows": 1, "sha256": "a"},
                {"year": 2024, "file": "b", "rows": 1, "sha256": "b"},
            ],
            "duplicados",
        ),
        (
            [
                {"year": 2025, "file": "a", "rows": 1, "sha256": "a"},
                {"year": 2024, "file": "b", "rows": 1, "sha256": "b"},
            ],
            "ordenados",
        ),
    ],
)
def test_load_manifest_rejects_invalid_year_order(
    tmp_path: Path, items: list[dict[str, object]], message: str
) -> None:
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, items)

    with pytest.raises(ValueError, match=message):
        load_manifest(manifest)


def test_database_path_uses_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STATE_OF_DATA_DB_PATH", "custom.duckdb")

    assert database_path() == Path("custom.duckdb")
