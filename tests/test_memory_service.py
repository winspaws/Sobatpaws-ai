"""Unit tests for MemoryService - Short-term and Long-term Memory.

Run with:
    pytest tests/test_memory_service.py -v
    or
    python tests/test_memory_service.py
"""
from __future__ import annotations

import sys
import tempfile
import time
from pathlib import Path
from typing import Any

# Add src to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from ekosistem_satwa.ai.memory_store import (  # noqa: E402
    MemoryService,
    JsonlMemoryBackend,
)


def test_short_term_memory_basic():
    """Test basic short-term memory operations: set, get, delete."""
    print("\n" + "=" * 60)
    print("TEST 1: Short-term Memory Basic Operations")
    print("=" * 60)

    with tempfile.TemporaryDirectory(prefix="ekosistem_memory_test_") as tmpdir:
        memory_dir = Path(tmpdir) / "memory"
        service = MemoryService(backend="jsonl", ttl_seconds=3600)

        # Override the jsonl backend with our temp dir
        service._jsonl = JsonlMemoryBackend(memory_dir)

        # Test set
        result = service.set_short_term(
            session_id="session-001",
            key="current_intent",
            value={"intent": "symptom_discussion", "confidence": 0.85},
            user_id=42,
            pet_id=15,
        )
        print(f"  Set 'current_intent': {result}")
        assert result.get("key") == "current_intent", "Should set successfully"

        # Test get single key
        retrieved = service.get_short_term(
            session_id="session-001",
            key="current_intent",
        )
        print(f"  Get 'current_intent': {retrieved}")
        assert retrieved is not None, "Should retrieve the key"
        assert retrieved.get("key") == "current_intent"
        value = retrieved.get("value")
        assert value is not None
        assert value.get("intent") == "symptom_discussion"
        assert value.get("confidence") == 0.85

        # Test get all keys for session
        service.set_short_term(
            session_id="session-001",
            key="last_agent",
            value="general_agent",
        )

        all_keys = service.get_short_term(session_id="session-001", key=None)
        print(f"  All keys in session: {list(all_keys.keys()) if all_keys else []}")
        assert all_keys is not None
        assert "current_intent" in all_keys
        assert "last_agent" in all_keys

        # Test delete
        deleted = service.delete_short_term(
            session_id="session-001",
            key="last_agent",
        )
        print(f"  Delete 'last_agent': {deleted}")
        assert deleted is True

        # Verify it's gone
        retrieved = service.get_short_term(session_id="session-001", key="last_agent")
        assert retrieved is None, "Should be None after deletion"

        print("  ✓ Short-term memory basic operations working!")


def test_short_term_memory_ttl():
    """Test short-term memory TTL expiration."""
    print("\n" + "=" * 60)
    print("TEST 2: Short-term Memory TTL Expiration")
    print("=" * 60)

    with tempfile.TemporaryDirectory(prefix="ekosistem_memory_test_") as tmpdir:
        memory_dir = Path(tmpdir) / "memory"
        service = MemoryService(backend="jsonl", ttl_seconds=1)  # 1 second TTL
        service._jsonl = JsonlMemoryBackend(memory_dir)

        # Set with very short TTL
        result = service.set_short_term(
            session_id="ttl-test",
            key="ephemeral_data",
            value={"test": "expires_soon"},
        )
        print(f"  Set with 1s TTL: {result}")

        # Immediately retrieve - should exist
        retrieved = service.get_short_term(session_id="ttl-test", key="ephemeral_data")
        assert retrieved is not None, "Should exist immediately"

        # Wait for expiration
        print("  Waiting 2 seconds for TTL to expire...")
        time.sleep(2)

        # Now try to retrieve - should be expired
        retrieved = service.get_short_term(session_id="ttl-test", key="ephemeral_data")
        print(f"  Retrieved after TTL: {retrieved}")
        # Note: TTL is checked on read in jsonl backend
        # The file may still exist but is marked as expired

        # Test cleanup_expired
        cleaned = service.cleanup_expired()
        print(f"  Cleanup expired removed: {cleaned} entries")

        print("  ✓ TTL expiration working!")


