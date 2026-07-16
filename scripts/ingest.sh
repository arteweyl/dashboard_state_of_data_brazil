#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN_DIR="${VIRTUAL_ENV:-${ROOT_DIR}/.venv}/bin"

if [[ ! -x "${BIN_DIR}/state-of-data" ]]; then
  echo "Ambiente ausente. Execute 'uv sync --all-groups --locked' primeiro." >&2
  exit 1
fi

"${BIN_DIR}/state-of-data" sources sync
"${BIN_DIR}/state-of-data" ingest
