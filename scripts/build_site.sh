#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN_DIR="${VIRTUAL_ENV:-${ROOT_DIR}/.venv}/bin"
SITE_DIR="${ROOT_DIR}/site"

if [[ ! -x "${BIN_DIR}/state-of-data" ]]; then
  echo "Ambiente ausente. Execute 'uv sync --all-groups --locked' primeiro." >&2
  exit 1
fi

"${BIN_DIR}/state-of-data" build-static --output "${SITE_DIR}"
"${BIN_DIR}/python" -m json.tool "${SITE_DIR}/snapshot.json" >/dev/null
test -s "${SITE_DIR}/index.html"
test -s "${SITE_DIR}/data/state_of_data_public.duckdb"
