"""Integration tests for API endpoints using FastAPI TestClient."""
from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from sobatpaws.api.main import app
from sobatpaws.ai.learning_store import LearningStore
from sobatpaws.ai.schemas import (
    ConsultationContext,
    ConsultationChannel,
    DoctorInput,
    IntakePayload,
    SuggestionFeedback,
)


def reset_singletons():
    """Reset all singletons to ensure test isolation."""
    # Reset AgentManager singleton
    import sobatpaws.ai.agent_manager as am
    am._agent = None
    
    # Reset AgentStore singleton
    import sobatpaws.ai.agent_store as as_
    as_._store_singleton = None
    
    # Reset IdentityRegistry singleton
    import sobatpaws.integration.identity as ii
    ii._registry = None
    
    # Reset SessionStore singleton
    import sobatpaws.ai.session_store as ss
    ss._store_singleton = None
    
    # Reset LearningStore singleton
    import sobatpaws.ai.learning_store as ls
    ls._default_store = None
    
    # Clear lru_cache for deps
    import sobatpaws.api.deps as deps
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
def client(temp_learning_dir):
    """Create a TestClient with mocked dependencies using temp directory."""
    
    # Create mock store with temp directory
    mock_learning_store = LearningStore(base_dir=temp_learning_dir, backend="jsonl")
    
    # Mock LLM to be unavailable so we use rule-based mode only
    mock_llm = MagicMock()
    mock_llm.available = False
    mock_llm.provider = "local"
    mock_llm.model = "rule-based"
    
    # Patch all relevant singletons and dependencies
    with patch("sobatpaws.api.deps.LLMClient", return_value=mock_llm):
        with patch("sobatpaws.ai.suggestion_engine.LLMClient", return_value=mock_llm):
            with patch("sobatpaws.ai.consultation.LLMClient", return_value=mock_llm):
                # Mock AI settings to use never augmentation mode
                with patch("sobatpaws.ai.suggestion_engine.AISettings") as mock_settings:
                    mock_settings_instance = MagicMock()
                    mock_settings_instance.augmentation_mode = "never"
                    mock_settings_instance.max_tokens = 800
                    mock_settings_instance.skip_llm_confidence = 0.82
                    mock_settings.return_value = mock_settings_instance
                    
                    yield TestClient(app)


