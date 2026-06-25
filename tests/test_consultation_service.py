"""Integration tests for ConsultationService."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ekosistem_satwa.ai.consultation import ConsultationService
from ekosistem_satwa.ai.learning_store import LearningStore
from ekosistem_satwa.ai.session_store import SessionStore
from ekosistem_satwa.ai.schemas import (
    ConsultationContext,
    ConsultationChannel,
    DoctorInput,
    IntakePayload,
    SuggestionFeedback,
)


def reset_singletons():
    """Reset all singletons to ensure test isolation."""
    # Reset AgentManager singleton
    import ekosistem_satwa.ai.agent_manager as am
    am._agent = None
    
    # Reset AgentStore singleton
    import ekosistem_satwa.ai.agent_store as as_
    as_._store_singleton = None
    
    # Reset IdentityRegistry singleton
    import ekosistem_satwa.integration.identity as ii
    ii._registry = None
    
    # Reset SessionStore singleton
    import ekosistem_satwa.ai.session_store as ss
    ss._store_singleton = None
    
    # Reset LearningStore singleton
    import ekosistem_satwa.ai.learning_store as ls
    ls._default_store = None
    
    # Clear lru_cache for deps
    import ekosistem_satwa.api.deps as deps
    deps.get_service.cache_clear()
    deps.get_agent.cache_clear()


@pytest.fixture(autouse=True)
def setup_and_teardown():
    """Auto-run fixture to reset singletons before and after each test."""
    reset_singletons()
    yield
    reset_singletons()


@pytest.fixture
def temp_learning_dir():
    """Create a temporary directory for learning store."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_sessions_dir():
    """Create a temporary directory for session store."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def consultation_context():
    """Create a sample consultation context with unique external ID."""
    import uuid
    return ConsultationContext(
        category_slug="cat",
        breed_slug="cat-persian",
        age_years=6,
        vet_id=1,
        owner_id=100,
        pet_id=200,
        external_consultation_id=f"ext-test-{uuid.uuid4().hex}",
    )


@pytest.fixture
def intake_payload():
    """Create a sample intake payload."""
    return IntakePayload(
        text="Kucing saya mengejan saat pipis, ada darah, lemas dan tidak mau makan",
        channel=ConsultationChannel.chat,
    )


class TestConsultationServiceRuleBased:
    """Test ConsultationService in rule-based mode (no LLM key)."""

    def test_start_consultation(self, temp_learning_dir, temp_sessions_dir, consultation_context, intake_payload):
        """Test starting a consultation."""
        store = LearningStore(base_dir=temp_learning_dir, backend="jsonl")
        session_store = SessionStore(base_dir=temp_sessions_dir, backend="jsonl")
        svc = ConsultationService(store=store, session_store=session_store)

        # Start consultation
        result = svc.start(consultation_context, intake_payload)

        # Verify result
        assert result.consultation_id is not None
        assert result.intake is not None
        assert result.suggestion is not None

        # Verify consultation start was recorded
        consult_records = store._read("consultation")
        assert len(consult_records) == 1
        assert consult_records[0]["consultation_id"] == result.consultation_id
        assert consult_records[0]["event"] == "start"

        # Verify intake was recorded
        intake_records = store._read("intake")
        assert len(intake_records) == 1
        assert intake_records[0]["consultation_id"] == result.consultation_id

        # Verify suggestion was recorded
        suggestion_records = store._read("suggestion")
        assert len(suggestion_records) == 1
        assert suggestion_records[0]["consultation_id"] == result.consultation_id

    def test_add_turn(self, temp_learning_dir, temp_sessions_dir, consultation_context, intake_payload):
        """Test adding a turn to an existing consultation."""
        store = LearningStore(base_dir=temp_learning_dir, backend="jsonl")
        session_store = SessionStore(base_dir=temp_sessions_dir, backend="jsonl")
        svc = ConsultationService(store=store, session_store=session_store)

        # Start consultation
        start_result = svc.start(consultation_context, intake_payload)

        # Add a new turn
        second_payload = IntakePayload(
            text="Sekarang kucingnya juga muntah dan perutnya kembung",
            channel=ConsultationChannel.chat,
        )
        add_result = svc.add_turn(start_result.consultation_id, second_payload)

        # Verify result
        assert add_result.consultation_id == start_result.consultation_id

        # Verify two intakes were recorded
        intake_records = store._read("intake")
        assert len(intake_records) == 2

        # Verify two suggestions were recorded
        suggestion_records = store._read("suggestion")
        assert len(suggestion_records) == 2

    def test_add_turn_nonexistent_consultation(self, temp_learning_dir):
        """Test adding a turn to a nonexistent consultation raises error."""
        store = LearningStore(base_dir=temp_learning_dir, backend="jsonl")
        svc = ConsultationService(store=store)

        with pytest.raises(KeyError):
            svc.add_turn(
                "nonexistent-id",
                IntakePayload(text="test", channel=ConsultationChannel.chat),
            )

    def test_record_doctor_input(self, temp_learning_dir, temp_sessions_dir, consultation_context, intake_payload):
        """Test recording doctor input."""
        store = LearningStore(base_dir=temp_learning_dir, backend="jsonl")
        session_store = SessionStore(base_dir=temp_sessions_dir, backend="jsonl")
        svc = ConsultationService(store=store, session_store=session_store)

        # Start consultation
        start_result = svc.start(consultation_context, intake_payload)

        # Record doctor input
        doctor_input = DoctorInput(
            consultation_id=start_result.consultation_id,
            confirmed_disease_slug="feline-lower-urinary-tract-disease",
            confirmed_symptoms=["Mengejan saat buang air kecil", "Darah dalam urin"],
            clinical_notes="Pasien menunjukkan gejala FLUTD. Diberikan antibiotik dan analgesik.",
        )
        result = svc.record_doctor_input(doctor_input)

        # Verify result
        assert result is not None

        # Verify doctor input was recorded
        doctor_records = store._read("doctor_input")
        assert len(doctor_records) == 1
        assert doctor_records[0]["consultation_id"] == start_result.consultation_id
        assert doctor_records[0]["confirmed_disease_slug"] == "feline-lower-urinary-tract-disease"

    def test_record_feedback(self, temp_learning_dir, temp_sessions_dir, consultation_context, intake_payload):
        """Test recording suggestion feedback."""
        store = LearningStore(base_dir=temp_learning_dir, backend="jsonl")
        session_store = SessionStore(base_dir=temp_sessions_dir, backend="jsonl")
        svc = ConsultationService(store=store, session_store=session_store)

        # Start consultation
        start_result = svc.start(consultation_context, intake_payload)

        # Record feedback
        feedback = SuggestionFeedback(
            consultation_id=start_result.consultation_id,
            verdict="correct",
            comment="Saran AI sangat membantu dan akurat",
            reviewer_id=1,
        )
        result = svc.record_feedback(feedback)

        # Verify result
        assert result is not None

        # Verify feedback was recorded
        feedback_records = store._read("feedback")
        assert len(feedback_records) == 1
        assert feedback_records[0]["consultation_id"] == start_result.consultation_id
        assert feedback_records[0]["verdict"] == "correct"


class TestConsultationServiceLLMMode:
    """Test ConsultationService with LLM mode (mocked)."""

    def test_llm_augmentation(self, temp_learning_dir, temp_sessions_dir, consultation_context, intake_payload):
        """Test that LLM augmentation is called when appropriate."""
        store = LearningStore(base_dir=temp_learning_dir, backend="jsonl")
        session_store = SessionStore(base_dir=temp_sessions_dir, backend="jsonl")
        
        # Mock LLMClient
        mock_llm = MagicMock()
        mock_llm.available = True
        mock_llm.chat_json.return_value = {
            "summary": "Ini adalah ringkasan dari LLM",
            "follow_up_questions": [
                "Apakah kucing Anda sudah divaksin lengkap?",
                "Sudah berapa lama gejala ini berlangsung?",
            ],
            "prioritized_disease_slugs": ["feline-lower-urinary-tract-disease"],
        }
        mock_llm.provider = "openai"
        mock_llm.model = "gpt-4o-mini"
        mock_llm.telemetry = MagicMock()
        mock_llm.telemetry.can_spend.return_value = (True, None)
        
        # Mock get_provider_registry to return a chain with our mock provider
        mock_provider = MagicMock()
        mock_provider.kind = "openai"
        mock_provider.available.return_value = True
        mock_provider.base_url = None
        mock_provider.api_key = "test-key"
        mock_provider.default_model = "gpt-4o-mini"
        mock_provider.id = "test-openai"
        
        with patch("ekosistem_satwa.ai.llm.get_provider_registry") as mock_registry:
            mock_registry_instance = MagicMock()
            mock_registry_instance.get_chain.return_value = [mock_provider]
            mock_registry_instance.get_primary.return_value = mock_provider
            mock_registry.return_value = mock_registry_instance

            # Mock LLMClient.for_provider to return our mock_llm
            with patch("ekosistem_satwa.ai.llm.LLMClient.for_provider", return_value=mock_llm):
                # Mock AISettings to use "always" augmentation mode
                with patch("ekosistem_satwa.ai.suggestion_engine.AISettings") as mock_settings:
                    mock_settings_instance = MagicMock()
                    mock_settings_instance.augmentation_mode = "always"
                    mock_settings_instance.max_tokens = 800
                    mock_settings_instance.skip_llm_confidence = 0.82
                    mock_settings.return_value = mock_settings_instance

                    # Create service with mocked LLM
                    svc = ConsultationService(store=store, llm=mock_llm, session_store=session_store)

                    # Start consultation
                    result = svc.start(consultation_context, intake_payload)

                    # Verify LLM augmentation was applied
                    assert result.suggestion.generated_by == "llm_augmented"
                    assert "LLM" in result.suggestion.summary
                    assert len(result.suggestion.follow_up_questions) >= 2
