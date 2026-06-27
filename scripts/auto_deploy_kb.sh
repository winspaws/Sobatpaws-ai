#!/bin/bash
# Auto-deploy KB Expansion — menjalankan pipeline lengkap
# Dipanggil setiap 10 menit oleh cron

set -e
cd /home/ubuntu/sobatpaws

# 1. Generate diseases
echo "[$(date)] Starting KB expansion..."
PYTHONPATH=src python3 scripts/generate_diseases_massive.py >> /tmp/kb_expansion.log 2>&1
echo "[$(date)] Generation done" >> /tmp/kb_expansion.log

# 2. Sync catalogs
python3 scripts/sync_catalogs_from_kb.py >> /tmp/kb_expansion.log 2>&1
echo "[$(date)] Sync done" >> /tmp/kb_expansion.log

# 3. Count new total
COUNT=$(python3 -c "import json,glob;print(sum(len(json.load(open(f))['diseases']) for f in glob.glob('data/clinical/diseases_*.json')))")
echo "[$(date)] Total: $COUNT diseases" >> /tmp/kb_expansion.log

# 4. Build & deploy
docker compose -f docker-compose.prod.yml build api >> /tmp/kb_expansion.log 2>&1
docker compose -f docker-compose.prod.yml up -d api >> /tmp/kb_expansion.log 2>&1
echo "[$(date)] Deploy done" >> /tmp/kb_expansion.log

# 5. Git commit & push
git add data/clinical/ scripts/
git commit -m "kb: Auto-expansion - $(date +%Y-%m-%d_%H:%M) - $COUNT diseases" 2>/dev/null || true
bash scripts/git_push.sh "kb: Auto-expansion"

echo "[$(date)] === Complete: $COUNT diseases ===" >> /tmp/kb_expansion.log
