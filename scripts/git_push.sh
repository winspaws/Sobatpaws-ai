#!/bin/bash
# Auto-push helper — retry sampai berhasil, tanpa perlu intervensi
# Usage: ./scripts/git_push.sh "commit message"

set -e
cd /home/ubuntu/sobatpaws

MSG="${1:-auto: update $(date +%Y-%m-%d_%H:%M)}"

# Add everything
git add -A 2>/dev/null

# Commit (jika ada perubahan)
if git diff --cached --quiet; then
    echo "No changes to commit"
    exit 0
fi

git commit -m "$MSG"

# Push with retry (max 5 kali)
for i in 1 2 3 4 5; do
    if git push origin main 2>&1; then
        echo "Push successful (attempt $i)"
        exit 0
    fi
    echo "Push failed (attempt $i), retrying in 5s..."
    sleep 5
done

echo "Push failed after 5 attempts" >&2
exit 1