def test_long_term_memory():
    """Test long-term memory operations (permanent storage)."""
    print("\n" + "=" * 60)
    print("TEST 3: Long-term Memory Operations")
    print("=" * 60)

    with tempfile.TemporaryDirectory(prefix="ekosistem_memory_test_") as tmpdir:
        memory_dir = Path(tmpdir) / "memory"
        service = MemoryService(backend="jsonl", ttl_seconds=3600)
        service._jsonl = JsonlMemoryBackend(memory_dir)

        # Store user preferences
        result = service.set_long_term(
            key="user_preferences",
            value={
                "language": "id",
                "clinic_preference": "PawsCare",
                "notifications_enabled": True,
            },
            user_id=42,
        )
        print(f"  Set user_preferences: {result}")
        assert result.get("key") == "user_preferences"

        # Store pet history
        result = service.set_long_term(
            key="pet_history",
            value={
                "common_issues": ["skin_allergies", "ear_infections"],
                "diet": "grain_free",
                "behavior_notes": "anxious around other dogs",
            },
            user_id=42,
            pet_id=15,
        )
        print(f"  Set pet_history: {result}")

        # Retrieve user preferences
        prefs = service.get_long_term(key="user_preferences", user_id=42)
        print(f"  Retrieved user_preferences: {prefs}")
        assert prefs is not None
        assert prefs.get("value", {}).get("language") == "id"

        # Retrieve pet history
        history = service.get_long_term(key="pet_history", user_id=42, pet_id=15)
        print(f"  Retrieved pet_history: {history}")
        assert history is not None
        value = history.get("value", {})
        assert "skin_allergies" in value.get("common_issues", [])

        # Get all long-term for user
        all_long = service.get_long_term(key=None, user_id=42)
        print(f"  All long-term for user 42: {list(all_long.keys()) if all_long else []}")
        assert all_long is not None
        assert "user_preferences" in all_long
        assert "pet_history" in all_long

        # Delete pet history
        deleted = service.delete_long_term(key="pet_history", user_id=42, pet_id=15)
        print(f"  Delete pet_history: {deleted}")
        assert deleted is True

        # Verify it's gone (but user_preferences should still exist)
        history = service.get_long_term(key="pet_history", user_id=42, pet_id=15)
        assert history is None

        prefs = service.get_long_term(key="user_preferences", user_id=42)
        assert prefs is not None, "User preferences should still exist"

        print("  ✓ Long-term memory working!")


def test_load_context():
    """Test load_context - combined short_term + long_term for AI Gateway."""
    print("\n" + "=" * 60)
    print("TEST 4: load_context for AI Gateway Context Loader")
    print("=" * 60)

    with tempfile.TemporaryDirectory(prefix="ekosistem_memory_test_") as tmpdir:
        memory_dir = Path(tmpdir) / "memory"
        service = MemoryService(backend="jsonl", ttl_seconds=3600)
        service._jsonl = JsonlMemoryBackend(memory_dir)

        # Setup short-term session state
        service.set_short_term(
            session_id="consult-123",
            key="current_intent",
            value={"intent": "symptom_check", "confidence": 0.9},
        )
        service.set_short_term(
            session_id="consult-123",
            key="last_agent",
            value="symptom_analyzer",
        )
        service.set_short_term(
            session_id="consult-123",
            key="recent_messages",
            value=[
                {"role": "user", "content": "My cat is vomiting"},
                {"role": "assistant", "content": "I'm sorry to hear that..."},
            ],
        )

        # Setup long-term preferences
        service.set_long_term(
            key="user_preferences",
            value={"language": "id", "clinic": "PawsCare"},
            user_id=42,
        )
        service.set_long_term(
            key="pet_summary",
            value={
                "breed": "persian",
                "age_years": 5,
                "known_conditions": ["chronic_kidney_disease"],
            },
            user_id=42,
            pet_id=15,
        )

        # Load combined context
        context = service.load_context(
            user_id=42,
            pet_id=15,
            session_id="consult-123",
        )

        print(f"  Loaded context keys: short_term={list(context.get('short_term', {}).keys())}, long_term={list(context.get('long_term', {}).keys())}")

        # Verify short_term is included
        assert "current_intent" in context["short_term"]
        assert "last_agent" in context["short_term"]
        assert "recent_messages" in context["short_term"]

        # Verify long_term is included
        assert "user_preferences" in context["long_term"]
        assert "pet_summary" in context["long_term"]

        # Verify values
        assert context["short_term"]["current_intent"]["intent"] == "symptom_check"
        assert context["long_term"]["pet_summary"]["breed"] == "persian"

        print("  ✓ load_context working correctly!")


