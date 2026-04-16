#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="${PROJECT_DIR}/portal-front"
PORT="${FRONTEND_PORT:-5173}"

echo "[frontend] project: ${FRONTEND_DIR}"
cd "${FRONTEND_DIR}"

PIDS="$(lsof -ti tcp:${PORT} 2>/dev/null || true)"
if [[ -z "${PIDS}" ]]; then
  PIDS="$(ss -lptn "sport = :${PORT}" 2>/dev/null | awk -F'pid=' 'NR>1{split($2,a,","); print a[1]}' | tr '\n' ' ' || true)"
fi

if [[ -n "${PIDS}" ]]; then
  echo "[frontend] found existing process on :${PORT}, killing: ${PIDS}"
  kill -9 ${PIDS} || true
  sleep 1
else
  echo "[frontend] no existing process on :${PORT}"
fi

echo "[frontend] starting..."
echo "[frontend] cmd: npm run dev"
exec npm run dev
