"""Synchronize immutable survey sources from the official Data Hackers Kaggle catalog."""

from __future__ import annotations

import hashlib
import http.client
import os
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlparse

import structlog

from state_of_data.config import PROJECT_ROOT, Dataset

LOGGER = structlog.get_logger(__name__)
KAGGLE_DOWNLOAD_BASE = "https://www.kaggle.com/api/v1/datasets/download"
TRUSTED_OWNER = "datahackers/"


class SourceSyncError(RuntimeError):
    """Raised when a contracted source cannot be synchronized safely."""


class _SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Never forward a Kaggle credential to a different host."""

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: http.client.HTTPMessage,
        newurl: str,
    ) -> urllib.request.Request | None:
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected is not None and urlparse(req.full_url).hostname != urlparse(newurl).hostname:
            redirected.remove_header("Authorization")
        return redirected


def _kaggle_api_token(env_file: Path | None = None) -> str | None:
    """Read the token from the process first, then from the ignored project .env file."""

    configured = os.getenv("KAGGLE_API_TOKEN")
    if configured:
        return configured

    path = env_file or PROJECT_ROOT / ".env"
    if not path.is_file():
        return None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        key, separator, value = raw_line.partition("=")
        if separator and key.strip() == "KAGGLE_API_TOKEN":
            token = value.strip().strip("\"'")
            return token or None
    return None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download_archive(
    url: str, destination: Path, timeout: int = 120, token: str | None = None
) -> None:
    headers = {"User-Agent": "state-of-data-dashboard/0.1"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(  # noqa: S310
        url,
        headers=headers,
    )
    opener = urllib.request.build_opener(_SafeRedirectHandler())
    with (
        opener.open(request, timeout=timeout) as response,
        destination.open("wb") as output,
    ):
        shutil.copyfileobj(response, output)


def _extract_expected_csv(archive_path: Path, expected_name: str, destination: Path) -> None:
    expected = PurePosixPath(expected_name)
    if expected.is_absolute() or ".." in expected.parts:
        raise SourceSyncError(f"Nome de arquivo inseguro no manifesto: {expected_name}")

    try:
        with zipfile.ZipFile(archive_path) as archive:
            matches = [item for item in archive.infolist() if item.filename == expected_name]
            if len(matches) != 1 or matches[0].is_dir():
                raise SourceSyncError(
                    f"O pacote Kaggle não contém exatamente um arquivo chamado {expected_name}."
                )
            with archive.open(matches[0]) as source, destination.open("wb") as output:
                shutil.copyfileobj(source, output)
    except zipfile.BadZipFile as error:
        raise SourceSyncError("O Kaggle não retornou um arquivo ZIP válido.") from error


def sync_dataset(dataset: Dataset, raw_dir: Path, force: bool = False) -> Path:
    """Synchronize one source atomically against its approved data contract."""

    if not dataset.kaggle_ref.startswith(TRUSTED_OWNER):
        raise SourceSyncError(f"Fonte Kaggle não autorizada: {dataset.kaggle_ref or 'ausente'}")

    raw_dir.mkdir(parents=True, exist_ok=True)
    target = raw_dir / dataset.file
    if target.exists() and _sha256(target) == dataset.sha256:
        LOGGER.info("source_already_in_sync", year=dataset.year, file=dataset.file)
        return target
    if target.exists() and not force:
        raise SourceSyncError(
            f"O arquivo existente de {dataset.year} diverge do manifesto. "
            "Use --force para substituí-lo."
        )

    url = f"{KAGGLE_DOWNLOAD_BASE}/{dataset.kaggle_ref}"
    with tempfile.TemporaryDirectory(prefix="state-of-data-", dir=raw_dir) as temporary:
        temporary_dir = Path(temporary)
        archive_path = temporary_dir / "dataset.zip"
        candidate = temporary_dir / "source.csv"
        _download_archive(url, archive_path, token=_kaggle_api_token())
        _extract_expected_csv(archive_path, dataset.file, candidate)
        actual_sha256 = _sha256(candidate)
        if actual_sha256 != dataset.sha256:
            raise SourceSyncError(
                f"Checksum inesperado para {dataset.year}: {actual_sha256}. "
                "O dataset pode ter sido atualizado; revise antes de alterar o manifesto."
            )
        candidate.replace(target)

    LOGGER.info("source_synchronized", year=dataset.year, file=dataset.file, source=url)
    return target


def sync_sources(
    datasets: tuple[Dataset, ...], raw_dir: Path, force: bool = False
) -> tuple[Path, ...]:
    """Synchronize all source assets declared in the manifest."""

    return tuple(sync_dataset(dataset, raw_dir, force) for dataset in datasets)
