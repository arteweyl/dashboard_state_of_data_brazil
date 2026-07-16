"""Build a privacy-safe, pre-rendered site from aggregate DuckDB marts."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import duckdb
import plotly.graph_objects as go
import plotly.io as pio
import structlog
from jinja2 import Environment, FileSystemLoader, select_autoescape

from state_of_data.config import PROJECT_ROOT, Dataset, load_manifest

LOGGER = structlog.get_logger(__name__)
MART_SCHEMA = "analytics_marts"
PUBLIC_MARTS = (
    "annual_summary",
    "categorical_distribution",
    "data_quality",
    "technology_cloud",
)
FORBIDDEN_OUTPUT_TERMS = (
    "respondent_key",
    "q_0_a_token",
    "p0_id",
    "raw.survey_",
)
PUBLIC_DATABASE_NAME = "state_of_data_public.duckdb"
COLORS = ("#8B5CF6", "#22D3EE", "#F472B6", "#FBBF24", "#34D399")
CLOUD_LABELS = {
    "aws": "AWS",
    "gcp": "Google Cloud",
    "azure": "Microsoft Azure",
    "oracle_cloud": "Oracle Cloud",
    "ibm": "IBM Cloud",
    "on_premise": "On-premise",
    "private_cloud": "Cloud própria",
}


class StaticSiteError(RuntimeError):
    """Raised when a public snapshot cannot be built safely."""


def _query_mart(connection: duckdb.DuckDBPyConnection, table: str) -> list[dict[str, Any]]:
    if table not in PUBLIC_MARTS:
        raise StaticSiteError(f"Mart não autorizado para exportação: {table}")
    cursor = connection.execute(f"SELECT * FROM {MART_SCHEMA}.{table}")
    columns = [description[0] for description in cursor.description]
    return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]


def _source_manifest_digest() -> str:
    manifest = PROJECT_ROOT / "data/raw/manifest.json"
    return hashlib.sha256(manifest.read_bytes()).hexdigest()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sql_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def build_public_database(warehouse: Path, output: Path, sources: Sequence[Dataset]) -> Path:
    """Copy only approved aggregate marts and source provenance to a public DuckDB."""

    if warehouse.resolve() == output.resolve():
        raise StaticSiteError("O DuckDB público deve ser diferente do warehouse interno.")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.unlink(missing_ok=True)
    warehouse_sql = _sql_string(warehouse.resolve().as_posix())

    try:
        with duckdb.connect(output.as_posix()) as connection:
            connection.execute(f"ATTACH DATABASE {warehouse_sql} AS warehouse (READ_ONLY)")
            connection.execute("CREATE SCHEMA analytics")
            for mart in PUBLIC_MARTS:
                connection.execute(
                    f"CREATE TABLE analytics.{mart} AS SELECT * FROM warehouse.{MART_SCHEMA}.{mart}"
                )
            connection.execute("DETACH DATABASE warehouse")
            connection.execute("CREATE SCHEMA metadata")
            connection.execute(
                """
                CREATE TABLE metadata.sources (
                    survey_year INTEGER,
                    kaggle_ref VARCHAR,
                    source_url VARCHAR,
                    source_file VARCHAR,
                    source_sha256 VARCHAR,
                    source_license VARCHAR
                )
                """
            )
            connection.executemany(
                "INSERT INTO metadata.sources VALUES (?, ?, ?, ?, ?, ?)",
                [
                    (
                        source.year,
                        source.kaggle_ref,
                        source.source_url,
                        source.file,
                        source.sha256,
                        source.license,
                    )
                    for source in sources
                ],
            )
            connection.execute(
                """
                CREATE TABLE metadata.release AS
                SELECT
                    1 AS schema_version,
                    10 AS privacy_threshold,
                    'Somente resultados agregados; sem respostas individuais.' AS privacy_scope,
                    'As licenças das fontes estão em metadata.sources.' AS license_notice
                """
            )

            tables = {
                str(row[0])
                for row in connection.execute(
                    """
                    SELECT table_schema || '.' || table_name
                    FROM information_schema.tables
                    WHERE table_schema IN ('analytics', 'metadata')
                    """
                ).fetchall()
            }
            expected = {f"analytics.{mart}" for mart in PUBLIC_MARTS} | {
                "metadata.sources",
                "metadata.release",
            }
            if tables != expected:
                raise StaticSiteError("O DuckDB público contém uma coleção inesperada de tabelas.")

            columns = [
                str(row[0]).lower()
                for row in connection.execute(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema IN ('analytics', 'metadata')
                    """
                ).fetchall()
            ]
            forbidden_columns = [
                column
                for column in columns
                if column in {"respondent_key", "q_0_a_token", "p0_id", "response_id"}
            ]
            if forbidden_columns:
                raise StaticSiteError(
                    f"Colunas proibidas no DuckDB público: {', '.join(forbidden_columns)}"
                )
            connection.execute("CHECKPOINT")
    except Exception:
        output.unlink(missing_ok=True)
        raise

    return output


