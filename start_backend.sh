sh #!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${BACKEND_PORT:-8080}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "[backend] project: ${PROJECT_DIR}"
cd "${PROJECT_DIR}"

PIDS="$(lsof -ti tcp:${PORT} 2>/dev/null || true)"
if [[ -z "${PIDS}" ]]; then
  PIDS="$(ss -lptn "sport = :${PORT}" 2>/dev/null | awk -F'pid=' 'NR>1{split($2,a,","); print a[1]}' | tr '\n' ' ' || true)"
fi

if [[ -n "${PIDS}" ]]; then
  echo "[backend] found existing process on :${PORT}, killing: ${PIDS}"
  kill -9 ${PIDS} || true
  sleep 1
else
  echo "[backend] no existing process on :${PORT}"
fi

export PYTHONPATH=src
echo "[backend] starting..."
echo "[backend] cmd: ${PYTHON_BIN} -c \"from harness_app.access.api_gateway.app import run; run()\""
exec "${PYTHON_BIN}" -c "from harness_app.access.api_gateway.app import run; run()"
