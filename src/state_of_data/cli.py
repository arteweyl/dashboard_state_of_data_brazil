"""Command-line interface for repeatable analytics workflows."""

from __future__ import annotations

import argparse
from pathlib import Path

import structlog

from state_of_data.config import PROJECT_ROOT, database_path, load_manifest
from state_of_data.download import sync_sources
from state_of_data.ingestion import ingest_all
from state_of_data.static_site import build_static_site


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="state-of-data")
    commands = parser.add_subparsers(dest="command", required=True)
    sources = commands.add_parser(
        "sources",
        help="Gerencia as fontes de dados contratadas.",
    )
    source_commands = sources.add_subparsers(dest="source_command", required=True)
    sync = source_commands.add_parser(
        "sync",
        help="Sincroniza e valida as fontes oficiais da Data Hackers no Kaggle.",
    )
    sync.add_argument(
        "--raw-dir",
        type=Path,
        default=PROJECT_ROOT / "data/raw",
        help="Diretório de destino dos CSVs.",
    )
    sync.add_argument(
        "--manifest",
        type=Path,
        default=PROJECT_ROOT / "data/raw/manifest.json",
        help="Contrato JSON das fontes.",
    )
    sync.add_argument(
        "--force",
        action="store_true",
        help="Substitui um arquivo local somente após validar o novo checksum.",
    )
    ingest = commands.add_parser("ingest", help="Valida e ingere todos os CSVs brutos.")
    ingest.add_argument(
        "--raw-dir",
        type=Path,
        default=PROJECT_ROOT / "data/raw",
        help="Diretório dos CSVs de origem.",
    )
    ingest.add_argument(
        "--manifest",
        type=Path,
        default=PROJECT_ROOT / "data/raw/manifest.json",
        help="Contrato JSON das fontes.",
    )
    ingest.add_argument("--database", type=Path, default=database_path())
    static = commands.add_parser(
        "build-static",
        help="Gera o site estático a partir dos marts agregados.",
    )
    static.add_argument("--database", type=Path, default=database_path())
    static.add_argument("--output", type=Path, default=PROJECT_ROOT / "site")
    static.add_argument(
        "--template-dir",
        type=Path,
        default=PROJECT_ROOT / "static/templates",
    )
    static.add_argument(
        "--assets-dir",
        type=Path,
        default=PROJECT_ROOT / "static/assets",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Execute the requested workflow."""

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer(),
        ]
    )
    args = build_parser().parse_args(argv)
    if args.command == "sources" and args.source_command == "sync":
        sync_sources(load_manifest(args.manifest), args.raw_dir, args.force)
    elif args.command == "ingest":
        ingest_all(load_manifest(args.manifest), args.raw_dir, args.database)
    elif args.command == "build-static":
        build_static_site(args.database, args.output, args.template_dir, args.assets_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
