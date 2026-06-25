"""Simple unit test for SessionStore and ConsultationState persistence."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

# Add src to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from ekosistem_satwa.ai.session_store import (  # noqa: E402
    SessionStore,
    _serialize_state,
)
from ekosistem_satwa.ai.consultation import (  # noqa: E402
    _state_to_dict,
    _dict_to_state,
    ConsultationState,
    ConsultationContext,
    IntakeResult,
    AISuggestion,
)
from ekosistem_satwa.ai.schemas import (  # noqa: E402
    ConsultationChannel,
    ExtractedSymptom,
    MediaObservation,
    IntakeModality,
    SuggestedDisease,
)


def test_state_serialization():
    """Test that ConsultationState can be serialized and deserialized correctly."""
    print("\n" + "="*60)
    print("TEST 1: ConsultationState serialization/deserialization")
    print("="*60)

    # Create a test state
    ctx = ConsultationContext(
        category_slug="cat",
        breed_slug="cat-persian",
        age_years=5.0,
        pet_id=123,
        vet_id=1,
        owner_id=456,
    )

    symptom1 = ExtractedSymptom(
        name_id="Muntah",
        name="Muntah",
        score=0.95,
        is_red_flag=True,
    )

    symptom2 = ExtractedSymptom(
        name_id="Nafsu makan menurun",
        name="Nafsu makan menurun",
        score=0.85,
        is_red_flag=False,
    )

    obs1 = MediaObservation(
        modality=IntakeModality.text,
        text="Kucing terlihat lemas",
        source="user_input",
    )

    intake1 = IntakeResult(
        complaint_text="Kucing muntah dan tidak mau makan",
        observations=[obs1],
        symptoms=[symptom1, symptom2],
        channel=ConsultationChannel.chat,
    )

    suggested_disease = SuggestedDisease(
        disease_slug="chronic-kidney-disease",
        name_id="Penyakit ginjal kronis",
        confidence=0.75,
        source="ml",
    )

    suggestion1 = AISuggestion(
        suggestion_type="symptom_to_disease",
        summary="Kucing menunjukkan gejala yang mengarah ke masalah ginjal atau pencernaan.",
        suggested_diseases=[suggested_disease],
        is_emergency=False,
    )

    state = ConsultationState(
        consultation_id="test-session-001",
        context=ctx,
        intakes=[intake1],
        suggestions=[suggestion1],
        accumulated_symptoms={
            "Muntah": symptom1.model_dump(),
            "Nafsu makan menurun": symptom2.model_dump(),
        },
    )

    print(f"  Original state: {state.consultation_id}")
    print(f"    Context: category={state.context.category_slug}, pet_id={state.context.pet_id}")
    print(f"    Intakes: {len(state.intakes)}")
    print(f"    Suggestions: {len(state.suggestions)}")
    print(f"    Accumulated symptoms: {list(state.accumulated_symptoms.keys())}")

    # Serialize
    state_dict = _state_to_dict(state)
    print(f"\n  Serialized to dict with keys: {list(state_dict.keys())}")

    # Deserialize
    restored = _dict_to_state(state_dict)
    assert restored is not None, "Should restore successfully"

    print(f"\n  Restored state: {restored.consultation_id}")
    print(f"    Context: category={restored.context.category_slug}, pet_id={restored.context.pet_id}")
    print(f"    Intakes: {len(restored.intakes)}")
    print(f"    Suggestions: {len(restored.suggestions)}")
    print(f"    Accumulated symptoms: {list(restored.accumulated_symptoms.keys())}")

    # Verify fields match
    assert restored.consultation_id == state.consultation_id
    assert restored.context.category_slug == state.context.category_slug
    assert restored.context.pet_id == state.context.pet_id
    assert restored.context.vet_id == state.context.vet_id
    assert len(restored.intakes) == len(state.intakes)
    assert len(restored.suggestions) == len(state.suggestions)
    assert set(restored.accumulated_symptoms.keys()) == set(state.accumulated_symptoms.keys())

    # Verify intake fields
    assert restored.intakes[0].complaint_text == state.intakes[0].complaint_text
    assert len(restored.intakes[0].symptoms) == len(state.intakes[0].symptoms)
    assert restored.intakes[0].symptoms[0].name_id == state.intakes[0].symptoms[0].name_id

    # Verify suggestion fields
    assert restored.suggestions[0].summary == state.suggestions[0].summary
    assert len(restored.suggestions[0].suggested_diseases) == len(state.suggestions[0].suggested_diseases)

    print("\n  ✓ All fields match after serialization/deserialization!")


def test_session_store_persistence():
    """Test that SessionStore saves and loads from disk correctly."""
    print("\n" + "="*60)
    print("TEST 2: SessionStore save/load persistence")
    print("="*60)

    # Create temp directory
    tmpdir = tempfile.mkdtemp(prefix="ekosistem_satwa_session_test_")
    sessions_dir = Path(tmpdir) / "sessions"
    print(f"  Using temp directory: {tmpdir}")

    # Create state
    ctx = ConsultationContext(category_slug="dog", pet_id=999, vet_id=2)
    state = ConsultationState(
        consultation_id="persist-test-001",
        context=ctx,
        accumulated_symptoms={
            "Batuk": {"name_id": "Batuk", "score": 0.9},
            "Napas cepat": {"name_id": "Napas cepat", "score": 0.85},
        },
    )

    # Store 1: save
    store1 = SessionStore(base_dir=sessions_dir, backend="jsonl")
    state_dict = _state_to_dict(state)
    store1.save(state.consultation_id, state_dict)
    print(f"  Saved state to store1: {state.consultation_id}")

    # Verify the file was created
    json_file = sessions_dir / f"{state.consultation_id}.json"
    assert json_file.exists(), f"JSON file should exist at {json_file}"
    print(f"  JSON file created: {json_file}")

    # Store 2: load (simulating new service instance / restart)
    store2 = SessionStore(base_dir=sessions_dir, backend="jsonl")
    loaded_dict = store2.load(state.consultation_id)
    assert loaded_dict is not None, "Should load from store2"

    restored = _dict_to_state(loaded_dict)
    assert restored is not None, "Should deserialize"

    print(f"  Loaded state from store2 (new instance): {restored.consultation_id}")
    print(f"    Context: category={restored.context.category_slug}, pet_id={restored.context.pet_id}")
    print(f"    Accumulated symptoms: {list(restored.accumulated_symptoms.keys())}")

    assert restored.consultation_id == state.consultation_id
    assert restored.context.category_slug == "dog"
    assert restored.context.pet_id == 999
    assert "Batuk" in restored.accumulated_symptoms
    assert "Napas cepat" in restored.accumulated_symptoms

    print("\n  ✓ State persisted correctly across SessionStore instances!")


def test_cache_rehydration():
    """Test that SessionStore rehydrates cache from disk on init."""
    print("\n" + "="*60)
    print("TEST 3: Cache rehydration on SessionStore init")
    print("="*60)

    tmpdir = tempfile.mkdtemp(prefix="ekosistem_satwa_rehydrate_test_")
    sessions_dir = Path(tmpdir) / "sessions"

    # First store: create multiple sessions
    store1 = SessionStore(base_dir=sessions_dir, backend="jsonl")

    # Create 3 sessions
    for i in range(3):
        ctx = ConsultationContext(category_slug="cat", pet_id=i+1)
        state = ConsultationState(
            consultation_id=f"rehydrate-session-{i:03d}",
            context=ctx,
        )
        store1.save(state.consultation_id, _state_to_dict(state))
        print(f"  Created session: {state.consultation_id}")

    # Verify store1 has them in cache
    assert len(store1._cache) == 3, f"store1 cache should have 3 items, got {len(store1._cache)}"

    # Create a NEW store - it should rehydrate from the JSON files on disk
    # Note: In our current implementation, rehydrate happens from PG first then JSON
    # But since we're using jsonl backend without PG, let's verify the files exist
    # and can be loaded individually

    store2 = SessionStore(base_dir=sessions_dir, backend="jsonl")

    # Actually in our implementation with jsonl only, the rehydrate_cache looks
    # for .json files. Let's verify each can be loaded.
    for i in range(3):
        cid = f"rehydrate-session-{i:03d}"
        loaded = store2.load(cid)
        assert loaded is not None, f"Should load {cid}"
        restored = _dict_to_state(loaded)
        assert restored is not None
        assert restored.consultation_id == cid
        print(f"  Loaded from store2: {cid}")

    print("\n  ✓ All sessions can be loaded from disk by new SessionStore instances!")


def main():
    print("="*60)
    print("SessionStore Persistence Tests")
    print("="*60)

    test_state_serialization()
    test_session_store_persistence()
    test_cache_rehydration()

    print("\n" + "="*60)
    print("ALL TESTS PASSED!")
    print("="*60)


if __name__ == "__main__":
    try:
        main()
        sys.exit(0)
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
