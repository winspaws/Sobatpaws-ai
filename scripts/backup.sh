#!/usr/bin/env bash
# =============================================================================
#  backup.sh — Sobatpaws / Ekosistem Satwa Daily Backup
#
#  Backup semua data penting:
#    - artifacts/ (ML models, learning data, sessions) — dari Docker volume
#    - data/ (clinical JSON, breeds)
#    - .env dan config files
#    - PostgreSQL database dump
#
#  Schedule: daily via cron
#  Retention: 7 hari
#  Destinasi: /backups/
# =============================================================================
set -euo pipefail

BACKUP_DIR="/backups"
RETENTION_DAYS=7
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="${BACKUP_DIR}/sobatpaws_${TIMESTAMP}"
PROJECT_DIR="/home/ubuntu/sobatpaws"
LOG_FILE="${BACKUP_DIR}/backup.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

mkdir -p "$BACKUP_PATH"
log "=== Starting backup: ${BACKUP_PATH} ==="

# ── 1. PostgreSQL dump ──────────────────────────────────────────────────────
log "Backing up PostgreSQL..."
if docker exec sobatpaws-db pg_dump -U sobatpaws sobatpaws > "${BACKUP_PATH}/postgres.sql" 2>>"$LOG_FILE"; then
    gzip "${BACKUP_PATH}/postgres.sql"
    log "  ✓ PostgreSQL dump: ${BACKUP_PATH}/postgres.sql.gz"
else
    log "  ✗ PostgreSQL dump FAILED"
fi

# ── 2. Artifacts (ML models, learning data, sessions) from Docker volume ────
log "Backing up artifacts volume..."
if docker run --rm \
    -v sobatpaws_sobatpaws_artifacts:/source \
    -v "${BACKUP_PATH}:/dest" \
    alpine:3.19 \
    tar czf /dest/artifacts.tar.gz -C /source . 2>>"$LOG_FILE"; then
    log "  ✓ Artifacts: ${BACKUP_PATH}/artifacts.tar.gz"
else
    log "  ✗ Artifacts backup FAILED"
fi

# ── 3. Data directory (clinical JSON, breeds) ───────────────────────────────
log "Backing up data/ directory..."
if tar czf "${BACKUP_PATH}/data.tar.gz" -C "$PROJECT_DIR" data/ 2>>"$LOG_FILE"; then
    log "  ✓ Data: ${BACKUP_PATH}/data.tar.gz"
else
    log "  ✗ Data backup FAILED"
fi

# ── 4. .env dan config files ────────────────────────────────────────────────
log "Backing up config files..."
CONFIG_FILES=(
    ".env"
    ".env.production"
    "docker-compose.prod.yml"
    "docker-compose.yml"
    "requirements.txt"
)
for f in "${CONFIG_FILES[@]}"; do
    if [ -f "${PROJECT_DIR}/${f}" ]; then
        cp "${PROJECT_DIR}/${f}" "${BACKUP_PATH}/${f}"
        log "  ✓ ${f}"
    else
        log "  - ${f} not found, skipped"
    fi
done

# ── 5. Crontab backup ───────────────────────────────────────────────────────
log "Backing up crontab..."
crontab -l > "${BACKUP_PATH}/crontab.txt" 2>/dev/null || true
log "  ✓ crontab saved"

# ── 6. Docker info snapshot ─────────────────────────────────────────────────
log "Backing up Docker info..."
{
    echo "=== Docker PS ==="
    docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
    echo ""
    echo "=== Docker Images ==="
    docker images --format 'table {{.Repository}}\t{{.Tag}}\t{{.Size}}'
    echo ""
    echo "=== Disk Usage ==="
    df -h /
} > "${BACKUP_PATH}/docker-info.txt"
log "  ✓ Docker info saved"

# ── 7. Create manifest ──────────────────────────────────────────────────────
{
    echo "Backup timestamp: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
    echo "Host: $(hostname)"
    echo "Files:"
    ls -lh "${BACKUP_PATH}/"
} > "${BACKUP_PATH}/MANIFEST.txt"

# ── 8. Cleanup old backups (retensi 7 hari) ─────────────────────────────────
log "Cleaning backups older than ${RETENTION_DAYS} days..."
find "$BACKUP_DIR" -maxdepth 1 -type d -name "sobatpaws_*" -mtime "+${RETENTION_DAYS}" -exec rm -rf {} \; -print | while read -r old; do
    log "  🗑 Removed old backup: ${old}"
done

# ── Summary ─────────────────────────────────────────────────────────────────
BACKUP_SIZE=$(du -sh "${BACKUP_PATH}" | cut -f1)
log "=== Backup complete: ${BACKUP_PATH} (${BACKUP_SIZE}) ==="
echo ""
echo "Backup: ${BACKUP_PATH}"
echo "Size:   ${BACKUP_SIZE}"
echo "Log:    ${LOG_FILE}"
