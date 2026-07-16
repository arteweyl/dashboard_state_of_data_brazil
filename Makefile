.PHONY: setup ingest transform static test lint format typecheck audit quality dashboard clean

setup:
	uv sync --all-groups

ingest:
	./scripts/ingest.sh

transform:
	./scripts/transform.sh

static:
	./scripts/build_site.sh

test:
	uv run pytest --cov=state_of_data --cov-report=term-missing

lint:
	uv run ruff check .

format:
	uv run ruff format .
	uv run ruff check --fix .

typecheck:
	uv run mypy

audit:
	uv run pip-audit

quality: lint typecheck test
	uv run dbt parse --project-dir analytics --profiles-dir analytics

dashboard:
	uv run streamlit run app/main.py

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov analytics/target analytics/logs
