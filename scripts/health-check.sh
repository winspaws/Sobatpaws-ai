#!/usr/bin/env bash
# =============================================================================
#  health-check.sh — Sobatpaws / Ekosistem Satwa Health Check Monitor
#
#  Periodic health check untuk service production:
#    - GET /health endpoint → 200 OK
#    - Docker container status
#    - Log hasil ke file untuk debugging
#
#  Schedule: every 5 minutes via cron
#  Log: /var/log/sobatpaws-health.log
# =============================================================================
set -euo pipefail

LOG_FILE="/var/log/sobatpaws-health.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
ALERT_LOG="/var/log/sobatpaws-alert.log"

log() {
    echo "[${TIMESTAMP}] $*" >> "$LOG_FILE"
}

alert() {
    local level="$1"
    local message="$2"
    echo "[${TIMESTAMP}] [${level}] ${message}" | tee -a "$ALERT_LOG" >&2
}

# ── 1. Health endpoint check ────────────────────────────────────────────────
HEALTH_STATUS=$(curl -sf -o /dev/null -w "%{http_code}" http://localhost:8080/health 2>/dev/null || echo "000")

if [ "$HEALTH_STATUS" = "200" ]; then
    log "HEALTH_OK http=200"
else
    alert "CRITICAL" "Health endpoint returned HTTP ${HEALTH_STATUS} (expected 200)"
    # Coba detail
    HEALTH_BODY=$(curl -sf http://localhost:8080/health 2>/dev/null || echo "unreachable")
    alert "CRITICAL" "Health body: ${HEALTH_BODY}"
fi

# ── 2. Docker container status ──────────────────────────────────────────────
for CONTAINER in sobatpaws-api sobatpaws-db; do
    STATUS=$(docker inspect --format='{{.State.Status}}' "$CONTAINER" 2>/dev/null || echo "not_found")
    HEALTH=$(docker inspect --format='{{.State.Health.Status}}' "$CONTAINER" 2>/dev/null || echo "no_healthcheck")

    if [ "$STATUS" != "running" ]; then
        alert "CRITICAL" "Container ${CONTAINER} is ${STATUS} (not running)"
    elif [ "$HEALTH" != "healthy" ] && [ "$HEALTH" != "no_healthcheck" ]; then
        alert "WARNING" "Container ${CONTAINER} is running but health is ${HEALTH}"
    else
        log "CONTAINER_OK ${CONTAINER} status=${STATUS} health=${HEALTH}"
    fi
done

# ── 3. API status endpoint (detail) ─────────────────────────────────────────
API_STATUS=$(curl -sf http://localhost:8080/api/status 2>/dev/null || echo "{}")
LLM_AVAILABLE=$(echo "$API_STATUS" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('ai',{}).get('llm_available','unknown'))" 2>/dev/null || echo "parse_error")

if [ "$LLM_AVAILABLE" = "True" ] || [ "$LLM_AVAILABLE" = "true" ]; then
    log "LLM_OK llm_available=true"
else
    alert "WARNING" "LLM not available (llm_available=${LLM_AVAILABLE})"
fi

# ── 4. Disk usage check ─────────────────────────────────────────────────────
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | tr -d '%')
if [ "$DISK_USAGE" -gt 80 ]; then
    alert "WARNING" "Disk usage ${DISK_USAGE}% exceeds 80% threshold"
elif [ "$DISK_USAGE" -gt 90 ]; then
    alert "CRITICAL" "Disk usage ${DISK_USAGE}% exceeds 90% threshold"
else
    log "DISK_OK usage=${DISK_USAGE}%"
fi

# ── 5. Rotate logs (keep last 10000 lines) ──────────────────────────────────
if [ -f "$LOG_FILE" ] && [ "$(wc -l < "$LOG_FILE")" -gt 10000 ]; then
    tail -n 5000 "$LOG_FILE" > "${LOG_FILE}.tmp" && mv "${LOG_FILE}.tmp" "$LOG_FILE"
fi
if [ -f "$ALERT_LOG" ] && [ "$(wc -l < "$ALERT_LOG")" -gt 5000 ]; then
    tail -n 2000 "$ALERT_LOG" > "${ALERT_LOG}.tmp" && mv "${ALERT_LOG}.tmp" "$ALERT_LOG"
fi
