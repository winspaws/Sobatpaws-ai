#!/usr/bin/env python
"""Verify Notification Service imports work correctly."""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

print("=" * 60)
print("VERIFYING NOTIFICATION SERVICE IMPLEMENTATION")
print("=" * 60)

# 1. Test models
print("\n[1] Testing models...")
from ekosistem_satwa.emr.models import Notification
print(f"  ✓ Notification model: {Notification.__tablename__}")
notif_cols = [c.name for c in Notification.__table__.columns]
print(f"  ✓ Columns ({len(notif_cols)}): {', '.join(notif_cols[:10])}...")

# 2. Test schemas
print("\n[2] Testing schemas...")
from ekosistem_satwa.emr.schemas import (
    NotificationCreate,
    NotificationResponse,
    NotificationUpdate,
    NotificationConfirmRequest,
    NotificationListResponse,
)
print(f"  ✓ NotificationCreate fields: {list(NotificationCreate.model_fields.keys())}")
print(f"  ✓ NotificationResponse fields: {list(NotificationResponse.model_fields.keys())[:10]}...")

# 3. Test service
print("\n[3] Testing service methods...")
from ekosistem_satwa.emr.service import EMRService

service_methods = [
    m for m in dir(EMRService)
    if not m.startswith('_') and ('notification' in m.lower() or 'confirm' in m.lower() or 'reminder' in m.lower() or 'alert' in m.lower() or 'digest' in m.lower() or 'engagement' in m.lower())
]
print(f"  ✓ Service notification methods ({len(service_methods)}):")
for m in sorted(service_methods):
    print(f"    - {m}")

# 4. Test router import
print("\n[4] Testing router...")
from ekosistem_satwa.api.notifications_router import router
print(f"  ✓ Router prefix: {router.prefix}")
print(f"  ✓ Router tags: {router.tags}")
print(f"  ✓ Routes ({len(router.routes)}):")
for r in router.routes:
    if hasattr(r, 'methods') and r.methods:
        print(f"    - {list(r.methods)[0]} {r.path}")

# 5. Test deps
print("\n[5] Testing dependencies...")
from ekosistem_satwa.api.deps import get_emr_service
print(f"  ✓ get_emr_service available")

print("\n" + "=" * 60)
print("ALL CHECKS PASSED! ✓")
print("=" * 60)