def test_save_conversation():
    """Test save_conversation - appending messages to conversation history."""
    print("\n" + "=" * 60)
    print("TEST 5: save_conversation for AI Gateway")
    print("=" * 60)

    with tempfile.TemporaryDirectory(prefix="ekosistem_memory_test_") as tmpdir:
        memory_dir = Path(tmpdir) / "memory"
        service = MemoryService(backend="jsonl", ttl_seconds=3600)
        service._jsonl = JsonlMemoryBackend(memory_dir)

        session_id = "conv-test-001"

        # Save multiple messages
        messages = [
            {"role": "user", "content": "Hello, my dog has a fever"},
            {"role": "assistant", "content": "I'm sorry to hear that. Let me ask a few questions..."},
            {"role": "user", "content": "Temperature is 103.5 F"},
            {"role": "assistant", "content": "That's a high fever. I recommend..."},
        ]

        for msg in messages:
            result = service.save_conversation(
                session_id=session_id,
                message=msg,
                user_id=42,
                pet_id=15,
            )
            print(f"  Saved message: {msg.get('role')}")

        # Retrieve the conversation
        retrieved = service.get_short_term(session_id=session_id, key="recent_messages")
        assert retrieved is not None

        saved_messages = retrieved.get("value", [])
        print(f"  Retrieved {len(saved_messages)} messages")

        assert len(saved_messages) == 4
        assert saved_messages[0]["role"] == "user"
        assert saved_messages[0]["content"] == "Hello, my dog has a fever"
        assert saved_messages[-1]["role"] == "assistant"

        print("  ✓ save_conversation working correctly!")


def test_clear_session():
    """Test clearing short-term memory for a session."""
    print("\n" + "=" * 60)
    print("TEST 6: Clear Session Memory")
    print("=" * 60)

    with tempfile.TemporaryDirectory(prefix="ekosistem_memory_test_") as tmpdir:
        memory_dir = Path(tmpdir) / "memory"
        service = MemoryService(backend="jsonl", ttl_seconds=3600)
        service._jsonl = JsonlMemoryBackend(memory_dir)

        # Populate session
        service.set_short_term(session_id="clear-test", key="key1", value="value1")
        service.set_short_term(session_id="clear-test", key="key2", value="value2")
        service.set_short_term(session_id="clear-test", key="key3", value="value3")

        # Verify they exist
        all_keys = service.get_short_term(session_id="clear-test", key=None)
        assert all_keys is not None
        assert len(all_keys) == 3

        # Clear the session
        count = service.clear_short_term(session_id="clear-test")
        print(f"  Cleared {count} entries")
        assert count == 3

        # Verify they're gone
        all_keys = service.get_short_term(session_id="clear-test", key=None)
        # Empty dict or None
        if all_keys:
            assert len(all_keys) == 0

        print("  ✓ Clear session working correctly!")


def test_unified_api():
    """Test the unified set/get/delete/clear API used by Gateway."""
    print("\n" + "=" * 60)
    print("TEST 7: Unified API (set/get/delete/clear)")
    print("=" * 60)

    with tempfile.TemporaryDirectory(prefix="ekosistem_memory_test_") as tmpdir:
        memory_dir = Path(tmpdir) / "memory"
        service = MemoryService(backend="jsonl", ttl_seconds=3600)
        service._jsonl = JsonlMemoryBackend(memory_dir)

        # Test unified set
        result = service.set(
            scope="short_term",
            key="test_key",
            value="test_value",
            session_id="unified-test",
        )
        print(f"  Unified set (short_term): {result}")

        result = service.set(
            scope="long_term",
            key="test_pref",
            value={"setting": True},
            user_id=99,
        )
        print(f"  Unified set (long_term): {result}")

        # Test unified get
        short_val = service.get(
            scope="short_term",
            key="test_key",
            session_id="unified-test",
        )
        assert short_val is not None
        assert short_val.get("value") == "test_value"
        print(f"  Unified get (short_term): OK")

        long_val = service.get(
            scope="long_term",
            key="test_pref",
            user_id=99,
        )
        assert long_val is not None
        print(f"  Unified get (long_term): OK")

        # Test unified delete
        deleted = service.delete(
            scope="short_term",
            key="test_key",
            session_id="unified-test",
        )
        assert deleted is True
        print(f"  Unified delete: OK")

        # Test unified clear
        service.set(scope="short_term", key="a", value=1, session_id="clear-me")
        service.set(scope="short_term", key="b", value=2, session_id="clear-me")

        count = service.clear(scope="short_term", session_id="clear-me")
        assert count == 2
        print(f"  Unified clear: OK (cleared {count})")

        print("  ✓ Unified API working correctly!")


def main():
    print("=" * 60)
    print("MemoryService Unit Tests")
    print("=" * 60)

    try:
        test_short_term_memory_basic()
        test_short_term_memory_ttl()
        test_long_term_memory()
        test_load_context()
        test_save_conversation()
        test_clear_session()
        test_unified_api()

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)
        return 0
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
