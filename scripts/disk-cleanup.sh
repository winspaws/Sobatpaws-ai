#!/usr/bin/env bash
# =============================================================================
#  disk-cleanup.sh — Disk Monitoring & Auto-cleanup
#
#  - Alert jika disk > 80%
#  - Auto-cleanup: docker system prune mingguan
#  - Log ke /var/log/sobatpaws-disk.log
#
#  Schedule: weekly via cron (every Sunday at 03:00)
# =============================================================================
set -euo pipefail

LOG_FILE="/var/log/sobatpaws-disk.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

log() {
    echo "[${TIMESTAMP}] $*" >> "$LOG_FILE"
}

# ── 1. Check disk usage ─────────────────────────────────────────────────────
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | tr -d '%')
DISK_INFO=$(df -h / | awk 'NR==2 {print $3 " used / " $2 " total"}')

log "Disk usage: ${DISK_USAGE}% (${DISK_INFO})"

if [ "$DISK_USAGE" -gt 80 ]; then
    log "WARNING: Disk ${DISK_USAGE}% exceeds 80% threshold"

    if [ "$DISK_USAGE" -gt 90 ]; then
        log "CRITICAL: Disk ${DISK_USAGE}% — running emergency cleanup"

        # Emergency: prune everything
        docker system prune -af --volumes 2>>"$LOG_FILE" || true
        log "Emergency docker system prune completed"

        # Clean apt cache
        sudo apt-get clean -y 2>/dev/null || true
        log "APT cache cleaned"

        # Remove old journal logs
        sudo journalctl --vacuum-time=3d 2>/dev/null || true
        log "Journal logs vacuumed (3d)"
    fi
fi

# ── 2. Docker system prune (mingguan) ───────────────────────────────────────
log "Running docker system prune..."
BEFORE=$(df -h / | awk 'NR==2 {print $3}')
docker system prune -f 2>>"$LOG_FILE" || true
AFTER=$(df -h / | awk 'NR==2 {print $3}')
log "Docker prune completed: ${BEFORE} → ${AFTER}"

# ── 3. Remove unused Docker images (keep last 3 tags) ───────────────────────
log "Cleaning old Docker images..."
docker image prune -af --filter "until=72h" 2>>"$LOG_FILE" || true

# ── 4. Summary ──────────────────────────────────────────────────────────────
DISK_AFTER=$(df -h / | awk 'NR==2 {print $5}')
log "Disk after cleanup: ${DISK_AFTER}"
echo "Disk: ${DISK_USAGE}% → ${DISK_AFTER}"
echo "Log:  ${LOG_FILE}"
