#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN_DIR="${VIRTUAL_ENV:-${ROOT_DIR}/.venv}/bin"
export DO_NOT_TRACK=1

if [[ ! -x "${BIN_DIR}/dbt" ]]; then
  echo "Ambiente ausente. Execute 'uv sync --all-groups --locked' primeiro." >&2
  exit 1
fi

"${BIN_DIR}/dbt" deps --project-dir "${ROOT_DIR}/analytics" --profiles-dir "${ROOT_DIR}/analytics"
"${BIN_DIR}/dbt" build --project-dir "${ROOT_DIR}/analytics" --profiles-dir "${ROOT_DIR}/analytics"