class TestPublicEndpoints:
    """Test public endpoints that don't require authentication."""

    def test_health_endpoint(self, client):
        """Test GET /health."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"

    def test_integration_manifest(self, client):
        """Test GET /api/integration/manifest."""
        response = client.get("/api/integration/manifest")
        assert response.status_code == 200
        data = response.json()
        assert "platform" in data
        assert "api_version" in data
        assert "recommended_flow" in data
        assert "endpoints" in data

    def test_integration_id_schema(self, client):
        """Test GET /api/integration/id-schema."""
        response = client.get("/api/integration/id-schema")
        assert response.status_code == 200
        data = response.json()
        assert "description" in data
        assert "fields" in data
        assert "vet_id" in data["fields"]
        assert "owner_id" in data["fields"]
        assert "pet_id" in data["fields"]

    def test_categories_endpoint(self, client):
        """Test GET /categories."""
        response = client.get("/categories")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should have at least dog and cat categories
        slugs = [c["slug"] for c in data]
        assert "dog" in slugs or "cat" in slugs

    def test_ml_predict_endpoint(self, client):
        """Test POST /ml/predict (without LLM)."""
        response = client.post(
            "/ml/predict",
            json={
                "category_slug": "dog",
                "symptoms": ["Muntah hebat", "Diare berdarah"],
                "top_k": 3,
            },
        )
        # Note: This may return 404 if no ML model exists yet, which is acceptable in dev
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "category_slug" in data
            assert "predictions" in data


class TestVetEndpoints:
    """Test endpoints that require vet authentication (disabled in dev mode)."""

    def test_start_consultation(self, client):
        """Test POST /consultations."""
        response = client.post(
            "/consultations",
            json={
                "context": {
                    "vet_id": 1,
                    "owner_id": 100,
                    "pet_id": 200,
                    "category_slug": "cat",
                    "breed_slug": "cat-persian",
                    "age_years": 3,
                },
                "intake": {
                    "channel": "chat",
                    "text": "Kucing saya muntah dan tidak mau makan",
                    "is_first_contact": True,
                },
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "consultation_id" in data
        assert "suggestion" in data
        assert "entities" in data

    def test_add_turn(self, client):
        """Test POST /consultations/{id}/turns (cumulative symptoms)."""
        # First start a consultation
        start_response = client.post(
            "/consultations",
            json={
                "context": {
                    "vet_id": 1,
                    "owner_id": 101,
                    "pet_id": 201,
                    "category_slug": "dog",
                },
                "intake": {
                    "channel": "chat",
                    "text": "Anjing saya muntah",
                },
            },
        )
        assert start_response.status_code == 200
        consultation_id = start_response.json()["consultation_id"]

        # Now add a turn
        turn_response = client.post(
            f"/consultations/{consultation_id}/turns",
            json={
                "intake": {
                    "channel": "chat",
                    "text": "Sekarang juga diare berdarah",
                },
            },
        )
        assert turn_response.status_code == 200
        data = turn_response.json()
        assert data["consultation_id"] == consultation_id

    def test_get_consultation(self, client):
        """Test GET /consultations/{id}."""
        # First start a consultation
        start_response = client.post(
            "/consultations",
            json={
                "context": {
                    "vet_id": 1,
                    "owner_id": 102,
                    "pet_id": 202,
                    "category_slug": "cat",
                },
                "intake": {
                    "channel": "chat",
                    "text": "Kucing lemas",
                },
            },
        )
        assert start_response.status_code == 200
        consultation_id = start_response.json()["consultation_id"]

        # Now get the consultation
        get_response = client.get(f"/consultations/{consultation_id}")
        assert get_response.status_code == 200

    def test_doctor_input(self, client):
        """Test POST /consultations/{id}/doctor-input (gold label)."""
        # First start a consultation
        start_response = client.post(
            "/consultations",
            json={
                "context": {
                    "vet_id": 1,
                    "owner_id": 103,
                    "pet_id": 203,
                    "category_slug": "dog",
                },
                "intake": {
                    "channel": "chat",
                    "text": "Anjing muntah dan diare",
                },
            },
        )
        assert start_response.status_code == 200
        consultation_id = start_response.json()["consultation_id"]

        # Now record doctor input
        doctor_response = client.post(
            f"/consultations/{consultation_id}/doctor-input",
            json={
                "confirmed_disease_slug": "dog-parvovirus",
                "confirmed_symptoms": ["Muntah hebat", "Diare berdarah"],
                "clinical_notes": "Parvo confirmed",
            },
        )
        assert doctor_response.status_code == 200
        data = doctor_response.json()
        assert data["status"] == "stored"

    def test_feedback(self, client):
        """Test POST /consultations/{id}/feedback."""
        # First start a consultation
        start_response = client.post(
            "/consultations",
            json={
                "context": {
                    "vet_id": 1,
                    "owner_id": 104,
                    "pet_id": 204,
                    "category_slug": "cat",
                },
                "intake": {
                    "channel": "chat",
                    "text": "Kucing tidak makan",
                },
            },
        )
        assert start_response.status_code == 200
        consultation_id = start_response.json()["consultation_id"]

        # Now record feedback
        feedback_response = client.post(
            f"/consultations/{consultation_id}/feedback",
            json={
                "verdict": "correct",
                "comment": "Saran akurat",
            },
        )
        assert feedback_response.status_code == 200
        data = feedback_response.json()
        assert data["status"] == "stored"

    def test_single_shot_consult(self, client):
        """Test POST /api/consult (single-shot)."""
        response = client.post(
            "/api/consult",
            json={
                "category_slug": "dog",
                "symptoms": ["Muntah", "Diare"],
                "top_k": 3,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "suggested_diseases" in data
        assert "summary" in data

    def test_integration_entities(self, client):
        """Test GET /api/integration/entities/{id}."""
        # First start a consultation
        start_response = client.post(
            "/consultations",
            json={
                "context": {
                    "vet_id": 1,
                    "owner_id": 105,
                    "pet_id": 205,
                    "category_slug": "cat",
                },
                "intake": {
                    "channel": "chat",
                    "text": "Kucing sakit",
                },
            },
        )
        assert start_response.status_code == 200
        consultation_id = start_response.json()["consultation_id"]

        # Now get entities
        entities_response = client.get(f"/api/integration/entities/{consultation_id}")
        assert entities_response.status_code == 200
        data = entities_response.json()
        assert "consultation_id" in data
        assert "entities" in data

    def test_integration_by_external(self, client):
        """Test GET /api/integration/consultations/by-external/{id}."""
        # First start a consultation with unique external ID
        import uuid
        external_id = f"ext-test-{uuid.uuid4().hex}"
        start_response = client.post(
            "/consultations",
            json={
                "context": {
                    "vet_id": 1,
                    "owner_id": 106,
                    "pet_id": 206,
                    "category_slug": "dog",
                    "external_consultation_id": external_id,
                },
                "intake": {
                    "channel": "chat",
                    "text": "Anjing lemas",
                },
            },
        )
        assert start_response.status_code == 200

        # Now lookup by external ID
        lookup_response = client.get(f"/api/integration/consultations/by-external/{external_id}")
        assert lookup_response.status_code == 200


class TestOpenAPIDocumentation:
    """Test that OpenAPI docs are properly generated."""

    def test_openapi_json(self, client):
        """Test GET /openapi.json."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "paths" in data
        assert "info" in data
        assert data["info"]["title"] == "Sobatpaws Veterinary ML & AI API"
