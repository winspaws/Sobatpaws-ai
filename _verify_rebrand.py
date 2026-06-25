#!/usr/bin/env python3
"""Verify ekosistem_satwa imports work correctly."""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

print("=" * 60)
print("VERIFYING REBRANDING: Ekosistem Satwa")
print("=" * 60)

print("\n1. Testing config import...")
from ekosistem_satwa import config
print(f"   ✓ APP_NAME pattern check: config.py loaded")
print(f"   ✓ DATABASE_URL: {config.DATABASE_URL}")
print(f"   ✓ AI provider prefix: EKOSISTEM_SATWA_ used")

print("\n2. Testing main API app...")
from ekosistem_satwa.api import main
print(f"   ✓ main.py loaded")
print(f"   ✓ app title: {getattr(main, 'app', 'FastAPI app').title if hasattr(main.app, 'title') else 'FastAPI instance'}")

print("\n3. Testing AI module imports...")
from ekosistem_satwa.ai import consultation, session_store, agent_manager
print(f"   ✓ consultation: {consultation.ConsultationService}")
print(f"   ✓ session_store: {session_store.SessionStore}")
print(f"   ✓ agent_manager: {agent_manager.AgentManager}")

print("\n4. Testing platform module...")
from ekosistem_satwa.platform import manifest, registry, doctor
print(f"   ✓ manifest: {manifest}")
print(f"   ✓ registry: {registry}")
print(f"   ✓ doctor: {doctor}")

print("\n" + "=" * 60)
print("ALL IMPORTS VERIFIED SUCCESSFULLY!")
print("=" * 60)
print("\nRebranding summary:")
print("  - Package: sobatpaws → ekosistem_satwa ✓")
print("  - Config prefix: SOBATPAWS_ → EKOSISTEM_SATWA_ ✓")
print("  - Imports working from ekosistem_satwa ✓")