def _build_time() -> datetime:
    source_date_epoch = os.getenv("SOURCE_DATE_EPOCH")
    if source_date_epoch:
        return datetime.fromtimestamp(int(source_date_epoch), tz=UTC)
    return datetime.now(UTC)


def _ranking(
    rows: Sequence[dict[str, Any]], dimension: str, year: int, limit: int = 10
) -> list[dict[str, Any]]:
    selected = [
        row for row in rows if row["dimension"] == dimension and int(row["survey_year"]) == year
    ]
    selected.sort(key=lambda row: int(row["respondents"]), reverse=True)
    selected = selected[:limit]
    maximum = max((int(row["respondents"]) for row in selected), default=1)
    return [
        {
            "label": str(row["category"]),
            "respondents": int(row["respondents"]),
            "width": round(100 * int(row["respondents"]) / maximum, 1),
        }
        for row in selected
    ]


def _line_chart(
    rows: Sequence[dict[str, Any]],
    value: str,
    title: str,
    suffix: str = "",
    include_plotly: bool = False,
) -> str:
    ordered = sorted(rows, key=lambda row: int(row["survey_year"]))
    figure = go.Figure(
        go.Scatter(
            x=[int(row["survey_year"]) for row in ordered],
            y=[float(row[value]) for row in ordered],
            mode="lines+markers",
            line={"color": COLORS[0], "width": 3},
            marker={"size": 9, "color": COLORS[1]},
            hovertemplate=f"%{{x}}: %{{y:,.1f}}{suffix}<extra></extra>",
        )
    )
    figure.update_layout(
        title=title,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#F5F3FF"},
        margin={"l": 45, "r": 20, "t": 55, "b": 40},
        xaxis={"dtick": 1, "gridcolor": "#292D50"},
        yaxis={"ticksuffix": suffix, "gridcolor": "#292D50"},
        height=360,
    )
    chart_html: Any = pio.to_html(
        figure,
        full_html=False,
        include_plotlyjs="cdn" if include_plotly else False,
        config={"displayModeBar": False, "responsive": True},
    )
    return str(chart_html)


def _cloud_chart(rows: Sequence[dict[str, Any]], year: int) -> dict[str, str | int]:
    """Build one horizontal cloud ranking while preserving its survey context."""

    selected = [row for row in rows if int(row["survey_year"]) == year]
    selected.sort(key=lambda row: int(row["respondents"]))
    context = str(selected[0]["question_context"]) if selected else "Sem pergunta comparável"
    labels = [CLOUD_LABELS.get(str(row["cloud"]), str(row["cloud"])) for row in selected]
    counts = [int(row["respondents"]) for row in selected]
    figure = go.Figure(
        go.Bar(
            x=counts,
            y=labels,
            orientation="h",
            marker={
                "color": [COLORS[index % len(COLORS)] for index in range(len(selected))],
                "line": {"color": "rgba(245, 243, 255, 0.13)", "width": 1},
            },
            text=[f"{count:,}".replace(",", ".") for count in counts],
            textposition="outside",
            cliponaxis=False,
            hovertemplate="%{y}: %{x:,.0f} menções<extra></extra>",
        )
    )
    figure.update_layout(
        title=f"{year} · {context}",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#F5F3FF"},
        margin={"l": 110, "r": 55, "t": 60, "b": 40},
        xaxis={"title": "Menções", "gridcolor": "#292D50", "rangemode": "tozero"},
        yaxis={"title": ""},
        height=390,
        showlegend=False,
    )
    chart_html: Any = pio.to_html(
        figure,
        full_html=False,
        include_plotlyjs=False,
        config={"displayModeBar": False, "responsive": True},
    )
    return {"year": year, "context": context, "html": str(chart_html)}


