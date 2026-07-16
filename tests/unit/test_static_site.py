from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import duckdb
import pytest

from state_of_data import static_site
from state_of_data.static_site import StaticSiteError, build_static_site


def create_public_database(path: Path) -> None:
    with duckdb.connect(path.as_posix()) as connection:
        connection.execute("CREATE SCHEMA analytics_marts")
        connection.execute(
            """
            CREATE TABLE analytics_marts.annual_summary (
                survey_year INTEGER, respondents INTEGER, average_age DOUBLE, satisfied_pct DOUBLE
            );
            INSERT INTO analytics_marts.annual_summary VALUES
                (2024, 100, 32.1, 70.0),
                (2025, 80, 33.2, 72.5)
            """
        )
        connection.execute(
            """
            CREATE TABLE analytics_marts.categorical_distribution (
                survey_year INTEGER, dimension VARCHAR, category VARCHAR, respondents INTEGER
            );
            INSERT INTO analytics_marts.categorical_distribution VALUES
                (2025, 'region', 'Sudeste', 40),
                (2025, 'region', 'Sul', 20),
                (2025, 'role', 'Analista de Dados', 30),
                (2025, 'seniority', 'Pleno', 24),
                (2025, 'gender', 'Feminino', 35)
            """
        )
        connection.execute(
            """
            CREATE TABLE analytics_marts.data_quality (
                survey_year INTEGER,
                question_key VARCHAR,
                question_label VARCHAR,
                question_status VARCHAR,
                total_respondents INTEGER,
                eligible_respondents INTEGER,
                answered_respondents INTEGER,
                missing_respondents INTEGER,
                not_applicable_respondents INTEGER,
                coverage_pct DOUBLE
            );
            INSERT INTO analytics_marts.data_quality VALUES
                (2025, 'role', 'Cargo', 'Disponível', 80, 70, 68, 2, 10, 97.1),
                (2025, 'race', 'Cor, raça ou etnia', 'Disponível', 80, 80, 80, 0, 0, 100.0)
            """
        )
        connection.execute(
            """
            CREATE TABLE analytics_marts.technology_cloud (
                survey_year INTEGER,
                question_context VARCHAR,
                cloud VARCHAR,
                respondents INTEGER
            );
            INSERT INTO analytics_marts.technology_cloud VALUES
                (2025, 'Uso no dia a dia', 'aws', 32),
                (2025, 'Uso no dia a dia', 'gcp', 22)
            """
        )


def test_build_static_site_exports_only_aggregate_snapshot(tmp_path: Path) -> None:
    database = tmp_path / "test.duckdb"
    output = tmp_path / "site"
    create_public_database(database)
    generated_at = datetime(2026, 7, 16, 12, 0, tzinfo=UTC)

    index = build_static_site(
        database,
        output,
        static_site.PROJECT_ROOT / "static/templates",
        static_site.PROJECT_ROOT / "static/assets",
        generated_at,
    )

    content = index.read_text(encoding="utf-8")
    snapshot = json.loads((output / "snapshot.json").read_text(encoding="utf-8"))
    assert "State of Data Brasil" in content
    assert "DASHBOARD DOS RESULTADOS DO STATE OF DATA" in content
    assert "desenvolvido com dados" in content
    assert "públicos das pesquisas State of Data Brazil" in content
    assert "Código e interface sob licença MIT" in content
    assert "Creative Commons nas edições de 2021 a 2023" in content
    assert "Analista de Dados" in content
    assert "Google Cloud" in content
    assert content.count("plotly-graph-div") == 3
    assert "Uso no dia a dia" in content
    assert "cada ano aparece em um gráfico separado" in content
    assert "respondent_key" not in content
    assert (output / "assets/styles.css").is_file()
    assert (output / "assets/app.js").is_file()
    assert (output / ".nojekyll").is_file()
    public_database = output / "data/state_of_data_public.duckdb"
    assert public_database.is_file()
    with duckdb.connect(public_database.as_posix(), read_only=True) as connection:
        tables = {
            tuple(row)
            for row in connection.execute(
                """
                SELECT table_schema, table_name
                FROM information_schema.tables
                WHERE table_schema IN ('analytics', 'metadata')
                """
            ).fetchall()
        }
        assert ("metadata", "sources") in tables
        assert ("analytics", "annual_summary") in tables
        assert not any(schema in {"raw", "analytics_staging"} for schema, _ in tables)
        assert connection.execute("SELECT count(*) FROM metadata.sources").fetchone() == (5,)
    assert snapshot["latest_survey_year"] == 2025
    assert snapshot["harmonized_responses"] == 180
    assert snapshot["privacy_threshold"] == 10
    assert snapshot["generated_at"] == "2026-07-16T12:00:00+00:00"
    assert snapshot["schema_version"] == 2
    assert snapshot["public_database"]["path"] == "data/state_of_data_public.duckdb"
    assert "Baixar DuckDB público" in content


def test_build_time_honors_source_date_epoch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "0")

    assert static_site._build_time() == datetime(1970, 1, 1, tzinfo=UTC)


def test_build_static_site_rejects_missing_or_empty_warehouse(tmp_path: Path) -> None:
    with pytest.raises(StaticSiteError, match="não encontrado"):
        build_static_site(
            tmp_path / "missing.duckdb",
            tmp_path / "site",
            static_site.PROJECT_ROOT / "static/templates",
            static_site.PROJECT_ROOT / "static/assets",
        )

    database = tmp_path / "empty.duckdb"
    create_public_database(database)
    with duckdb.connect(database.as_posix()) as connection:
        connection.execute("DELETE FROM analytics_marts.annual_summary")
    with pytest.raises(StaticSiteError, match="está vazio"):
        build_static_site(
            database,
            tmp_path / "site",
            static_site.PROJECT_ROOT / "static/templates",
            static_site.PROJECT_ROOT / "static/assets",
        )


def test_public_guards_reject_private_terms_and_unknown_marts(tmp_path: Path) -> None:
    with pytest.raises(StaticSiteError, match="Conteúdo proibido"):
        static_site._assert_public_output("SELECT respondent_key FROM anything")

    database = tmp_path / "test.duckdb"
    create_public_database(database)
    with (
        duckdb.connect(database.as_posix(), read_only=True) as connection,
        pytest.raises(StaticSiteError, match="não autorizado"),
    ):
        static_site._query_mart(connection, "private_responses")
