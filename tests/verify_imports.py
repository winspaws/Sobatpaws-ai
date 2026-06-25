#!/usr/bin/env python3
"""Verify all imports work correctly."""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

print("Testing imports...")

from ekosistem_satwa.ai.consultation import (
    ConsultationService,
    ConsultationState,
    _state_to_dict,
    _dict_to_state,
)
print("  ✓ ekosistem_satwa.ai.consultation")

from ekosistem_satwa.ai.session_store import SessionStore, get_session_store, SESSIONS_DIR
print("  ✓ ekosistem_satwa.ai.session_store")

from ekosistem_satwa.ai.agent_manager import AgentManager, get_agent_manager
print("  ✓ ekosistem_satwa.ai.agent_manager")

from ekosistem_satwa.api.deps import get_service, get_agent
print("  ✓ ekosistem_satwa.api.deps")

from ekosistem_satwa.config import SESSION_STORE_BACKEND
print("  ✓ ekosistem_satwa.config")

print("\nAll imports successful!")
print(f"\nSESSION_STORE_BACKEND = {SESSION_STORE_BACKEND}")
print(f"SESSIONS_DIR = {SESSIONS_DIR}")

# Test get_session_store
store = get_session_store()
print(f"\nSessionStore info:")
print(f"  backend: {store.backend}")
print(f"  pg_available: {store.pg_available}")
print(f"  cache_count: {len(store._cache)}")
print(f"  backend_info: {store.backend_info()}")