def _assert_public_output(content: str) -> None:
    lowered = content.lower()
    found = [term for term in FORBIDDEN_OUTPUT_TERMS if term in lowered]
    if found:
        raise StaticSiteError(f"Conteúdo proibido no site estático: {', '.join(found)}")


def build_static_site(
    database: Path,
    output: Path,
    template_dir: Path,
    assets_dir: Path,
    generated_at: datetime | None = None,
) -> Path:
    """Render aggregate marts to a deployable static directory."""

    if not database.is_file():
        raise StaticSiteError(f"Warehouse não encontrado: {database}")
    with duckdb.connect(database.as_posix(), read_only=True) as connection:
        annual = _query_mart(connection, "annual_summary")
        distributions = _query_mart(connection, "categorical_distribution")
        quality = _query_mart(connection, "data_quality")
        cloud = _query_mart(connection, "technology_cloud")

    if not annual:
        raise StaticSiteError("O mart annual_summary está vazio.")

    latest_year = max(int(row["survey_year"]) for row in annual)
    latest = next(row for row in annual if int(row["survey_year"]) == latest_year)
    quality_latest = [row for row in quality if int(row["survey_year"]) == latest_year]
    quality_latest.sort(
        key=lambda row: (
            row["coverage_pct"] is None,
            -(float(row["coverage_pct"]) if row["coverage_pct"] is not None else 0),
        )
    )
    cloud_charts = [
        _cloud_chart(cloud, year) for year in sorted({int(row["survey_year"]) for row in cloud})
    ]

    output.mkdir(parents=True, exist_ok=True)
    public_database = build_public_database(
        database,
        output / "data" / PUBLIC_DATABASE_NAME,
        load_manifest(),
    )
    public_database_size = public_database.stat().st_size

    build_time = generated_at or _build_time()
    environment = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(("html", "xml")),
        keep_trailing_newline=True,
    )
    template = environment.get_template("index.html.j2")
    content = template.render(
        generated_at=build_time.astimezone(UTC).strftime("%d/%m/%Y às %H:%M UTC"),
        latest_year=latest_year,
        latest=latest,
        total_responses=sum(int(row["respondents"]) for row in annual),
        participation_chart=_line_chart(
            annual, "respondents", "Participação por edição", include_plotly=True
        ),
        satisfaction_chart=_line_chart(
            annual, "satisfied_pct", "Satisfação profissional", suffix="%"
        ),
        rankings={
            "region": _ranking(distributions, "region", latest_year, 8),
            "age": _ranking(distributions, "age_group", latest_year),
            "gender": _ranking(distributions, "gender", latest_year),
            "race": _ranking(distributions, "race_ethnicity", latest_year),
            "education": _ranking(distributions, "education_level", latest_year),
            "role": _ranking(distributions, "role", latest_year, 12),
            "seniority": _ranking(distributions, "seniority", latest_year),
            "salary": _ranking(distributions, "salary_range", latest_year, 14),
            "industry": _ranking(distributions, "industry", latest_year, 12),
            "employment": _ranking(distributions, "employment_status", latest_year, 12),
            "current_work": _ranking(distributions, "current_work_model", latest_year),
            "ideal_work": _ranking(distributions, "ideal_work_model", latest_year),
        },
        cloud_charts=cloud_charts,
        quality=quality_latest,
        public_database_path=f"data/{PUBLIC_DATABASE_NAME}",
        public_database_size_mb=public_database_size / (1024 * 1024),
    )
    _assert_public_output(content)

    output_assets = output / "assets"
    if output_assets.exists():
        shutil.rmtree(output_assets)
    shutil.copytree(assets_dir, output_assets)
    index_path = output / "index.html"
    index_path.write_text(content, encoding="utf-8")

    snapshot = {
        "schema_version": 2,
        "generated_at": build_time.astimezone(UTC).isoformat(),
        "latest_survey_year": latest_year,
        "survey_years": sorted(int(row["survey_year"]) for row in annual),
        "harmonized_responses": sum(int(row["respondents"]) for row in annual),
        "privacy_threshold": 10,
        "source_manifest_sha256": _source_manifest_digest(),
        "exported_marts": list(PUBLIC_MARTS),
        "public_database": {
            "path": f"data/{PUBLIC_DATABASE_NAME}",
            "bytes": public_database_size,
            "sha256": _sha256(public_database),
        },
    }
    (output / "snapshot.json").write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output / ".nojekyll").touch()
    LOGGER.info("static_site_built", output=str(index_path), latest_year=latest_year)
    return index_path
