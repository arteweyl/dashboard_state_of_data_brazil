from __future__ import annotations

from pathlib import Path

from pytest import MonkeyPatch

from state_of_data import cli
from state_of_data.config import Dataset


def test_main_dispatches_ingestion(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    raw_dir = tmp_path / "raw"
    database = tmp_path / "warehouse.duckdb"
    datasets = (Dataset(2025, "survey.csv", 1, "abc"),)
    call: dict[str, object] = {}

    monkeypatch.setattr(cli, "load_manifest", lambda path: datasets)

    def fake_ingest_all(
        received_datasets: tuple[Dataset, ...], received_raw: Path, received_database: Path
    ) -> int:
        call.update(
            datasets=received_datasets,
            raw_dir=received_raw,
            database=received_database,
        )
        return 1

    monkeypatch.setattr(cli, "ingest_all", fake_ingest_all)

    result = cli.main(
        [
            "ingest",
            "--raw-dir",
            str(raw_dir),
            "--manifest",
            str(manifest),
            "--database",
            str(database),
        ]
    )

    assert result == 0
    assert call == {"datasets": datasets, "raw_dir": raw_dir, "database": database}


def test_main_dispatches_source_sync(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    raw_dir = tmp_path / "raw"
    datasets = (Dataset(2025, "survey.csv", 1, "abc"),)
    call: dict[str, object] = {}
    monkeypatch.setattr(cli, "load_manifest", lambda path: datasets)

    def fake_sync_sources(
        received_datasets: tuple[Dataset, ...], received_raw: Path, force: bool
    ) -> tuple[Path, ...]:
        call.update(datasets=received_datasets, raw_dir=received_raw, force=force)
        return ()

    monkeypatch.setattr(cli, "sync_sources", fake_sync_sources)

    result = cli.main(
        [
            "sources",
            "sync",
            "--manifest",
            str(manifest),
            "--raw-dir",
            str(raw_dir),
            "--force",
        ]
    )

    assert result == 0
    assert call == {"datasets": datasets, "raw_dir": raw_dir, "force": True}


def test_main_dispatches_static_build(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    database = tmp_path / "warehouse.duckdb"
    output = tmp_path / "site"
    template_dir = tmp_path / "templates"
    assets_dir = tmp_path / "assets"
    call: dict[str, Path] = {}

    def fake_build_static_site(
        received_database: Path,
        received_output: Path,
        received_templates: Path,
        received_assets: Path,
    ) -> Path:
        call.update(
            database=received_database,
            output=received_output,
            templates=received_templates,
            assets=received_assets,
        )
        return received_output / "index.html"

    monkeypatch.setattr(cli, "build_static_site", fake_build_static_site)

    result = cli.main(
        [
            "build-static",
            "--database",
            str(database),
            "--output",
            str(output),
            "--template-dir",
            str(template_dir),
            "--assets-dir",
            str(assets_dir),
        ]
    )

    assert result == 0
    assert call == {
        "database": database,
        "output": output,
        "templates": template_dir,
        "assets": assets_dir,
    }
