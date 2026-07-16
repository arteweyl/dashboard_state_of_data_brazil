from __future__ import annotations

import hashlib
import http.client
import io
import shutil
import zipfile
from pathlib import Path
from urllib.request import Request

import pytest

from state_of_data import download
from state_of_data.config import Dataset
from state_of_data.download import SourceSyncError, sync_dataset


def dataset_for(content: bytes) -> Dataset:
    source = Path("survey.csv")
    checksum = hashlib.sha256(content).hexdigest()
    return Dataset(
        2025,
        source.name,
        1,
        checksum,
        "datahackers/state-of-data-test",
        "https://www.kaggle.com/datasets/datahackers/state-of-data-test",
        "Open Database",
    )


def test_sync_dataset_extracts_and_validates_atomically(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    content = b"answer\n42\n"
    package = tmp_path / "source.zip"
    with zipfile.ZipFile(package, "w") as archive:
        archive.writestr("survey.csv", content)

    def fake_download(
        url: str, destination: Path, timeout: int = 120, token: str | None = None
    ) -> None:
        assert url.endswith("datahackers/state-of-data-test")
        assert timeout == 120
        assert token is None
        shutil.copyfile(package, destination)

    monkeypatch.setattr(download, "_download_archive", fake_download)

    target = sync_dataset(dataset_for(content), tmp_path / "raw")

    assert target.read_bytes() == content
    assert not list((tmp_path / "raw").glob("state-of-data-*"))


def test_sync_dataset_rejects_untrusted_source_and_checksum(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    valid = dataset_for(b"expected")
    untrusted = Dataset(2025, "survey.csv", 1, valid.sha256, "someone/dataset")
    with pytest.raises(SourceSyncError, match="não autorizada"):
        sync_dataset(untrusted, tmp_path / "raw")

    package = tmp_path / "changed.zip"
    with zipfile.ZipFile(package, "w") as archive:
        archive.writestr("survey.csv", b"changed")
    monkeypatch.setattr(
        download,
        "_download_archive",
        lambda url, destination, timeout=120, token=None: shutil.copyfile(package, destination),
    )
    with pytest.raises(SourceSyncError, match="Checksum inesperado"):
        sync_dataset(valid, tmp_path / "raw")


def test_existing_changed_file_requires_force(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "survey.csv").write_bytes(b"changed")

    with pytest.raises(SourceSyncError, match="--force"):
        sync_dataset(dataset_for(b"expected"), raw)


def test_kaggle_token_prefers_environment_and_supports_ignored_env_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("KAGGLE_API_TOKEN=from-file\n", encoding="utf-8")

    assert download._kaggle_api_token(env_file) == "from-file"

    monkeypatch.setenv("KAGGLE_API_TOKEN", "from-process")
    assert download._kaggle_api_token(env_file) == "from-process"


def test_cross_host_redirect_removes_authorization_header() -> None:
    handler = download._SafeRedirectHandler()
    original = Request(
        "https://www.kaggle.com/api/v1/datasets/download/datahackers/example",
        headers={"Authorization": "Bearer secret"},
    )

    redirected = handler.redirect_request(
        original,
        io.BytesIO(),
        302,
        "Found",
        http.client.HTTPMessage(),
        "https://storage.googleapis.com/signed-download",
    )

    assert redirected is not None
    assert redirected.get_header("Authorization") is None
