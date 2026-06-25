#!/usr/bin/env python3
"""Generate real request/response examples for docs/INTEGRATION.md."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from ekosistem_satwa.api.main import app
from ekosistem_satwa.ai.learning_store import LearningStore
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


def generate_examples():
    reset_singletons()
    
    # Create temp directories
    with tempfile.TemporaryDirectory() as temp_learning_dir, tempfile.TemporaryDirectory() as temp_sessions_dir:
        temp_learning_path = Path(temp_learning_dir)
        temp_sessions_path = Path(temp_sessions_dir)
        
        # Create mock stores
        mock_learning_store = LearningStore(base_dir=temp_learning_path, backend="jsonl")
        
        # Mock LLM to be unavailable
        mock_llm = MagicMock()
        mock_llm.available = False
        mock_llm.provider = "local"
        mock_llm.model = "rule-based"
        
        examples = []
        
        # Patch all relevant singletons
        with patch("ekosistem_satwa.api.deps.LLMClient", return_value=mock_llm):
            with patch("ekosistem_satwa.ai.suggestion_engine.LLMClient", return_value=mock_llm):
                with patch("ekosistem_satwa.ai.consultation.LLMClient", return_value=mock_llm):
                    with patch("ekosistem_satwa.ai.suggestion_engine.AISettings") as mock_settings:
                        mock_settings_instance = MagicMock()
                        mock_settings_instance.augmentation_mode = "never"
                        mock_settings_instance.max_tokens = 800
                        mock_settings_instance.skip_llm_confidence = 0.82
                        mock_settings.return_value = mock_settings_instance
                        
                        client = TestClient(app)
                        
                        # 1. GET /health
                        print("Generating: GET /health")
                        response = client.get("/health")
                        examples.append({
                            "title": "Health Check",
                            "method": "GET",
                            "endpoint": "/health",
                            "request": "No request body",
                            "response": response.json()
                        })
                        
                        # 2. GET /api/integration/manifest
                        print("Generating: GET /api/integration/manifest")
                        response = client.get("/api/integration/manifest")
                        examples.append({
                            "title": "Integration Manifest",
                            "method": "GET",
                            "endpoint": "/api/integration/manifest",
                            "request": "No request body",
                            "response": response.json()
                        })
                        
                        # 3. GET /api/integration/id-schema
                        print("Generating: GET /api/integration/id-schema")
                        response = client.get("/api/integration/id-schema")
                        examples.append({
                            "title": "ID Schema",
                            "method": "GET",
                            "endpoint": "/api/integration/id-schema",
                            "request": "No request body",
                            "response": response.json()
                        })
                        
                        # 4. GET /categories
                        print("Generating: GET /categories")
                        response = client.get("/categories")
                        examples.append({
                            "title": "List Categories",
                            "method": "GET",
                            "endpoint": "/categories",
                            "request": "No request body",
                            "response": response.json()[:3]  # Limit to first 3 for brevity
                        })
                        
                        # 5. POST /consultations
                        print("Generating: POST /consultations")
                        request_data = {
                            "context": {
                                "vet_id": 1,
                                "owner_id": 100,
                                "pet_id": 200,
                                "category_slug": "cat",
                                "breed_slug": "cat-persian",
                                "age_years": 3,
                                "external_consultation_id": "ext-20250619-001"
                            },
                            "intake": {
                                "channel": "chat",
                                "text": "Kucing saya muntah hebat dan tidak mau makan sejak kemarin",
                                "is_first_contact": True
                            }
                        }
                        response = client.post("/consultations", json=request_data)
                        examples.append({
                            "title": "Start Consultation",
                            "method": "POST",
                            "endpoint": "/consultations",
                            "request": request_data,
                            "response": response.json()
                        })
                        consultation_id = response.json()["consultation_id"]
                        
                        # 6. POST /consultations/{id}/turns
                        print("Generating: POST /consultations/{id}/turns")
                        request_data = {
                            "intake": {
                                "channel": "chat",
                                "text": "Sekarang juga diare berdarah dan lemas sekali"
                            }
                        }
                        response = client.post(f"/consultations/{consultation_id}/turns", json=request_data)
                        examples.append({
                            "title": "Add Turn (Cumulative Symptoms)",
                            "method": "POST",
                            "endpoint": f"/consultations/{consultation_id}/turns",
                            "request": request_data,
                            "response": response.json()
                        })
                        
                        # 7. GET /consultations/{id}
                        print("Generating: GET /consultations/{id}")
                        response = client.get(f"/consultations/{consultation_id}")
                        examples.append({
                            "title": "Get Consultation",
                            "method": "GET",
                            "endpoint": f"/consultations/{consultation_id}",
                            "request": "No request body",
                            "response": response.json()
                        })
                        
                        # 8. POST /consultations/{id}/doctor-input
                        print("Generating: POST /consultations/{id}/doctor-input")
                        request_data = {
                            "confirmed_disease_slug": "cat-fpv-panleukopenia",
                            "confirmed_symptoms": ["Muntah hebat", "Diare berdarah", "Lemas"],
                            "clinical_notes": "Panleukopenia confirmed via rapid test. Diberikan terapi suportif: cairan infus, anti muntah, antibiotik."
                        }
                        response = client.post(f"/consultations/{consultation_id}/doctor-input", json=request_data)
                        examples.append({
                            "title": "Record Doctor Input (Gold Label)",
                            "method": "POST",
                            "endpoint": f"/consultations/{consultation_id}/doctor-input",
                            "request": request_data,
                            "response": response.json()
                        })
                        
                        # 9. POST /consultations/{id}/feedback
                        print("Generating: POST /consultations/{id}/feedback")
                        request_data = {
                            "verdict": "correct",
                            "comment": "Saran AI sangat akurat. Panleukopenia memang menjadi differential diagnosis utama.",
                            "reviewer_id": 1
                        }
                        response = client.post(f"/consultations/{consultation_id}/feedback", json=request_data)
                        examples.append({
                            "title": "Record Feedback",
                            "method": "POST",
                            "endpoint": f"/consultations/{consultation_id}/feedback",
                            "request": request_data,
                            "response": response.json()
                        })
                        
                        # 10. GET /api/integration/entities/{id}
                        print("Generating: GET /api/integration/entities/{id}")
                        response = client.get(f"/api/integration/entities/{consultation_id}")
                        examples.append({
                            "title": "Get Entities",
                            "method": "GET",
                            "endpoint": f"/api/integration/entities/{consultation_id}",
                            "request": "No request body",
                            "response": response.json()
                        })
                        
                        # 11. GET /api/integration/consultations/by-external/{id}
                        print("Generating: GET /api/integration/consultations/by-external/{id}")
                        response = client.get("/api/integration/consultations/by-external/ext-20250619-001")
                        examples.append({
                            "title": "Lookup by External ID",
                            "method": "GET",
                            "endpoint": "/api/integration/consultations/by-external/ext-20250619-001",
                            "request": "No request body",
                            "response": response.json()
                        })
                        
                        # 12. POST /api/consult (single-shot)
                        print("Generating: POST /api/consult")
                        request_data = {
                            "category_slug": "dog",
                            "symptoms": ["Muntah", "Diare", "Lemas"],
                            "top_k": 3
                        }
                        response = client.post("/api/consult", json=request_data)
                        examples.append({
                            "title": "Single-shot Consult",
                            "method": "POST",
                            "endpoint": "/api/consult",
                            "request": request_data,
                            "response": response.json()
                        })
                        
                        # 13. POST /ml/predict
                        print("Generating: POST /ml/predict")
                        request_data = {
                            "category_slug": "cat",
                            "symptoms": ["Muntah hebat", "Diare berdarah"],
                            "top_k": 3
                        }
                        response = client.post("/ml/predict", json=request_data)
                        examples.append({
                            "title": "ML Predict",
                            "method": "POST",
                            "endpoint": "/ml/predict",
                            "request": request_data,
                            "response": response.json()
                        })
                        
                        # 14. GET /openapi.json
                        print("Generating: GET /openapi.json")
                        response = client.get("/openapi.json")
                        examples.append({
                            "title": "OpenAPI Schema",
                            "method": "GET",
                            "endpoint": "/openapi.json",
                            "request": "No request body",
                            "response": {"info": response.json()["info"], "paths_count": len(response.json()["paths"])}
                        })
    
    return examples


def format_example(example: dict) -> str:
    lines = []
    lines.append(f"### {example['title']}\n")
    lines.append(f"**{example['method']} {example['endpoint']}**\n")
    
    if example['request'] != "No request body":
        import json
        lines.append("**Request:**\n")
        lines.append("```json\n")
        lines.append(json.dumps(example['request'], indent=2, ensure_ascii=False))
        lines.append("\n```\n")
    
    lines.append("**Response:**\n")
    lines.append("```json\n")
    import json
    lines.append(json.dumps(example['response'], indent=2, ensure_ascii=False))
    lines.append("\n```\n")
    lines.append("---\n")
    return "\n".join(lines)


if __name__ == "__main__":
    import json
    
    print("Generating integration examples...")
    examples = generate_examples()
    
    # Format examples for docs
    output_lines = [
        "# API Request/Response Examples\n",
        "Contoh request dan response real dari endpoint integrasi Ekosistem Satwa.\n",
        "---\n"
    ]
    
    for example in examples:
        output_lines.append(format_example(example))
    
    # Write to file
    output_path = Path(__file__).parent.parent / "docs" / "API_EXAMPLES.md"
    output_path.write_text("\n".join(output_lines), encoding="utf-8")
    print(f"Examples written to: {output_path}")
    
    # Also print summary
    print("\nGenerated examples:")
    for i, example in enumerate(examples, 1):
        print(f"{i}. {example['method']} {example['endpoint']}")