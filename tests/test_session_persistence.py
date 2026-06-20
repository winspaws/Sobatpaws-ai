"""Test session persistence across 'restarts' (new ConsultationService instances)."""
from __future__ import annotations

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add src to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Patch ARTIFACTS_DIR before any imports
tmpdir = tempfile.mkdtemp(prefix="sobatpaws_test_")
print(f"Using temp test directory: {tmpdir}")
os.makedirs(os.path.join(tmpdir, "sessions"), exist_ok=True)

# Now do the imports
from sobatpaws.ai.session_store import SessionStore, SESSIONS_DIR  # noqa: E402
from sobatpaws.ai.consultation import (  # noqa: E402
    ConsultationService,
    ConsultationState,
    ConsultationResult,
    ConsultationContext,
    IntakePayload,
)
from sobatpaws.ai.schemas import ConsultationChannel  # noqa: E402


def test_session_persistence():
    """Test that sessions persist across ConsultationService instances."""
    print("\n" + "="*60)
    print("TEST 1: Start consultation with first service instance")
    print("="*60)

    # Create a fresh session store in temp directory
    sessions_dir = Path(tmpdir) / "sessions"
    store1 = SessionStore(base_dir=sessions_dir, backend="jsonl")
    svc1 = ConsultationService(session_store=store1)

    # Start a consultation
    ctx = ConsultationContext(
        category_slug="cat",
        breed_slug="cat-persian",
        age_years=5,
        pet_id=123,
        vet_id=1,
    )
    payload = IntakePayload(
        text="Kucing saya muntah dan tidak mau makan, sudah 2 hari.",
        channel=ConsultationChannel.chat,
    )

    result1 = svc1.start(ctx, payload)
    cid = result1.consultation_id
    print(f"  Started consultation: {cid}")
    print(f"  Turn 1 intake symptoms: {[s.name_id for s in result1.intake.symptoms]}")

    # Get state from svc1
    state1 = svc1.get_state(cid)
    assert state1 is not None, "State should exist"
    assert len(state1.intakes) == 1, f"Should have 1 intake, got {len(state1.intakes)}"
    assert len(state1.suggestions) == 1, f"Should have 1 suggestion, got {len(state1.suggestions)}"
    print(f"  State from svc1: {len(state1.intakes)} intakes, {len(state1.suggestions)} suggestions")
    print(f"  Accumulated symptoms: {list(state1.accumulated_symptoms.keys())}")

    # Add a second turn
    print("\n" + "="*60)
    print("TEST 2: Add second turn with first service instance")
    print("="*60)

    payload2 = IntakePayload(
        text="Sekarang kucingnya lemas dan demam, suhu badannya tinggi.",
        channel=ConsultationChannel.chat,
    )
    result2 = svc1.add_turn(cid, payload2)
    print(f"  Turn 2 intake symptoms: {[s.name_id for s in result2.intake.symptoms]}")

    state1_updated = svc1.get_state(cid)
    assert state1_updated is not None
    assert len(state1_updated.intakes) == 2, f"Should have 2 intakes now, got {len(state1_updated.intakes)}"
    assert len(state1_updated.suggestions) == 2, f"Should have 2 suggestions now, got {len(state1_updated.suggestions)}"
    print(f"  Updated state from svc1: {len(state1_updated.intakes)} intakes, {len(state1_updated.suggestions)} suggestions")
    print(f"  Updated accumulated symptoms: {list(state1_updated.accumulated_symptoms.keys())}")

    # Now create a NEW ConsultationService (simulating server restart)
    print("\n" + "="*60)
    print("TEST 3: Create NEW service instance (simulate restart)")
    print("="*60)

    # Create fresh session store pointing to SAME directory
    # (it will rehydrate from disk)
    store2 = SessionStore(base_dir=sessions_dir, backend="jsonl")
    svc2 = ConsultationService(session_store=store2)

    # Try to get the state from the NEW service
    state2 = svc2.get_state(cid)
    assert state2 is not None, f"State should persist across service instances! Looking for {cid}"
    print(f"  State loaded from NEW service svc2: {len(state2.intakes)} intakes, {len(state2.suggestions)} suggestions")
    print(f"  Accumulated symptoms from svc2: {list(state2.accumulated_symptoms.keys())}")

    # Verify the state is complete
    assert len(state2.intakes) == 2, f"Expected 2 intakes, got {len(state2.intakes)}"
    assert len(state2.suggestions) == 2, f"Expected 2 suggestions, got {len(state2.suggestions)}"
    assert state2.consultation_id == cid, "Consultation ID should match"
    assert state2.context.category_slug == "cat", "Context should be preserved"
    assert state2.context.pet_id == 123, f"Pet ID should be preserved, got {state2.context.pet_id}"

    # Verify accumulated symptoms are the same
    assert set(state1_updated.accumulated_symptoms.keys()) == set(state2.accumulated_symptoms.keys()), \
        f"Accumulated symptoms should be identical. svc1={list(state1_updated.accumulated_symptoms.keys())}, svc2={list(state2.accumulated_symptoms.keys())}"

    print("  ✓ State preserved correctly across service instances!")

    # Now try to add a THIRD turn with the NEW service
    print("\n" + "="*60)
    print("TEST 4: Add third turn with NEW service instance")
    print("="*60)

    payload3 = IntakePayload(
        text="Kucingnya juga diare, fesesnya berwarna hitam.",
        channel=ConsultationChannel.chat,
    )
    result3 = svc2.add_turn(cid, payload3)
    print(f"  Turn 3 intake symptoms: {[s.name_id for s in result3.intake.symptoms]}")

    state2_updated = svc2.get_state(cid)
    assert state2_updated is not None
    assert len(state2_updated.intakes) == 3, f"Should have 3 intakes now, got {len(state2_updated.intakes)}"
    assert len(state2_updated.suggestions) == 3, f"Should have 3 suggestions now, got {len(state2_updated.suggestions)}"
    print(f"  Final state: {len(state2_updated.intakes)} intakes, {len(state2_updated.suggestions)} suggestions")
    print("  ✓ Third turn added successfully with rehydrated service!")

    print("\n" + "="*60)
    print("ALL TESTS PASSED!")
    print("="*60)
    print(f"\nTest data location: {tmpdir}")
    print(f"Sessions JSON files: {sessions_dir}")

    # List the session files
    if sessions_dir.exists():
        print("\nSession files created:")
        for f in sessions_dir.glob("*.json"):
            print(f"  - {f.name}")

    return True, tmpdir


if __name__ == "__main__":
    try:
        success, test_dir = test_session_persistence()
        print(f"\nTo inspect test data: ls -la {test_dir}")
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
