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

echo "🐾 Ekosistem Satwa / Sobatpaws — menjalankan API + Dashboard"
echo "   Dashboard      : http://localhost:${PORT}/"
echo "   Admin          : http://localhost:${PORT}/admin.html"
echo "   Telekonsultasi : http://localhost:${PORT}/telekonsultasi.html"
echo "   Pawnia AI      : POST http://localhost:${PORT}/api/v1/ai/chat"
echo "   API docs       : http://localhost:${PORT}/docs"
echo "   (Ctrl+C untuk berhenti)"
echo

exec "$PY" -m uvicorn ekosistem_satwa.api.main:app --host 0.0.0.0 --port "$PORT" --app-dir src
