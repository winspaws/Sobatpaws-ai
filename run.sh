#!/usr/bin/env bash
# Jalankan API + Dashboard Sobatpaws.
# Pakai:  ./run.sh           (default port 8000)
#         ./run.sh 8080      (port lain)
set -e

cd "$(dirname "$0")"

PORT="${1:-8000}"
PY=".venv/bin/python"
[ -x "$PY" ] || PY="python3"

export PYTHONPATH=src

echo "🐾 Sobatpaws — menjalankan API + Dashboard"
echo "   Dashboard : http://localhost:${PORT}/"
echo "   API docs  : http://localhost:${PORT}/docs"
echo "   (Ctrl+C untuk berhenti)"
echo

exec "$PY" -m uvicorn sobatpaws.api.main:app --host 0.0.0.0 --port "$PORT" --app-dir src
